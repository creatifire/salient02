#!/bin/bash

# Test runner script for backend tests
# Run from backend/ directory
#
# Prerequisites: pip install -r ../requirements-dev.txt

echo "🧪 Running Backend Test Suite"
echo "================================"

# Activate virtual environment if not already active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Please install dev dependencies:"
    echo "   pip install -r ../requirements-dev.txt"
    exit 1
fi

# Run unit tests
echo ""
echo "🔹 Running Unit Tests..."
pytest tests/unit/ -v --tb=short

# Run integration tests (skip if marked as slow)
echo ""
echo "🔹 Running Integration Tests..."
pytest tests/ -m integration -v --tb=short

# Run all tests with coverage
echo ""
echo "🔹 Running Full Test Suite with Coverage..."
pytest tests/ --cov=app --cov-report=term-missing --cov-report=html:htmlcov

# Show summary
echo ""
echo "✅ Test run complete!"
echo "📊 Coverage report available at: htmlcov/index.html"
