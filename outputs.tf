
# Define the outputs to display after the resources are created

output "instance_ips" {
  description = "Public IP addresses of the created EC2 instances"
  value       = [for i in aws_instance.example : i.public_ip]
}

# Add more outputs as needed for your project