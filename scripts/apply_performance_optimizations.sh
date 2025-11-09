#!/bin/bash

# Performance Optimization Setup Script
# This script helps you apply all performance optimizations to Tales Analytics

set -e  # Exit on error

echo "========================================="
echo "Tales Analytics Performance Optimization"
echo "========================================="
echo ""

# Check if Redis is installed
echo "Step 1: Checking Redis installation..."
if command -v redis-cli &> /dev/null; then
    echo "✓ Redis is installed"

    # Check if Redis is running
    if redis-cli ping &> /dev/null; then
        echo "✓ Redis is running"
    else
        echo "⚠ Redis is installed but not running"
        echo ""
        read -p "Would you like to start Redis? (y/n): " START_REDIS
        if [ "$START_REDIS" = "y" ]; then
            if [[ "$OSTYPE" == "darwin"* ]]; then
                brew services start redis
                echo "✓ Redis started via Homebrew"
            else
                echo "Please start Redis manually: sudo systemctl start redis"
            fi
        fi
    fi
else
    echo "✗ Redis not found"
    echo ""
    echo "Installing Redis:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  macOS: brew install redis && brew services start redis"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "  Ubuntu/Debian: sudo apt-get install redis-server"
        echo "  CentOS/RHEL: sudo yum install redis"
    else
        echo "  See: https://redis.io/download"
    fi
    echo ""
    read -p "Continue without Redis? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        exit 1
    fi
fi

echo ""
echo "Step 2: Checking environment variables..."

# Check for .env file
if [ -f ".env" ]; then
    echo "✓ .env file found"

    # Check for Redis URL
    if grep -q "REDIS_URL" .env; then
        echo "✓ REDIS_URL configured"
    else
        echo "⚠ REDIS_URL not found in .env"
        read -p "Add REDIS_URL=redis://localhost:6379/0 to .env? (y/n): " ADD_REDIS
        if [ "$ADD_REDIS" = "y" ]; then
            echo "REDIS_URL=redis://localhost:6379/0" >> .env
            echo "✓ Added REDIS_URL to .env"
        fi
    fi

    # Check for analytics settings
    if grep -q "ANALYTICS_DEFAULT_LOOKBACK_DAYS" .env; then
        echo "✓ ANALYTICS_DEFAULT_LOOKBACK_DAYS configured"
    else
        echo "⚠ ANALYTICS_DEFAULT_LOOKBACK_DAYS not found in .env"
        read -p "Add ANALYTICS_DEFAULT_LOOKBACK_DAYS=180 to .env? (y/n): " ADD_DAYS
        if [ "$ADD_DAYS" = "y" ]; then
            echo "" >> .env
            echo "# Performance Optimization Settings" >> .env
            echo "ANALYTICS_DEFAULT_LOOKBACK_DAYS=180" >> .env
            echo "REDIS_CACHE_TTL_DASHBOARD=900" >> .env
            echo "REDIS_CACHE_TTL_TRENDS=3600" >> .env
            echo "REDIS_CACHE_TTL_BATCH=86400" >> .env
            echo "✓ Added performance settings to .env"
        fi
    fi
else
    echo "✗ .env file not found"
    read -p "Create .env from .env.example? (y/n): " CREATE_ENV
    if [ "$CREATE_ENV" = "y" ]; then
        cp .env.example .env
        echo "✓ Created .env from .env.example"
        echo "⚠ Remember to update API keys and secrets in .env"
    fi
fi

echo ""
echo "Step 3: Checking database connection..."

# Check if DATABASE_URL is set
if grep -q "DATABASE_URL" .env 2>/dev/null; then
    echo "✓ DATABASE_URL configured"

    echo ""
    echo "Step 4: Running database migration..."
    echo ""
    read -p "Run composite index migration now? (y/n): " RUN_MIGRATION
    if [ "$RUN_MIGRATION" = "y" ]; then
        cd migrations
        python add_composite_indexes.py
        cd ..
        echo ""
        echo "✓ Migration completed"
    else
        echo "⚠ Skipped migration - run manually later with:"
        echo "   cd migrations && python add_composite_indexes.py"
    fi
else
    echo "⚠ DATABASE_URL not configured"
    echo "  Using SQLite - indexes will be created automatically"
fi

echo ""
echo "Step 5: Verifying setup..."
echo ""

# Test Redis connection
if command -v redis-cli &> /dev/null && redis-cli ping &> /dev/null; then
    echo "✓ Redis connection: OK"
else
    echo "⚠ Redis connection: NOT AVAILABLE"
    echo "  Application will work but without caching benefits"
fi

# Test Python imports
python -c "from app.services.redis_cache import get_redis_cache; cache = get_redis_cache(); print('✓ Redis cache service: OK' if cache else '✗ Redis cache service: ERROR')" 2>&1

echo ""
echo "========================================="
echo "Setup Summary"
echo "========================================="
echo ""
echo "Optimizations applied:"
echo "  ✓ Composite database indexes (via models.py)"
echo "  ✓ Redis caching service (via redis_cache.py)"
echo "  ✓ Optimized descriptor matching (via analytics_cache.py)"
echo "  ✓ Date range filtering (default: 180 days)"
echo ""
echo "Next steps:"
echo "  1. Restart your application server"
echo "  2. Monitor cache hit rate (should be 80-90%)"
echo "  3. Verify dashboard loads in <100ms"
echo "  4. Read docs/PERFORMANCE_OPTIMIZATIONS.md for details"
echo ""
echo "Monitoring commands:"
echo "  Redis status: redis-cli ping"
echo "  Cache stats: python -c 'from app.services.redis_cache import get_redis_cache; cache = get_redis_cache(); print(cache.redis_client.info(\"stats\") if cache.is_available else \"Redis not available\")'"
echo ""
echo "========================================="
echo "✓ Performance optimizations ready!"
echo "========================================="
