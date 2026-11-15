# OWASP Juice Shop lab target, provisioned on the local Docker engine.
# No cloud resources are created; this keeps the lab free and contained.

resource "docker_network" "lab" {
  name = "${var.name_prefix}-net"
}

resource "docker_image" "juice_shop" {
  name         = var.juice_shop_image
  keep_locally = true
}

resource "docker_container" "juice_shop" {
  name  = "${var.name_prefix}-app"
  image = docker_image.juice_shop.image_id

  ports {
    internal = 3000
    external = var.host_port
  }

  networks_advanced {
    name    = docker_network.lab.name
    aliases = ["juice-shop"]
  }
}
