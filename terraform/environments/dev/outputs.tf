output "alb_dns_name" {
  value = module.loadbalancer.alb_dns_name
}

output "blue_asg_name" {
  value = module.compute_blue.asg_name
}

output "green_asg_name" {
  value = module.compute_green.asg_name
}

output "db_endpoint" {
  value = module.database.db_endpoint
}

output "vpc_id" {
  value = module.networking.vpc_id
}
