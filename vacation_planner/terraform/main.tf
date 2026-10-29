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

  function_name       = "vacation_planner"
  source_dir          = "vacation_planner"
  agent_runtime_arn   = module.agentcore.agent_runtime_arn
  managed_policy_arns = ["arn:aws:iam::aws:policy/BedrockAgentCoreFullAccess"]
  tags                = var.tags
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

module "travel_details_tool" {
  source = "./Lambda"

  function_name       = "bedrock_agentcore_travel_details_tool"
  source_dir          = "bedrock_agentcore_travel_details_tool"
  agent_runtime_arn   = module.agentcore.agent_runtime_arn
  managed_policy_arns = ["arn:aws:iam::aws:policy/AdministratorAccess"]
  inline_policy_json  = null
  environment_variables = {
    TRAVEL_TABLE_NAME = module.dynamodb.table_name
  }
  tags = var.tags
}

output "travel_details_tool_function_name" {
  value = module.travel_details_tool.lambda_function_name
}

output "travel_details_tool_function_arn" {
  value = module.travel_details_tool.lambda_function_arn
}

module "agent_core_gateway" {
  source = "./Agent_Core_Gateway"

  issuer_url             = module.cognito.issuer_url
  allowed_clients        = [module.cognito.client_id]
  travel_tool_lambda_arn = module.travel_details_tool.lambda_function_arn
  tags                   = var.tags
}

output "agent_core_gateway_url" {
  value = module.agent_core_gateway.gateway_url
}

output "agent_core_gateway_discovery_url" {
  value = module.agent_core_gateway.discovery_url
}
