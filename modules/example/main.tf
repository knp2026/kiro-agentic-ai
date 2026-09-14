
# Define a Terraform module for creating an EC2 instance

resource "aws_instance" "example" {
  ami           = data.aws_ami.example.id
  instance_type = var.instance_type

  # Add more configurations as needed for your project
}