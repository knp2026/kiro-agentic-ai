
# Define the provider (AWS)
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"
}

# Define the VPC
resource "aws_vpc" "project_vpc" {
  cidr_block = "10.0.0.0/16"
  enable_dns_support = true
  enable_dns_hostnames = true
}

# Define the subnets
resource "aws_subnet" "public_subnet" {
  vpc_id            = aws_vpc.project_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-west-2a"
}

resource "aws_subnet" "private_subnet" {
  vpc_id            = aws_vpc.project_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-west-2b"
}

# Define the security groups
resource "aws_security_group" "api_security_group" {
  name        = "api_security_group"
  description = "Allow inbound traffic for API"
  vpc_id      = aws_vpc.project_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Define the EC2 instance for the API
resource "aws_instance" "api_instance" {
  ami           = "ami-0c94855ba95c574c8"
  instance_type = "t2.micro"
  subnet_id     = aws_subnet.public_subnet.id

  vpc_security_group_ids = [aws_security_group.api_security_group.id]

  user_data = <<-EOF
              #!/bin/bash
              sudo apt-get update
              sudo apt-get install -y docker.io
              sudo systemctl start docker
              sudo docker pull your-docker-image
              sudo docker run -p 80:80 your-docker-image
              EOF

  tags = {
    Name = "APIInstance"
  }
}