module "networking" {
  source = "../../modules/networking"

  environment      = var.environment
  vpc_cidr         = var.vpc_cidr
  ssh_allowed_cidr = var.ssh_allowed_cidr
}

module "loadbalancer" {
  source = "../../modules/loadbalancer"

  environment            = var.environment
  vpc_id                 = module.networking.vpc_id
  subnet_ids             = module.networking.public_subnet_ids
  alb_security_group_id  = module.networking.alb_security_group_id
}

module "compute_blue" {
  source = "../../modules/compute"

  environment            = var.environment
  slot                   = "blue"
  instance_type          = var.instance_type
  subnet_ids             = module.networking.public_subnet_ids
  app_security_group_id  = module.networking.app_security_group_id
  target_group_arns      = [module.loadbalancer.blue_target_group_arn]
  min_size               = var.asg_min_size
  max_size               = var.asg_max_size
  desired_capacity       = var.asg_desired_capacity
  key_name               = var.key_name
}

module "compute_green" {
  source = "../../modules/compute"

  environment            = var.environment
  slot                   = "green"
  instance_type          = var.instance_type
  subnet_ids             = module.networking.public_subnet_ids
  app_security_group_id  = module.networking.app_security_group_id
  target_group_arns      = [module.loadbalancer.green_target_group_arn]
  min_size               = var.asg_min_size
  max_size               = var.asg_max_size
  desired_capacity       = var.asg_desired_capacity
  key_name               = var.key_name
}

module "database" {
  source = "../../modules/database"

  environment           = var.environment
  subnet_ids            = module.networking.public_subnet_ids
  db_security_group_id  = module.networking.db_security_group_id
  db_instance_class     = var.db_instance_class
  db_username           = var.db_username
  db_password            = var.db_password
}
