output "target_url" {
  description = "URL of the lab target on the Docker host."
  value       = "http://127.0.0.1:${var.host_port}"
}

output "internal_target_url" {
  description = "URL scanners on the lab network should use."
  value       = "http://juice-shop:3000"
}

output "network_name" {
  description = "Front Docker network that carries the loopback port binding."
  value       = docker_network.lab.name
}

output "scan_network_name" {
  description = "Internal (no egress) network the DAST scanner must join."
  value       = docker_network.scan.name
}

output "container_name" {
  description = "Name of the Juice Shop container."
  value       = docker_container.juice_shop.name
}
