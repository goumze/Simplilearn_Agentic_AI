resource "aws_api_gateway_rest_api" "vacation_planner" {
  name        = var.api_name
  description = "REST API that invokes the ${var.lambda_function_name} Lambda function"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = var.tags
}

resource "aws_api_gateway_resource" "vacation_planner" {
  rest_api_id = aws_api_gateway_rest_api.vacation_planner.id
  parent_id   = aws_api_gateway_rest_api.vacation_planner.root_resource_id
  path_part   = var.resource_path
}

resource "aws_api_gateway_method" "post" {
  rest_api_id   = aws_api_gateway_rest_api.vacation_planner.id
  resource_id   = aws_api_gateway_resource.vacation_planner.id
  http_method   = "POST"
  authorization = "NONE"
}

# Lambda proxy integration: the function receives the full request event and returns
# the statusCode/headers/body envelope that API Gateway passes through to the caller.
resource "aws_api_gateway_integration" "post" {
  rest_api_id             = aws_api_gateway_rest_api.vacation_planner.id
  resource_id             = aws_api_gateway_resource.vacation_planner.id
  http_method             = aws_api_gateway_method.post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.lambda_invoke_arn
}

# CORS preflight for browser callers
resource "aws_api_gateway_method" "options" {
  rest_api_id   = aws_api_gateway_rest_api.vacation_planner.id
  resource_id   = aws_api_gateway_resource.vacation_planner.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options" {
  rest_api_id = aws_api_gateway_rest_api.vacation_planner.id
  resource_id = aws_api_gateway_resource.vacation_planner.id
  http_method = aws_api_gateway_method.options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({ statusCode = 200 })
  }
}

resource "aws_api_gateway_method_response" "options" {
  rest_api_id = aws_api_gateway_rest_api.vacation_planner.id
  resource_id = aws_api_gateway_resource.vacation_planner.id
  http_method = aws_api_gateway_method.options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "options" {
  rest_api_id = aws_api_gateway_rest_api.vacation_planner.id
  resource_id = aws_api_gateway_resource.vacation_planner.id
  http_method = aws_api_gateway_method.options.http_method
  status_code = aws_api_gateway_method_response.options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  depends_on = [aws_api_gateway_integration.options]
}

resource "aws_api_gateway_deployment" "vacation_planner" {
  rest_api_id = aws_api_gateway_rest_api.vacation_planner.id

  # Redeploy whenever any routing piece changes
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.vacation_planner.id,
      aws_api_gateway_method.post.id,
      aws_api_gateway_integration.post.id,
      aws_api_gateway_method.options.id,
      aws_api_gateway_integration.options.id,
      aws_api_gateway_method_response.options.id,
      aws_api_gateway_integration_response.options.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "vacation_planner" {
  rest_api_id   = aws_api_gateway_rest_api.vacation_planner.id
  deployment_id = aws_api_gateway_deployment.vacation_planner.id
  stage_name    = var.stage_name
  tags          = var.tags
}

# Resource-based policy that lets API Gateway invoke the function. No IAM execution
# role is required for a Lambda proxy integration.
resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.vacation_planner.execution_arn}/*/POST/${var.resource_path}"
}
