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
