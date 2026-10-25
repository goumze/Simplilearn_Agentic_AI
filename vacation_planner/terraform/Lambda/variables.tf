variable "function_name" {
  description = "Name of the Lambda function; used to name the execution role and log group"
  type        = string
  default     = "vacation_planner"
}

variable "agent_runtime_arn" {
  description = "ARN of the AgentCore agent runtime the function invokes (passed as AGENT_RUNTIME_ARN)"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime for the function"
  type        = string
  default     = "python3.13"
}

variable "timeout" {
  description = "Function timeout in seconds; AgentCore invocations can take a while"
  type        = number
  default     = 120
}

variable "memory_size" {
  description = "Function memory in MB"
  type        = number
  default     = 256
}

variable "log_retention_days" {
  description = "Retention period, in days, for the function's CloudWatch log group"
  type        = number
  default     = 14
}

variable "tags" {
  description = "Tags applied to Lambda resources"
  type        = map(string)
  default     = {}
}
