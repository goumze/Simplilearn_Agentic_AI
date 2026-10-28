variable "function_name" {
  description = "Name of the Lambda function; also names the execution role, log group, and build artifact"
  type        = string
}

variable "source_dir" {
  description = "Folder name under vacation_planner/src/ that contains the function's lambda.py"
  type        = string
}

variable "agent_runtime_arn" {
  description = "ARN of the AgentCore agent runtime the function invokes (passed as AGENT_RUNTIME_ARN)"
  type        = string
}

variable "managed_policy_arns" {
  description = "IAM managed policy ARNs to attach to the function's execution role"
  type        = list(string)
  default     = []
}

variable "inline_policy_json" {
  description = "Optional inline IAM policy document (JSON) for the execution role; null to skip"
  type        = string
  default     = null
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
