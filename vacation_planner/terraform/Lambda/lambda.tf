data "aws_region" "current" {}

data "archive_file" "lambda" {
  type        = "zip"
  source_file = "${path.root}/../src/${var.source_dir}/lambda.py"
  output_path = "${path.module}/build/${var.function_name}.zip"
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

# Managed policies attached to the execution role; supplied per function
resource "aws_iam_role_policy_attachment" "managed" {
  for_each   = toset(var.managed_policy_arns)
  role       = aws_iam_role.lambda_execution.name
  policy_arn = each.value
}

# Optional function-specific inline policy (e.g. DynamoDB access)
resource "aws_iam_role_policy" "custom" {
  count  = var.inline_policy_json == null ? 0 : 1
  name   = "${var.function_name}-custom-policy"
  role   = aws_iam_role.lambda_execution.id
  policy = var.inline_policy_json
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

resource "aws_lambda_function" "this" {
  function_name    = var.function_name
  role             = aws_iam_role.lambda_execution.arn
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  handler          = "lambda.lambda_handler"
  runtime          = var.runtime
  timeout          = var.timeout
  memory_size      = var.memory_size

  environment {
    variables = merge(var.environment_variables, {
      AGENT_RUNTIME_ARN = var.agent_runtime_arn
      AGENT_REGION      = data.aws_region.current.region
    })
  }

  tags = var.tags

  # The role must be able to write logs before the function's first invocation
  depends_on = [
    aws_iam_role_policy_attachment.managed,
    aws_iam_role_policy.custom,
    aws_iam_role_policy.lambda_logging,
    aws_cloudwatch_log_group.lambda,
  ]
}

