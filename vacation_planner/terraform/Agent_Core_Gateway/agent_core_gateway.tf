data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  discovery_url = "${var.issuer_url}/.well-known/openid-configuration"
}

# Role the gateway assumes: invokes the travel tool Lambda (outbound) and is referenced by the gateway (IAM outbound auth)
data "aws_iam_policy_document" "gateway_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["bedrock-agentcore.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "ArnLike"
      variable = "aws:SourceArn"
      values   = ["arn:aws:bedrock-agentcore:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:*"]
    }
  }
}

resource "aws_iam_role" "gateway" {
  name               = "${var.gateway_name}-gateway-role"
  assume_role_policy = data.aws_iam_policy_document.gateway_assume_role.json
  tags               = var.tags
}

data "aws_iam_policy_document" "gateway_invoke_tool" {
  statement {
    sid       = "InvokeTravelAgentToolLambda"
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = [var.travel_tool_lambda_arn]
  }
}

resource "aws_iam_role_policy" "gateway_invoke_tool" {
  name   = "${var.gateway_name}-invoke-travel-tool-policy"
  role   = aws_iam_role.gateway.id
  policy = data.aws_iam_policy_document.gateway_invoke_tool.json
}

# Inbound: JWT validated against the existing Cognito identity provider; semantic search enabled on the MCP protocol
resource "aws_bedrockagentcore_gateway" "this" {
  name            = var.gateway_name
  description     = var.gateway_description
  role_arn        = aws_iam_role.gateway.arn
  authorizer_type = "CUSTOM_JWT"
  protocol_type   = "MCP"

  authorizer_configuration {
    custom_jwt_authorizer {
      discovery_url   = local.discovery_url
      allowed_clients = var.allowed_clients
    }
  }

  protocol_configuration {
    mcp {
      search_type = "SEMANTIC"
    }
  }

  tags = var.tags

  depends_on = [aws_iam_role_policy.gateway_invoke_tool]
}

# Target: Lambda ARN with an in-line tool schema; outbound auth uses the gateway's IAM role
resource "aws_bedrockagentcore_gateway_target" "travel_agent_tool" {
  name               = var.target_name
  description        = var.target_description
  gateway_identifier = aws_bedrockagentcore_gateway.this.gateway_id

  credential_provider_configuration {
    gateway_iam_role {}
  }

  target_configuration {
    mcp {
      lambda {
        lambda_arn = var.travel_tool_lambda_arn

        tool_schema {
          inline_payload {
            name        = "get_travel_packages"
            description = "Get city travel package information including travel plan, cost, duration"

            input_schema {
              type = "object"

              property {
                name        = "city"
                type        = "string"
                description = "Name of the city to get travel information for"
                required    = true
              }
            }
          }
        }
      }
    }
  }
}
