
# Define output variables for the Terraform configuration
output "app_server_public_ip" {
  description = "The public IP address of the application server"
  value       = aws_instance.app_server.public_ip
}

output "database_endpoint" {
  description = "The endpoint of the database"
  value       = aws_db_instance.database.endpoint
}

output "message_broker_endpoint" {
  description = "The endpoint of the message broker"
  value       = aws_mq_broker.message_broker.instances[0].endpoints[0]
}