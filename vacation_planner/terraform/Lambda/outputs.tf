output "lambda_execution_role_arn" {
  description = "ARN of the IAM execution role for the Lambda function"
  value       = aws_iam_role.lambda_execution.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.vacation_planner.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.vacation_planner.arn
}

output "lambda_log_group_name" {
  description = "Name of the CloudWatch log group for the Lambda function"
  value       = aws_cloudwatch_log_group.lambda.name
}
