#!/bin/bash

# GEN-VIEW-KSE Monitoring Stack Startup Script
# This script starts the complete monitoring and observability stack

set -e

echo "🚀 Starting GEN-VIEW-KSE Monitoring Stack..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create monitoring directories if they don't exist
print_status "Creating monitoring directories..."
mkdir -p monitoring/prometheus/rules
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources
mkdir -p monitoring/alertmanager

# Start the monitoring stack
print_status "Starting monitoring services..."
docker-compose --profile monitoring up -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 10

# Check service health
services=(
    "prometheus:9090"
    "grafana:3000"
    "alertmanager:9093"
    "jaeger:16686"
    "redis-exporter:9121"
    "postgres-exporter:9187"
    "node-exporter:9100"
    "cadvisor:8081"
)

print_status "Checking service health..."
for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if curl -s http://localhost:$port > /dev/null 2>&1; then
        print_success "$name is running on port $port"
    else
        print_warning "$name may not be ready yet on port $port"
    fi
done

# Display access information
echo ""
echo "🎯 Monitoring Stack Access Information:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}📊 Grafana Dashboard:${NC}     http://localhost:3000"
echo -e "   ${YELLOW}Username:${NC} admin"
echo -e "   ${YELLOW}Password:${NC} admin123"
echo ""
echo -e "${GREEN}📈 Prometheus:${NC}            http://localhost:9090"
echo -e "${GREEN}🚨 Alertmanager:${NC}          http://localhost:9093"
echo -e "${GREEN}🔍 Jaeger Tracing:${NC}        http://localhost:16686"
echo ""
echo -e "${GREEN}📊 Exporters:${NC}"
echo -e "   Redis Exporter:      http://localhost:9121/metrics"
echo -e "   Postgres Exporter:   http://localhost:9187/metrics"
echo -e "   Node Exporter:       http://localhost:9100/metrics"
echo -e "   cAdvisor:           http://localhost:8081"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start backend services if not already running
if ! docker-compose ps | grep -q "generation-api.*Up"; then
    print_status "Backend services not running. Starting backend services..."
    docker-compose up -d
    print_success "Backend services started"
else
    print_success "Backend services are already running"
fi

echo ""
echo "🎉 Monitoring stack is ready!"
echo ""
echo "📋 Next Steps:"
echo "1. Open Grafana at http://localhost:3000 and explore the dashboards"
echo "2. Check Prometheus targets at http://localhost:9090/targets"
echo "3. View distributed traces in Jaeger at http://localhost:16686"
echo "4. Monitor alerts in Alertmanager at http://localhost:9093"
echo ""
echo "🛠️  To stop the monitoring stack, run:"
echo "   docker-compose --profile monitoring down"
echo ""
echo "📖 For troubleshooting, check logs with:"
echo "   docker-compose --profile monitoring logs -f [service-name]"