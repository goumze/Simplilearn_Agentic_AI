variable "aws_region" {
  description = "AWS region for the resources"
  type        = string
  default     = "ap-south-1"
}

variable "tags" {
  description = "Common tags applied to all resources"
  type        = map(string)
  default = {
    Project   = "vacation_planner"
    ManagedBy = "terraform"
  }
}
