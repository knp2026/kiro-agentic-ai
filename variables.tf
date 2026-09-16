
# Define input variables for the Terraform configuration
variable "aws_region" {
  description = "The AWS region to deploy resources in"
  type        = string
  default     = "us-west-2"
}

variable "db_username" {
  description = "The username for the database"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "The password for the database"
  type        = string
  sensitive   = true
}

variable "message_broker_username" {
  description = "The username for the message broker"
  type        = string
  default     = "admin"
}

variable "message_broker_password" {
  description = "The password for the message broker"
  type        = string
  sensitive   = true
}