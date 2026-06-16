#!/usr/bin/env bash
# Restart production services through systemd. Requires deploy/sudoers-personal-deploy.
set -euo pipefail

sudo systemctl restart personal-backend.service personal-frontend.service
systemctl status personal-backend.service --no-pager
systemctl status personal-frontend.service --no-pager
