variable "project_name" {
  type    = string
  default = "autoscaling-platform"
}

variable "environment" {
  type = string
}

variable "instance_type" {
  type    = string
  default = "t2.micro"  # free-tier eligible
}

variable "subnet_ids" {
  type = list(string)
}

variable "app_security_group_id" {
  type = string
}

variable "target_group_arns" {
  type = list(string)
}

variable "min_size" {
  type    = number
  default = 2
}

variable "max_size" {
  type    = number
  default = 4
}

variable "desired_capacity" {
  type    = number
  default = 2
}
