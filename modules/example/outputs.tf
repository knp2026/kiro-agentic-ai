
# Define the outputs to display after the resources are created in the module

output "instance_ip" {
  description = "Public IP address of the created EC2 instance"
  value       = aws_instance.example.public_ip
}

# Add more outputs as needed for your project