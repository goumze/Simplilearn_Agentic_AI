variable "user_pool_name" {
  description = "Name of the Cognito user pool"
  type        = string
  default     = "vacation-planner-user-pool"
}

variable "app_client_name" {
  description = "Name of the app client used for the client credentials flow"
  type        = string
  default     = "vacation-planner-agent-client"
}

variable "domain_prefix" {
  description = "Prefix of the Cognito hosted domain (must be unique within the region)"
  type        = string
  default     = "vacation-planner-auth"
}

variable "resource_server_identifier" {
  description = "Identifier of the resource server (prefix of the custom scope)"
  type        = string
  default     = "vacation-planner"
}

variable "resource_server_name" {
  description = "Display name of the resource server"
  type        = string
  default     = "Vacation Planner API"
}

variable "scope_name" {
  description = "Custom scope granted to the app client"
  type        = string
  default     = "invoke"
}

variable "scope_description" {
  description = "Description of the custom scope"
  type        = string
  default     = "Invoke vacation planner tools"
}

variable "access_token_validity_minutes" {
  description = "Lifetime of the access token (JWT) in minutes"
  type        = number
  default     = 60
}

variable "password_min_length" {
  description = "Minimum password length for the user pool"
  type        = number
  default     = 12
}

variable "deletion_protection" {
  description = "Deletion protection for the user pool (ACTIVE or INACTIVE)"
  type        = string
  default     = "INACTIVE"
}

variable "tags" {
  description = "Tags applied to Cognito resources"
  type        = map(string)
  default     = {}
}
