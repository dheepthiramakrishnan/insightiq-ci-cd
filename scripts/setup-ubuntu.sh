#!/usr/bin/env bash
# One-time setup for an Ubuntu 22.04/24.04 VM: Docker, Jenkins, Ansible.
# Run with: bash scripts/setup-ubuntu.sh
set -euo pipefail

sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg fontconfig openjdk-17-jre git \
  software-properties-common python3-pip python3-docker

# Docker
sudo apt-get install -y docker.io
sudo systemctl enable --now docker

# Jenkins (official LTS repo)
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" \
  | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt-get update
sudo apt-get install -y jenkins

# Ansible + Docker collection
sudo apt-get install -y ansible
sudo ansible-galaxy collection install community.docker -p /usr/share/ansible/collections || true

# Let Jenkins use Docker, then restart
sudo usermod -aG docker jenkins
sudo systemctl enable --now jenkins
sudo systemctl restart jenkins

echo
echo "Done. Open http://<this-vm-ip>:8080"
echo "Initial admin password:"
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
