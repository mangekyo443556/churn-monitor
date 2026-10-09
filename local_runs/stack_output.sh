#!/usr/bin/env bash
# Lee una salida (Output) del stack de CloudFormation.
# Uso: ./local_runs/stack_output.sh churn-monitor-dev DataBucketName
set -euo pipefail
aws cloudformation describe-stacks --stack-name "$1" \
  --query "Stacks[0].Outputs[?OutputKey=='$2'].OutputValue" --output text
