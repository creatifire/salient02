#!/bin/bash
# Salient Development Environment Setup Script
# Sets up the complete development environment with Docker services

set -e  # Exit on any error

echo "🚀 Starting Salient development environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Start the services
echo "📦 Starting Docker services..."
docker-compose -f docker-compose.dev.yml up -d

echo "⏳ Waiting for services to be ready..."
sleep 15

# Check service health
echo "🔍 Checking service health..."

# Check PostgreSQL
echo "  - PostgreSQL..."
if docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U salient_user -d salient_dev > /dev/null 2>&1; then
    echo "    ✅ PostgreSQL is ready"
else
    echo "    ⚠️  PostgreSQL is still starting up, please wait..."
fi

# Check Redis
echo "  - Redis..."
if docker-compose -f docker-compose.dev.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
    echo "    ✅ Redis is ready"
else
    echo "    ⚠️  Redis is still starting up, please wait..."
fi

# Run database migrations (when Alembic is set up)
if [ -f "backend/alembic.ini" ]; then
    echo "🔄 Running database migrations..."
    cd backend && alembic upgrade head
    cd ..
else
    echo "ℹ️  Alembic not yet configured - migrations will be available in Epic 0004"
fi

echo ""
echo "🎉 Development environment ready!"
echo ""
echo "📋 Service URLs:"
echo "  - PostgreSQL: localhost:5432"
echo "    Database: salient_dev"
echo "    User: salient_user"
echo "    Password: salient_pass"
echo ""
echo "  - Adminer (DB Admin): http://localhost:8080"
echo "    Server: postgres"
echo "    Username: salient_user"
echo "    Password: salient_pass"
echo "    Database: salient_dev"
echo ""
echo "  - Redis: localhost:6379"
echo ""
echo "🛠️  Useful commands:"
echo "  - Stop services: docker-compose -f docker-compose.dev.yml down"
echo "  - View logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "  - Reset database: ./scripts/dev-reset.sh"
echo ""
