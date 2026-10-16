#!/usr/bin/env bash
set -euo pipefail
gh api repos/JasperHG90/Knowledge-management/actions/permissions/workflow
gh api repos/JasperHG90/Knowledge-management/actions/permissions/workflow --jq .can_approve_pull_request_reviews | grep -x true
