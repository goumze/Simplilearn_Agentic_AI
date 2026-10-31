# Short-term memory: raw events expire after 7 days
resource "aws_bedrockagentcore_memory" "this" {
  name                  = var.memory_name
  description           = var.memory_description
  event_expiry_duration = var.event_expiry_days
  tags                  = var.tags
}

# Built-in summarization strategy; summaries are stored per actor and session
resource "aws_bedrockagentcore_memory_strategy" "summarization" {
  name                = var.summarization_strategy_name
  memory_id           = aws_bedrockagentcore_memory.this.id
  type                = "SUMMARIZATION"
  description         = "Summarizes vacation planning conversations per session"
  namespace_templates = ["/summaries/{actorId}/{sessionId}"]
}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# Streams AgentCore application logs for the memory resource
resource "aws_cloudwatch_log_delivery_source" "memory_application_logs" {
  name         = "${var.memory_name}-application-logs"
  log_type     = "APPLICATION_LOGS"
  resource_arn = aws_bedrockagentcore_memory.this.arn
  tags         = var.tags
}

resource "aws_cloudwatch_log_group" "memory_application_logs" {
  name              = "/aws/vendedlogs/bedrock-agentcore/memory/APPLICATION_LOGS/${var.memory_name}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

# Allows the CloudWatch Logs delivery service to write to the log group
data "aws_iam_policy_document" "memory_log_delivery" {
  statement {
    sid     = "AWSLogDeliveryWrite"
    effect  = "Allow"
    actions = ["logs:CreateLogStream", "logs:PutLogEvents"]

    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }

    resources = ["${aws_cloudwatch_log_group.memory_application_logs.arn}:*"]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_cloudwatch_log_resource_policy" "memory_log_delivery" {
  policy_name     = "${var.memory_name}-log-delivery"
  policy_document = data.aws_iam_policy_document.memory_log_delivery.json
}

resource "aws_cloudwatch_log_delivery_destination" "memory_application_logs" {
  name = "${var.memory_name}-application-logs"

  delivery_destination_configuration {
    destination_resource_arn = aws_cloudwatch_log_group.memory_application_logs.arn
  }

  tags = var.tags

  depends_on = [aws_cloudwatch_log_resource_policy.memory_log_delivery]
}

# Connects the memory's application log source to the CloudWatch Logs destination
resource "aws_cloudwatch_log_delivery" "memory_application_logs" {
  delivery_source_name     = aws_cloudwatch_log_delivery_source.memory_application_logs.name
  delivery_destination_arn = aws_cloudwatch_log_delivery_destination.memory_application_logs.arn
  tags                     = var.tags
}
