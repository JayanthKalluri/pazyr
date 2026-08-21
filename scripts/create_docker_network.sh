#!/usr/bin/env bash
networks=("data-network" "platform-network" "coe-network" "dns-network")

# Detect runtime
if command -v podman >/dev/null 2>&1; then
  runtime="podman"
elif command -v docker >/dev/null 2>&1; then
  runtime="docker"
else
  echo "Neither Podman nor Docker found in PATH."
  exit 1
fi

for net in "${networks[@]}"; do
  if ! $runtime network ls --format '{{.Name}}' | grep -q "^${net}$"; then
    echo "Creating network $net with $runtime..."
    $runtime network create "$net"
  else
    echo "Network $net already exists."
  fi
done
