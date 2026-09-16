terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "autoscaling-platform-tfstate-576003025159"
    key            = "dev/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "autoscaling-platform-tf-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region
}
