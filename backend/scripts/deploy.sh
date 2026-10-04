#!/usr/bin/env bash
# ==============================================================================
# WatchMe Production Deployment Script for Oracle Cloud Always Free VM
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

cd "${BACKEND_DIR}"

echo "=========================================================="
echo " Starting WatchMe Production Deployment"
echo "=========================================================="

# Check for .env file
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found in ${BACKEND_DIR}!"
    echo "Please copy .env.example to .env and configure your secrets first:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Hardening file permissions
echo "🔒 Securing .env file permissions (chmod 600)..."
chmod 600 .env

if [ -f "watchme-*.json" ]; then
    chmod 400 watchme-*.json
fi

# Build and start containers
echo "🐳 Building and starting production containers (Backend + Caddy TLS)..."
docker compose -f docker-compose.prod.yml up -d --build --remove-orphans

echo "⏳ Waiting for backend service to become healthy..."
MAX_RETRIES=20
COUNT=0
HEALTHY=false

while [ $COUNT -lt $MAX_RETRIES ]; do
    if docker compose -f docker-compose.prod.yml ps backend | grep -q "healthy"; then
        HEALTHY=true
        break
    fi
    echo "   Checking health... (attempt $((COUNT + 1))/$MAX_RETRIES)"
    sleep 3
    COUNT=$((COUNT + 1))
done

if [ "$HEALTHY" = true ]; then
    echo "✅ Backend is healthy and running!"
else
    echo "⚠️ Backend container is still initializing or encountered an issue. Showing logs:"
    docker compose -f docker-compose.prod.yml logs --tail=50 backend
fi

echo "=========================================================="
echo " Running Alembic Database Migrations..."
echo "=========================================================="
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head || {
    echo "⚠️ Alembic migration command returned non-zero. Check database credentials in .env."
}

echo "=========================================================="
echo " Deployment Complete!"
echo " Status of running containers:"
docker compose -f docker-compose.prod.yml ps
echo "=========================================================="
