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
  description = "OWASP Juice Shop image, pinned by digest (tag kept for readability)."
  type        = string
  default     = "bkimminich/juice-shop:v20.4.0@sha256:9bbaecc41791f00b002bc65931cc5ff355fbdb941fa72b06558c18dace43197b"
}

variable "host_port" {
  description = "Host port the lab target is published on."
  type        = number
  default     = 3000
}

variable "memory_limit_mb" {
  description = "Memory ceiling for the lab target container."
  type        = number
  default     = 1024
}
