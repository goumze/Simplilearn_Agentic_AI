output "gateway_id" {
  description = "ID of the AgentCore gateway"
  value       = aws_bedrockagentcore_gateway.this.gateway_id
}

output "gateway_arn" {
  description = "ARN of the AgentCore gateway"
  value       = aws_bedrockagentcore_gateway.this.gateway_arn
}

output "gateway_url" {
  description = "MCP endpoint URL of the AgentCore gateway"
  value       = aws_bedrockagentcore_gateway.this.gateway_url
}

output "gateway_role_arn" {
  description = "ARN of the IAM role the gateway assumes (inbound/outbound IAM auth)"
  value       = aws_iam_role.gateway.arn
}

output "discovery_url" {
  description = "OpenID Connect discovery URL used by the gateway's JWT authorizer"
  value       = local.discovery_url
}

output "target_id" {
  description = "ID of the travel agent tool gateway target"
  value       = aws_bedrockagentcore_gateway_target.travel_agent_tool.target_id
}
