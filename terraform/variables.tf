variable "docker_host" {
  description = "Docker daemon endpoint Terraform talks to."
  type        = string
  default     = "unix:///var/run/docker.sock"
}

variable "name_prefix" {
  description = "Prefix for every Docker object created by this lab."
  type        = string
  default     = "juice-shop-lab"
}

variable "juice_shop_image" {
  description = "OWASP Juice Shop image reference."
  type        = string
  default     = "bkimminich/juice-shop:v20.4.0"
}

variable "host_port" {
  description = "Host port the lab target is published on."
  type        = number
  default     = 3000
}
