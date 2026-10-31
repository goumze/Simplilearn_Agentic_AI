variable "memory_name" {
  description = "Name of the AgentCore memory (letters, numbers and underscores)"
  type        = string
  default     = "vacation_planner_memory"
}

variable "memory_description" {
  description = "Description of the AgentCore memory"
  type        = string
  default     = "Short-term memory for the vacation planner agent"
}

variable "event_expiry_days" {
  description = "Number of days after which memory events expire (7-365)"
  type        = number
  default     = 7
}

variable "summarization_strategy_name" {
  description = "Name of the built-in summarization memory strategy"
  type        = string
  default     = "vacation_planner_summarization"
}

variable "log_retention_days" {
  description = "Retention in days for the memory application log group"
  type        = number
  default     = 7
}

variable "tags" {
  description = "Tags applied to the AgentCore memory resources"
  type        = map(string)
  default     = {}
}
