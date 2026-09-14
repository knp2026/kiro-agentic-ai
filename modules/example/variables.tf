
# Define the variables used in the main.tf file of the module

variable "instance_type" {
  description = "Type of EC2 instance to create"
  type        = string
  default     = "t2.micro"
}

# Add more variables as needed for your project