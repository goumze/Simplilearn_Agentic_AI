module "ecr" {
  source = "./ECR"

  repository_name = "vacation_planner"
  force_delete    = true
}

output "ecr_repository_url" {
  value = module.ecr.repository_url
}

module "agentcore" {
  source = "./AgentCore"

  repository_name = module.ecr.repository_name
  repository_url  = module.ecr.repository_url
  tags            = var.tags

  depends_on = [module.ecr]
}

output "agent_runtime_arn" {
  value = module.agentcore.agent_runtime_arn
}

module "lambda" {
  source = "./Lambda"

  agent_runtime_arn = module.agentcore.agent_runtime_arn
  tags              = var.tags
}

output "lambda_execution_role_arn" {
  value = module.lambda.lambda_execution_role_arn
}

output "lambda_function_arn" {
  value = module.lambda.lambda_function_arn
}

module "api_gateway" {
  source = "./API_Gateway"

  lambda_function_name = module.lambda.lambda_function_name
  lambda_invoke_arn    = module.lambda.lambda_invoke_arn
  tags                 = var.tags

  depends_on = [module.lambda]
}

output "api_gateway_invoke_url" {
  value = module.api_gateway.api_gateway_invoke_url
}

module "cognito" {
  source = "./Cognito"

  tags = var.tags
}

output "cognito_user_pool_id" {
  value = module.cognito.user_pool_id
}

output "cognito_issuer_url" {
  value = module.cognito.issuer_url
}

output "cognito_token_endpoint" {
  value = module.cognito.token_endpoint
}

output "cognito_client_id" {
  value = module.cognito.client_id
}

output "cognito_client_secret" {
  value     = module.cognito.client_secret
  sensitive = true
}

output "cognito_oauth_scope" {
  value = module.cognito.oauth_scope
}

module "dynamodb" {
  source = "./DynamoDB"

  tags = var.tags
}

output "dynamodb_table_name" {
  value = module.dynamodb.table_name
}

output "dynamodb_table_arn" {
  value = module.dynamodb.table_arn
}
