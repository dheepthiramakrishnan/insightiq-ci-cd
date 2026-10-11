# Jenkins with Docker CLI + Ansible preinstalled, so nothing needs installing on your PC except Docker Desktop
FROM jenkins/jenkins:lts-jdk17
USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates curl gnupg ansible python3-docker \
 && install -m 0755 -d /etc/apt/keyrings \
 && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
 && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
      > /etc/apt/sources.list.d/docker.list \
 && apt-get update && apt-get install -y --no-install-recommends docker-ce-cli \
 && ansible-galaxy collection install community.docker -p /usr/share/ansible/collections || true \
 && rm -rf /var/lib/apt/lists/*
# Runs as root so it can use the mounted Docker socket (fine for a local demo, not for production)
USER root
