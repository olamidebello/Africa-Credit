#!/usr/bin/env bash
set -euo pipefail
if [ "$(id -u)" -ne 0 ]; then
  echo "Run with sudo bash deploy/pull-and-deploy.sh"
  exit 1
fi
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y git ansible
deployer=/opt/africa-credit-deployer
if [ ! -d "$deployer/.git" ]; then
  git clone https://github.com/olamidebello/Africa-Credit.git "$deployer"
else
  if [ -n "$(git -C "$deployer" status --porcelain)" ]; then
    echo "Deployer has local changes; preserve or commit them before retrying."
    exit 1
  fi
  git -C "$deployer" checkout main
  git -C "$deployer" pull --ff-only origin main
fi
exec ansible-playbook -i localhost, -c local "$deployer/deploy/pull-and-deploy.yml" "$@"
