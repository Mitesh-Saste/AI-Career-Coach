variable "aws_region" {
  description = "AWS region to deploy into"
  default     = "us-east-1"
}

variable "ami_id" {
  description = "Ubuntu 22.04 LTS AMI ID for us-east-1"
  default     = "ami-0ec10929233384c7f"
}

variable "key_name" {
  description = "Name of existing EC2 key pair (injected by Jenkins)"
}
