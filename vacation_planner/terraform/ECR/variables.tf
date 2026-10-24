variable "repository_name" {
  description = "Name of the ECR repository"
  type        = string
  default     = "vacation_planner"
}

variable "force_delete" {
  description = "Delete the repository even if it contains images"
  type        = bool
  default     = false
}

variable "max_image_count" {
  description = "Number of images to retain in the repository"
  type        = number
  default     = 10
}

variable "tags" {
  description = "Tags applied to the repository"
  type        = map(string)
  default     = {}
}
