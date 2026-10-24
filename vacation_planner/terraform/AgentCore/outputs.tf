output "agent_runtime_id" {
  description = "ID of the AgentCore agent runtime"
  value       = aws_bedrockagentcore_agent_runtime.vacation_planner.agent_runtime_id
}

output "agent_runtime_arn" {
  description = "ARN of the AgentCore agent runtime"
  value       = aws_bedrockagentcore_agent_runtime.vacation_planner.agent_runtime_arn
}

output "agent_runtime_role_arn" {
  description = "ARN of the IAM service role used by the AgentCore runtime"
  value       = aws_iam_role.agentcore_runtime.arn
}

output "agent_image_digest" {
  description = "Digest of the ECR image deployed to the runtime"
  value       = data.aws_ecr_image.agent.image_digest
}
