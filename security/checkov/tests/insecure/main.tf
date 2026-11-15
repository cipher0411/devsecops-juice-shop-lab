# Deliberately insecure fixture. Every CKV2_LAB_* policy MUST fail here.
# Used by scripts/test-checkov-policies.sh to prove the policies detect
# explicit bad values, not only missing attributes. Never applied.

resource "docker_image" "bad" {
  name = "bkimminich/juice-shop:latest"
}

resource "docker_container" "bad" {
  name       = "bad"
  image      = docker_image.bad.image_id
  user       = "0"
  privileged = true
  memory     = null

  capabilities {
    drop = ["NET_RAW"]
  }

  security_opts = ["label=disable"]

  ports {
    internal = 3000
    external = 3000
    ip       = "0.0.0.0"
  }
}
