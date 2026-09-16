output "alb_dns_name" {
  value = module.loadbalancer.alb_dns_name
}

output "asg_name" {
  value = module.compute.asg_name
}

output "db_endpoint" {
  value = module.database.db_endpoint
}

output "vpc_id" {
  value = module.networking.vpc_id
}
