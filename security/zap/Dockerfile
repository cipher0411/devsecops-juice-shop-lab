# Hermetic ZAP scanner image.
# zap-baseline.py installs the beta passive rules (pscanrulesBeta) from the
# internet at start-up. The DAST scan runs on an internal, no-egress Docker
# network (LAB-OPS-01), so the add-ons are baked in at build time instead.
FROM ghcr.io/zaproxy/zaproxy:2.17.0@sha256:9624669db72f54d86c4b46a7064518bd9bf79d8c61a4c31befa9923489f328af

RUN zap.sh -cmd -silent -addonupdate -addoninstall pscanrulesBeta \
 && ls /home/zap/.ZAP/plugin | sort > /home/zap/addons.txt \
 && grep -q '^pscanrulesBeta-' /home/zap/addons.txt

# DS-0002: state the non-root runtime user explicitly rather than inheriting it.
USER zap

# DS-0026: one-shot CLI scanner, no long-running service to health-check.
HEALTHCHECK NONE
