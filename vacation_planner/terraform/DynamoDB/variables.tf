variable "table_name" {
  description = "Name of the DynamoDB table"
  type        = string
  default     = "travel_packages"
}

variable "partition_key" {
  description = "Partition key attribute name (string type)"
  type        = string
  default     = "city"
}

variable "billing_mode" {
  description = "DynamoDB billing mode (PAY_PER_REQUEST or PROVISIONED)"
  type        = string
  default     = "PAY_PER_REQUEST"
}

variable "tags" {
  description = "Tags applied to the DynamoDB table"
  type        = map(string)
  default     = {}
}
