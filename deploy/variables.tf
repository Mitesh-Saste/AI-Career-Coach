variable "aws_region" {
  default = "us-east-1"
}

variable "ami_id" {
  description = "Ubuntu 22.04 LTS AMI for us-east-1"
  default     = "ami-0ec10929233384c7f"
}

variable "key_name" {
  description = "Name of your existing EC2 key pair"
}
