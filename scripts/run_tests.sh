#!/bin/bash

# GEN-VIEW-KSE Test Runner Script
# Comprehensive test execution with multiple modes and configurations

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_DIR="$PROJECT_ROOT/tests"
COVERAGE_DIR="$PROJECT_ROOT/htmlcov"
REPORTS_DIR="$PROJECT_ROOT/test-reports"

# Default values
TEST_TYPE="all"
VERBOSE=false
COVERAGE=true
PARALLEL=true
PERFORMANCE=false
INTEGRATION=false
FAIL_FAST=false
MARKERS=""
OUTPUT_FORMAT="terminal"

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show usage
show_usage() {
    cat << EOF
GEN-VIEW-KSE Test Runner

Usage: $0 [OPTIONS]

OPTIONS:
    -t, --type TYPE         Test type: unit, integration, performance, all (default: all)
    -v, --verbose          Enable verbose output
    -c, --no-coverage      Disable coverage reporting
    -s, --sequential       Run tests sequentially (disable parallel execution)
    -p, --performance      Include performance tests
    -i, --integration      Include integration tests
    -f, --fail-fast        Stop on first failure
    -m, --markers MARKERS  Run tests with specific markers
    -o, --output FORMAT    Output format: terminal, html, json (default: terminal)
    -h, --help             Show this help message

EXAMPLES:
    $0                              # Run all unit tests with coverage
    $0 -t unit -v                   # Run unit tests with verbose output
    $0 -t integration -p            # Run integration and performance tests
    $0 -m "api and not slow"        # Run API tests excluding slow ones
    $0 -o html                      # Generate HTML test report
    $0 -f -s                        # Run sequentially and fail fast

TEST MARKERS:
    unit, integration, performance, slow, asyncio, database, redis,
    websocket, frontend, kse_memory, multimodal, api, models, services
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            TEST_TYPE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -c|--no-coverage)
            COVERAGE=false
            shift
            ;;
        -s|--sequential)
            PARALLEL=false
            shift
            ;;
        -p|--performance)
            PERFORMANCE=true
            shift
            ;;
        -i|--integration)
            INTEGRATION=true
            shift
            ;;
        -f|--fail-fast)
            FAIL_FAST=true
            shift
            ;;
        -m|--markers)
            MARKERS="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Setup test environment
setup_test_environment() {
    print_status $BLUE "Setting up test environment..."
    
    # Create reports directory
    mkdir -p "$REPORTS_DIR"
    
    # Check if virtual environment is activated
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_status $YELLOW "Warning: No virtual environment detected. Consider activating one."
    fi
    
    # Install test dependencies if needed
    if ! python -c "import pytest" 2>/dev/null; then
        print_status $YELLOW "Installing test dependencies..."
        pip install -r "$PROJECT_ROOT/tests/requirements.txt"
    fi
    
    # Set environment variables for testing
    export ENVIRONMENT=test
    export DATABASE_URL="sqlite+aiosqlite:///./test.db"
    export REDIS_URL="redis://localhost:6379/1"
    export SECRET_KEY="test_secret_key_for_testing_only"
    export LOG_LEVEL="DEBUG"
}

# Build pytest command
build_pytest_command() {
    local cmd="python -m pytest"
    
    # Add test directory
    cmd="$cmd $TEST_DIR"
    
    # Add verbose flag
    if [[ "$VERBOSE" == true ]]; then
        cmd="$cmd -v"
    fi
    
    # Add coverage options
    if [[ "$COVERAGE" == true ]]; then
        cmd="$cmd --cov=services --cov=demos"
        cmd="$cmd --cov-report=html:$COVERAGE_DIR"
        cmd="$cmd --cov-report=term-missing"
        cmd="$cmd --cov-fail-under=80"
    fi
    
    # Add parallel execution
    if [[ "$PARALLEL" == true ]]; then
        local cpu_count=$(python -c "import os; print(os.cpu_count())")
        cmd="$cmd -n $cpu_count"
    fi
    
    # Add fail fast option
    if [[ "$FAIL_FAST" == true ]]; then
        cmd="$cmd -x"
    fi
    
    # Add output format options
    case $OUTPUT_FORMAT in
        html)
            cmd="$cmd --html=$REPORTS_DIR/report.html --self-contained-html"
            ;;
        json)
            cmd="$cmd --json-report --json-report-file=$REPORTS_DIR/report.json"
            ;;
    esac
    
    # Add test type markers
    local test_markers=""
    case $TEST_TYPE in
        unit)
            test_markers="unit and not integration and not performance"
            ;;
        integration)
            test_markers="integration"
            if [[ "$PERFORMANCE" == true ]]; then
                test_markers="$test_markers or performance"
            fi
            ;;
        performance)
            test_markers="performance"
            ;;
        all)
            test_markers="not performance"
            if [[ "$PERFORMANCE" == true ]]; then
                test_markers=""
            fi
            if [[ "$INTEGRATION" == false ]]; then
                if [[ -z "$test_markers" ]]; then
                    test_markers="not integration"
                else
                    test_markers="$test_markers and not integration"
                fi
            fi
            ;;
    esac
    
    # Add custom markers
    if [[ -n "$MARKERS" ]]; then
        if [[ -n "$test_markers" ]]; then
            test_markers="($test_markers) and ($MARKERS)"
        else
            test_markers="$MARKERS"
        fi
    fi
    
    # Add markers to command
    if [[ -n "$test_markers" ]]; then
        cmd="$cmd -m \"$test_markers\""
    fi
    
    echo "$cmd"
}

