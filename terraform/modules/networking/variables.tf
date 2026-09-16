variable "project_name" {
  type    = string
  default = "autoscaling-platform"
}

variable "environment" {
  type = string
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "availability_zones" {
  type    = list(string)
  default = ["ap-south-1a", "ap-south-1b"]
}

variable "ssh_allowed_cidr" {
  description = "CIDR allowed to SSH into app instances - set to your IP/32 in real use"
  type        = string
  default     = "0.0.0.0/0"
}
