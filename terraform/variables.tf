variable "aws_region" {
  description = "AWS Region für das Deployment"
  type        = string
  default     = "eu-central-1"
}

variable "project_name" {
  description = "Projektname als Präfix für AWS-Ressourcen"
  type        = string
  default     = "k3s-resilience-lab"
}

variable "vpc_cidr" {
  description = "CIDR-Block für die VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR-Block für das öffentliche Subnetz"
  type        = string
  default     = "10.0.1.0/24"
}

variable "instance_type" {
  description = "EC2 Instanztyp (t3.small: 2 vCPU, 2 GB RAM)"
  type        = string
  default     = "t3.small"
}

variable "root_volume_size" {
  description = "Größe des gp3 Root-Volumes in GB"
  type        = number
  default     = 30
}

variable "allowed_ssh_cidr" {
  description = "Erlaubte IP-Bereiche für SSH-Zugriff"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
