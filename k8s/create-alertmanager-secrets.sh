#!/bin/bash

# Create namespace if it doesn't exist
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Create the secret for Alertmanager (ensure to replace with real tokens before running)
kubectl create secret generic alertmanager-secrets -n monitoring \
  --from-literal=slack-url="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX" \
  --from-literal=telegram-bot-token="123456789:ABCDefghIJKLmnopQRSTuvwxYZ" \
  --from-literal=telegram-chat-id="-1001234567890"

echo "Alertmanager secrets created successfully!"
