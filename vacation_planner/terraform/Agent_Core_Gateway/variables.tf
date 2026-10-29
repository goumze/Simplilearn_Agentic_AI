variable "gateway_name" {
  description = "Name of the AgentCore gateway (letters, digits, hyphens)"
  type        = string
  default     = "vacation-planner-gateway"
}

variable "gateway_description" {
  description = "Description of the AgentCore gateway"
  type        = string
  default     = "Gateway exposing vacation planner tools to agents"
}

variable "issuer_url" {
  description = "OIDC issuer URL of the identity provider (Cognito); the discovery URL is derived from it"
  type        = string
}

variable "allowed_clients" {
  description = "App client IDs whose JWTs the gateway accepts"
  type        = list(string)
}

variable "travel_tool_lambda_arn" {
  description = "ARN of the Lambda function backing the travel agent tool target"
  type        = string
}

variable "target_name" {
  description = "Name of the gateway target that exposes the travel agent tool (letters, digits, hyphens only)"
  type        = string
  default     = "target-travel-agent-tool"
}

variable "target_description" {
  description = "Description of the gateway target"
  type        = string
  default     = "travel_agent_tool"
}

variable "tags" {
  description = "Tags applied to AgentCore gateway resources"
  type        = map(string)
  default     = {}
}
