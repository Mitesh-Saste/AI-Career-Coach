#!/bin/bash
set -e

echo "==> Updating apt packages..."
apt-get update -y

echo "==> Installing dependencies..."
apt-get install -y ca-certificates curl gnupg unzip

echo "==> Adding Docker GPG key..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo "==> Adding Docker apt repository..."
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
| tee /etc/apt/sources.list.d/docker.list

echo "==> Installing Docker CE..."
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io

echo "==> Starting and enabling Docker..."
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu

echo "==> Installing AWS CLI v2..."
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
unzip -q /tmp/awscliv2.zip -d /tmp
/tmp/aws/install
rm -rf /tmp/awscliv2.zip /tmp/aws

echo "==> Verifying installations..."
docker --version
aws --version

echo "==> Done. Docker and AWS CLI installed successfully."
