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
