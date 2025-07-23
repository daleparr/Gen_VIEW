# GEN-VIEW-KSE Test Suite

Comprehensive test suite for the GEN-VIEW-KSE AI-powered fashion generation platform, covering backend APIs, KSE memory integration, database operations, frontend components, and performance benchmarks.

## 📋 Table of Contents

- [Overview](#overview)
- [Test Structure](#test-structure)
- [Quick Start](#quick-start)
- [Test Categories](#test-categories)
- [Running Tests](#running-tests)
- [Configuration](#configuration)
- [Coverage Reports](#coverage-reports)
- [Performance Testing](#performance-testing)
- [Continuous Integration](#continuous-integration)
- [Troubleshooting](#troubleshooting)

## 🎯 Overview

The test suite provides comprehensive coverage for:

- **Backend API Testing**: FastAPI endpoints, WebSocket connections, error handling
- **KSE Memory Service Testing**: Temporal knowledge graphs, cross-modal embeddings, feedback loops
- **Database Testing**: SQLAlchemy models, relationships, complex queries, migrations
- **Frontend Testing**: React components, TypeScript interfaces, state management
- **Performance Testing**: Load testing, memory usage, response times, throughput
- **Integration Testing**: End-to-end workflows, service interactions

## 🏗️ Test Structure

```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── requirements.txt            # Test dependencies
├── test_api_routes.py         # API endpoint tests
├── test_kse_memory.py         # KSE Memory Service tests
├── test_database.py           # Database and model tests
├── test_frontend_components.py # Frontend component tests
├── test_performance.py        # Performance and load tests
└── __init__.py

scripts/
└── run_tests.sh              # Test runner script

pytest.ini                    # Pytest configuration
```

## 🚀 Quick Start

### Prerequisites

```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Ensure services are running (for integration tests)
docker-compose up -d postgres redis
```

### Basic Usage

```bash
# Run all unit tests
./scripts/run_tests.sh

# Run specific test category
./scripts/run_tests.sh -t unit
./scripts/run_tests.sh -t integration
./scripts/run_tests.sh -t performance

# Run with verbose output and coverage
./scripts/run_tests.sh -v -o html
```

## 📊 Test Categories

### Unit Tests (`@pytest.mark.unit`)

Test individual components in isolation:

- **API Routes**: Endpoint validation, request/response handling
- **Database Models**: Model creation, relationships, validation
- **KSE Memory**: Memory storage, retrieval, context processing
- **Services**: Business logic, data processing, transformations
- **Frontend Components**: Component props, state management, validation

```bash
# Run only unit tests
./scripts/run_tests.sh -t unit

# Run specific service tests
./scripts/run_tests.sh -m "unit and kse_memory"
```

### Integration Tests (`@pytest.mark.integration`)

Test component interactions and workflows:

- **End-to-End Workflows**: Complete generation processes
- **Database Integrations**: Cross-table operations, transactions
- **Service Communications**: API-to-service interactions
- **WebSocket Connections**: Real-time communication flows

```bash
# Run integration tests
./scripts/run_tests.sh -t integration -i

# Run with test services
docker-compose -f docker-compose.test.yml up -d
./scripts/run_tests.sh -t integration
```

### Performance Tests (`@pytest.mark.performance`)

Benchmark system performance and resource usage:

- **API Performance**: Response times, throughput, concurrent load
- **Database Performance**: Query optimization, bulk operations
- **Memory Usage**: Memory leaks, resource consumption
- **WebSocket Performance**: Message throughput, connection handling

```bash
# Run performance tests
./scripts/run_tests.sh -t performance -p

# Run with benchmarking
./scripts/run_tests.sh -m "performance" --benchmark-only
```

## 🔧 Running Tests

### Test Runner Script

The `run_tests.sh` script provides comprehensive test execution with multiple options:

```bash
Usage: ./scripts/run_tests.sh [OPTIONS]

OPTIONS:
    -t, --type TYPE         Test type: unit, integration, performance, all
    -v, --verbose          Enable verbose output
    -c, --no-coverage      Disable coverage reporting
    -s, --sequential       Run tests sequentially
    -p, --performance      Include performance tests
    -i, --integration      Include integration tests
    -f, --fail-fast        Stop on first failure
    -m, --markers MARKERS  Run tests with specific markers
    -o, --output FORMAT    Output format: terminal, html, json
    -h, --help             Show help message
```

### Examples

```bash
# Basic test run
./scripts/run_tests.sh

# Comprehensive test run with all categories
./scripts/run_tests.sh -i -p -v -o html

# Fast feedback loop
./scripts/run_tests.sh -t unit -f -s

# Specific component testing
./scripts/run_tests.sh -m "api and not slow"

# Performance benchmarking
./scripts/run_tests.sh -t performance --benchmark-sort=mean
```

### Direct Pytest Usage

```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=services --cov-report=html

# Run specific test file
python -m pytest tests/test_api_routes.py -v

# Run with markers
python -m pytest -m "unit and not slow" tests/

# Parallel execution
python -m pytest -n auto tests/
```

## ⚙️ Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[tool:pytest]
markers =
    unit: Unit tests for individual components
    integration: Integration tests across components
    performance: Performance and load tests
    slow: Tests that take a long time to run
    asyncio: Tests that use asyncio
    database: Tests that require database access
    redis: Tests that require Redis access
    websocket: Tests involving WebSocket connections
    frontend: Tests for frontend components
    kse_memory: Tests for KSE Memory Service
    multimodal: Tests for multi-modal processing
    api: Tests for API endpoints
    models: Tests for database models
    services: Tests for service layer components

asyncio_mode = auto
timeout = 300
```

### Environment Variables

Test environment configuration:

```bash
export ENVIRONMENT=test
export DATABASE_URL="sqlite+aiosqlite:///./test.db"
export REDIS_URL="redis://localhost:6379/1"
export SECRET_KEY="test_secret_key_for_testing_only"
export LOG_LEVEL="DEBUG"
```

### Test Fixtures

Key fixtures available in `conftest.py`:

- `test_client`: FastAPI test client
- `test_db_session`: Database session for testing
- `mock_kse_memory_service`: KSE Memory Service mock
- `mock_multimodal_processor`: Multi-modal processor mock
- `sample_brand_data`: Test brand data
- `sample_generation_request`: Test generation request
- `performance_test_config`: Performance test configuration

## 📈 Coverage Reports

### HTML Coverage Report

```bash
# Generate HTML coverage report
./scripts/run_tests.sh -o html

# View report
open htmlcov/index.html
```

### Terminal Coverage Report

```bash
# Show coverage in terminal
./scripts/run_tests.sh -v

# Coverage summary
python -m pytest --cov=services --cov-report=term-missing tests/
```

### Coverage Targets

- **Minimum Coverage**: 80%
- **Target Coverage**: 90%
- **Critical Components**: 95%

### Coverage Exclusions

```python
# pragma: no cover - exclude from coverage
def debug_only_function():  # pragma: no cover
    pass
```

## ⚡ Performance Testing

### Performance Metrics

The performance test suite measures:

- **Response Times**: API endpoint latency
- **Throughput**: Requests per second
- **Memory Usage**: RAM consumption and leaks
- **CPU Usage**: Processing efficiency
- **Database Performance**: Query execution times
- **WebSocket Performance**: Message throughput

### Performance Benchmarks

```bash
# Run performance tests with benchmarking
./scripts/run_tests.sh -t performance --benchmark-only

# Performance report
python -m pytest tests/test_performance.py --benchmark-sort=mean --benchmark-save=baseline
```

### Performance Thresholds

- **API Response Time**: < 2.0 seconds (95th percentile)
- **Database Queries**: < 100ms (average)
- **Memory Usage**: < 512MB increase
- **CPU Usage**: < 80% peak
- **WebSocket Throughput**: > 1000 messages/second

## 🔄 Continuous Integration

### GitHub Actions Integration

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r tests/requirements.txt
      - name: Run tests
        run: |
          ./scripts/run_tests.sh -i -c -o json
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: tests
        name: Run tests
        entry: ./scripts/run_tests.sh -t unit -f
        language: system
        pass_filenames: false
```

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Errors

```bash
# Reset test database
rm test.db
./scripts/run_tests.sh -t database

# Check database migrations
alembic upgrade head
```

#### Redis Connection Errors

```bash
# Start Redis for testing
docker run -d -p 6379:6379 redis:alpine

# Use alternative Redis URL
export REDIS_URL="redis://localhost:6379/1"
```

#### Memory Issues in Performance Tests

```bash
# Run with memory profiling
python -m memory_profiler tests/test_performance.py

# Reduce test load
./scripts/run_tests.sh -m "performance and not slow"
```

#### Async Test Failures

```bash
# Run with asyncio debug mode
export PYTHONASYNCIODEBUG=1
./scripts/run_tests.sh -m "asyncio" -v
```

### Debug Mode

```bash
# Run with debugging
./scripts/run_tests.sh -v --pdb

# Run specific failing test
python -m pytest tests/test_api_routes.py::TestGenerationRoutes::test_capsule_collection_generation_valid -v --pdb
```

### Test Data Cleanup

```bash
# Clean test artifacts
rm -rf htmlcov/ test-reports/ test.db
find . -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
```

## 📝 Writing New Tests

### Test Structure

```python
import pytest
from unittest.mock import Mock, patch

class TestNewFeature:
    """Test suite for new feature."""
    
    @pytest.mark.unit
    def test_basic_functionality(self):
        """Test basic functionality."""
        # Test implementation
        pass
    
    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality."""
        # Async test implementation
        pass
    
    @pytest.mark.integration
    def test_integration_scenario(self, test_client):
        """Test integration scenario."""
        # Integration test implementation
        pass
```

### Best Practices

1. **Descriptive Names**: Use clear, descriptive test names
2. **Single Responsibility**: Each test should test one thing
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mock External Dependencies**: Use mocks for external services
5. **Test Edge Cases**: Include boundary conditions and error cases
6. **Performance Considerations**: Mark slow tests appropriately

### Test Markers

```python
@pytest.mark.unit           # Unit test
@pytest.mark.integration    # Integration test
@pytest.mark.performance    # Performance test
@pytest.mark.slow           # Slow-running test
@pytest.mark.asyncio        # Async test
@pytest.mark.database       # Requires database
@pytest.mark.redis          # Requires Redis
@pytest.mark.websocket      # WebSocket test
```

## 🎯 Test Metrics and Reporting

### Key Metrics

- **Test Count**: Total number of tests
- **Coverage Percentage**: Code coverage metrics
- **Pass Rate**: Percentage of passing tests
- **Execution Time**: Total test execution time
- **Performance Benchmarks**: Response times and throughput

### Reporting

- **HTML Reports**: Detailed test results with coverage
- **JSON Reports**: Machine-readable test data
- **Performance Reports**: Benchmark results and trends
- **Coverage Reports**: Line-by-line coverage analysis

## 🤝 Contributing

When contributing new features:

1. **Write Tests First**: Follow TDD principles
2. **Maintain Coverage**: Ensure new code is tested
3. **Update Documentation**: Keep test docs current
4. **Run Full Suite**: Verify all tests pass
5. **Performance Impact**: Consider performance implications

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/14/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
- [AsyncIO Testing](https://docs.python.org/3/library/asyncio-dev.html#testing)
- [Performance Testing Best Practices](https://martinfowler.com/articles/practical-test-pyramid.html)

---

**GEN-VIEW-KSE Test Suite** - Ensuring quality and reliability for AI-powered fashion generation platform.