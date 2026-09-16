
output "rds_endpoint" {
  description = "The connection endpoint"
  value = module.rds.this_db_instance_endpoint
}

# Insert other outputs here