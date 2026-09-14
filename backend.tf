
# Define the backend to store the Terraform state file

terraform {
  backend "s3" {
    bucket = "my-terraform-state-bucket"
    key    = "my-project/terraform.tfstate"
    region = "us-west-2"
  }
}