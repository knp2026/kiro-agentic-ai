
# Define the AWS provider
provider "aws" {
  region = "us-west-2"
}

# Define the Terraform backend for state storage
terraform {
  backend "s3" {
    bucket = "my-terraform-state-bucket"
    key    = "my-project/terraform.tfstate"
    region = "us-west-2"
  }
}

# Define the variables for the project
variable "project_name" {
  description = "The name of the project"
  type        = string
  default     = "my-project"
}

variable "environment" {
  description = "The environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Define the data sources for the project
data "aws_ami" "ubuntu" {
  most_recent = true

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  owners = ["099720109477"] # Canonical
}

# Define the resources for the project
resource "aws_instance" "app_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t2.micro"

  tags = {
    Name        = "${var.project_name}-app-server"
    Environment = var.environment
  }
}

# Define the outputs for the project
output "app_server_public_ip" {
  value = aws_instance.app_server.public_ip
}