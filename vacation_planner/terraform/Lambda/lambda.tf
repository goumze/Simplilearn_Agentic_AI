data "aws_region" "current" {}

data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.module}/../../src/vacation_planner/lambda.py"
  output_path = "${path.module}/build/lambda.zip"
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_execution" {
  name               = "${var.function_name}-lambda-execution-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = var.tags
}

# Lets the function invoke the AgentCore agent runtime
resource "aws_iam_role_policy_attachment" "bedrock_agentcore_full_access" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/BedrockAgentCoreFullAccess"
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

data "aws_iam_policy_document" "lambda_logging" {
  statement {
    sid    = "WriteFunctionLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = [
      "${aws_cloudwatch_log_group.lambda.arn}:*",
    ]
  }
}

resource "aws_iam_role_policy" "lambda_logging" {
  name   = "${var.function_name}-lambda-logging-policy"
  role   = aws_iam_role.lambda_execution.id
  policy = data.aws_iam_policy_document.lambda_logging.json
}

resource "aws_lambda_function" "vacation_planner" {
  function_name    = var.function_name
  role             = aws_iam_role.lambda_execution.arn
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  handler          = "lambda.lambda_handler"
  runtime          = var.runtime
  timeout          = var.timeout
  memory_size      = var.memory_size

  environment {
    variables = {
      AGENT_RUNTIME_ARN = var.agent_runtime_arn
      AGENT_REGION      = data.aws_region.current.region
    }
  }

  tags = var.tags

  # The role must be able to write logs before the function's first invocation
  depends_on = [
    aws_iam_role_policy_attachment.bedrock_agentcore_full_access,
    aws_iam_role_policy.lambda_logging,
    aws_cloudwatch_log_group.lambda,
  ]
}
