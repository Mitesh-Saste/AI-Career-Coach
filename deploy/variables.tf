variable "aws_region" {
  default = "ap-south-1"
}

variable "ami_id" {
  description = "Ubuntu 22.04 LTS AMI for ap-south-1"
  default     = "ami-0f58b397bc5c1f2e8"
}

variable "key_name" {
  description = "Name of your existing EC2 key pair"
}
