#!/bin/bash
# Salient Development Database Reset Script
# Resets the development database with fresh data

set -e  # Exit on any error

echo "🔄 Resetting Salient development database..."

# Confirm the action
read -p "⚠️  This will destroy all data in the development database. Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Database reset cancelled."
    exit 0
fi

echo "🛑 Stopping services and removing volumes..."
docker-compose -f docker-compose.dev.yml down -v

echo "📦 Starting PostgreSQL service..."
docker-compose -f docker-compose.dev.yml up -d postgres

echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Wait for PostgreSQL to be fully ready
echo "🔍 Checking PostgreSQL readiness..."
for i in {1..30}; do
    if docker-compose -f docker-compose.dev.yml exec -T postgres pg_isready -U salient_user -d salient_dev > /dev/null 2>&1; then
        echo "✅ PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ PostgreSQL failed to start within timeout"
        exit 1
    fi
    echo "  Waiting... ($i/30)"
    sleep 2
done

# Start remaining services
echo "📦 Starting remaining services..."
docker-compose -f docker-compose.dev.yml up -d

# Run database migrations (when Alembic is set up)
if [ -f "backend/alembic.ini" ]; then
    echo "🔄 Running database migrations..."
    cd backend && alembic upgrade head
    cd ..
else
    echo "ℹ️  Alembic not yet configured - migrations will be available in Epic 0004"
fi

echo ""
echo "🎉 Database reset complete!"
echo ""
echo "📋 Fresh development environment ready:"
echo "  - PostgreSQL: localhost:5432 (fresh database)"
echo "  - Adminer: http://localhost:8080"
echo "  - Redis: localhost:6379 (fresh instance)"
echo ""
