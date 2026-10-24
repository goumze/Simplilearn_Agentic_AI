variable "agent_runtime_name" {
  description = "Name of the AgentCore agent runtime (letters, digits, underscores; must start with a letter)"
  type        = string
  default     = "vacation_planner"
}

variable "repository_name" {
  description = "Name of the ECR repository holding the agent image"
  type        = string
}

variable "repository_url" {
  description = "URL of the ECR repository holding the agent image"
  type        = string
}

variable "image_tag" {
  description = "Tag of the agent image in ECR to deploy"
  type        = string
  default     = "latest"
}

variable "tags" {
  description = "Tags applied to AgentCore resources"
  type        = map(string)
  default     = {}
}