# Run specific test suites
run_unit_tests() {
    print_status $BLUE "Running unit tests..."
    
    local cmd=$(build_pytest_command)
    cmd="$cmd -m \"unit and not slow\""
    
    print_status $YELLOW "Command: $cmd"
    eval $cmd
}

run_integration_tests() {
    print_status $BLUE "Running integration tests..."
    
    # Start required services for integration tests
    print_status $YELLOW "Starting test services..."
    
    # Check if Docker is available for service dependencies
    if command -v docker &> /dev/null; then
        # Start test database and Redis if needed
        docker-compose -f docker-compose.test.yml up -d postgres redis || true
        sleep 5
    fi
    
    local cmd=$(build_pytest_command)
    cmd="$cmd -m \"integration\""
    
    print_status $YELLOW "Command: $cmd"
    eval $cmd
    
    # Cleanup services
    if command -v docker &> /dev/null; then
        docker-compose -f docker-compose.test.yml down || true
    fi
}

run_performance_tests() {
    print_status $BLUE "Running performance tests..."
    
    local cmd=$(build_pytest_command)
    cmd="$cmd -m \"performance\" --benchmark-only --benchmark-sort=mean"
    
    print_status $YELLOW "Command: $cmd"
    eval $cmd
}

run_api_tests() {
    print_status $BLUE "Running API tests..."
    
    local cmd=$(build_pytest_command)
    cmd="$cmd -m \"api\""
    
    print_status $YELLOW "Command: $cmd"
    eval $cmd
}

run_database_tests() {
    print_status $BLUE "Running database tests..."
    
    local cmd=$(build_pytest_command)
    cmd="$cmd -m \"database or models\""
    
    print_status $YELLOW "Command: $cmd"
    eval $cmd
}

run_kse_memory_tests() {
    print_status $BLUE "Running KSE Memory Service tests..."
    
    local cmd=$(build_pytest_command)
    cmd="$cmd -m \"kse_memory or multimodal\""
    
    print_status $YELLOW "Command: $cmd"
    eval $cmd
}

run_frontend_tests() {
    print_status $BLUE "Running frontend tests..."
    
    local cmd=$(build_pytest_command)
    cmd="$cmd -m \"frontend\""
    
    print_status $YELLOW "Command: $cmd"
    eval $cmd
}

# Generate test reports
generate_reports() {
    print_status $BLUE "Generating test reports..."
    
    # Coverage report
    if [[ "$COVERAGE" == true ]] && [[ -d "$COVERAGE_DIR" ]]; then
        print_status $GREEN "Coverage report generated: $COVERAGE_DIR/index.html"
    fi
    
    # Test report
    if [[ -f "$REPORTS_DIR/report.html" ]]; then
        print_status $GREEN "HTML test report generated: $REPORTS_DIR/report.html"
    fi
    
    if [[ -f "$REPORTS_DIR/report.json" ]]; then
        print_status $GREEN "JSON test report generated: $REPORTS_DIR/report.json"
    fi
}

# Main execution
main() {
    print_status $GREEN "GEN-VIEW-KSE Test Runner"
    print_status $BLUE "Test type: $TEST_TYPE"
    print_status $BLUE "Verbose: $VERBOSE"
    print_status $BLUE "Coverage: $COVERAGE"
    print_status $BLUE "Parallel: $PARALLEL"
    print_status $BLUE "Performance: $PERFORMANCE"
    print_status $BLUE "Integration: $INTEGRATION"
    
    setup_test_environment
    
    local start_time=$(date +%s)
    local exit_code=0
    
    case $TEST_TYPE in
        unit)
            run_unit_tests || exit_code=$?
            ;;
        integration)
            run_integration_tests || exit_code=$?
            ;;
        performance)
            run_performance_tests || exit_code=$?
            ;;
        api)
            run_api_tests || exit_code=$?
            ;;
        database)
            run_database_tests || exit_code=$?
            ;;
        kse_memory)
            run_kse_memory_tests || exit_code=$?
            ;;
        frontend)
            run_frontend_tests || exit_code=$?
            ;;
        all)
            # Run unit tests first
            run_unit_tests || exit_code=$?
            
            # Run integration tests if requested
            if [[ "$INTEGRATION" == true ]] && [[ $exit_code -eq 0 ]]; then
                run_integration_tests || exit_code=$?
            fi
            
            # Run performance tests if requested
            if [[ "$PERFORMANCE" == true ]] && [[ $exit_code -eq 0 ]]; then
                run_performance_tests || exit_code=$?
            fi
            ;;
        *)
            # Custom marker-based execution
            local cmd=$(build_pytest_command)
            print_status $YELLOW "Command: $cmd"
            eval $cmd || exit_code=$?
            ;;
    esac
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    generate_reports
    
    if [[ $exit_code -eq 0 ]]; then
        print_status $GREEN "✅ All tests passed! (Duration: ${duration}s)"
    else
        print_status $RED "❌ Some tests failed! (Duration: ${duration}s)"
    fi
    
    return $exit_code
}

# Run main function
main "$@"