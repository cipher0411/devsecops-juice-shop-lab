# OWASP Juice Shop lab target, provisioned on the local Docker engine.
# No cloud resources are created; this keeps the lab free and contained.
#
# Hardening (enforced by security/checkov/policies):
#   CKV2_LAB_001  publish on 127.0.0.1 only - the provider default is 0.0.0.0
#   CKV2_LAB_002  drop every Linux capability
#   CKV2_LAB_003  no-new-privileges
#   CKV2_LAB_004  memory limit
#   CKV2_LAB_005  image pinned by sha256 digest
#   CKV2_LAB_006  never privileged
#   CKV2_LAB_007  explicit non-root user

# Front network: carries the loopback-only port binding to the host.
resource "docker_network" "lab" {
  name = "${var.name_prefix}-net"
}

# Scan network: internal = true means no route to the internet. The DAST
# scanner joins ONLY this network, so its crawler physically cannot reach
# third-party sites linked or embedded by the target (see LAB-OPS-01).
resource "docker_network" "scan" {
  name     = "${var.name_prefix}-scan"
  internal = true
}

resource "docker_image" "juice_shop" {
  name         = var.juice_shop_image
  keep_locally = true
}

resource "docker_container" "juice_shop" {
  name  = "${var.name_prefix}-app"
  image = docker_image.juice_shop.image_id

  # Distroless "nonroot" UID used by the upstream image, set explicitly.
  user       = "65532"
  privileged = false
  restart    = "no"
  memory     = var.memory_limit_mb

  capabilities {
    drop = ["ALL"]
  }

  security_opts = ["no-new-privileges:true"]

  ports {
    internal = 3000
    external = var.host_port
    ip       = "127.0.0.1"
  }

  networks_advanced {
    name    = docker_network.lab.name
    aliases = ["juice-shop"]
  }

  networks_advanced {
    name    = docker_network.scan.name
    aliases = ["juice-shop"]
  }
}
