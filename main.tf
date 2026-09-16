
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  # Insert VPC configuration here
}

module "rds" {
  source = "terraform-aws-modules/rds/aws"
  # Insert RDS configuration here
}

module "ecs" {
  source = "terraform-aws-modules/ecs/aws"
  # Insert ECS configuration here
}

module "alb" {
  source = "terraform-aws-modules/alb/aws"
  # Insert ALB configuration here
}