variable "project_name" {
  type    = string
  default = "autoscaling-platform"
}

variable "environment" {
  type = string
}

variable "subnet_ids" {
  type = list(string)
}

variable "db_security_group_id" {
  type = string
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"  # free-tier eligible
}

variable "db_name" {
  type    = string
  default = "appdb"
}

variable "db_username" {
  type      = string
  sensitive = true
}

variable "db_password" {
  type      = string
  sensitive = true
}
