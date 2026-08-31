#!/bin/bash
set -e

echo "⚠️ Đang tiến hành TẮT VÀ XÓA BỎ toàn bộ hệ thống..."

echo "🛑 1. Xóa bỏ luật cảnh báo và thu thập Metrics"
kubectl delete -f k8s/service-monitor.yaml --ignore-not-found
kubectl delete -f k8s/prometheus-rules.yaml --ignore-not-found

echo "🔥 2. Gỡ cài đặt hệ thống giám sát (Prometheus & Grafana)"
helm uninstall prometheus --namespace monitoring || true
kubectl delete secret alertmanager-secrets -n monitoring --ignore-not-found

echo "🛑 3. Xóa bỏ Backend API và Ingress"
kubectl delete -f k8s/ingress.yaml --ignore-not-found
kubectl delete -f k8s/backend.yaml --ignore-not-found

echo "🛑 4. Xóa bỏ Cơ sở dữ liệu và Job Migration"
kubectl delete -f k8s/migration-job.yaml --ignore-not-found
kubectl delete -f k8s/database.yaml --ignore-not-found
kubectl delete -f k8s/redis.yaml --ignore-not-found

echo "🧹 5. Dọn dẹp Config và Secrets"
kubectl delete -f k8s/config.yaml --ignore-not-found
kubectl delete secret backend-secrets -n backend-prod --ignore-not-found

echo "🗑️ 6. Xóa vĩnh viễn Namespace (Cảnh báo: Dữ liệu PVC sẽ bị xóa)"
kubectl delete namespace backend-prod --ignore-not-found
kubectl delete namespace monitoring --ignore-not-found

echo "✅ HỆ THỐNG ĐÃ ĐƯỢC TẮT VÀ DỌN DẸP HOÀN TOÀN!"
