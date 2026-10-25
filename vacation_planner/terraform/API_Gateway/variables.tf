variable "lambda_function_name" {
  description = "Name of the Lambda function the API invokes"
  type        = string
}

variable "lambda_invoke_arn" {
  description = "Invoke ARN of the Lambda function (used as the integration URI)"
  type        = string
}

variable "api_name" {
  description = "Name of the REST API"
  type        = string
  default     = "vacation-planner-api"
}

variable "resource_path" {
  description = "Path segment exposed under the API root"
  type        = string
  default     = "vacation_planner"
}

variable "stage_name" {
  description = "Deployment stage name"
  type        = string
  default     = "dev"
}

variable "tags" {
  description = "Tags applied to API Gateway resources"
  type        = map(string)
  default     = {}
}
