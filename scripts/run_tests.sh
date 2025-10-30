#!/bin/bash
# Test runner script for Goose Slackbot
# Runs unit tests, integration tests, and generates coverage reports

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Goose Slackbot Test Runner${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Parse arguments
TEST_TYPE="${1:-all}"
COVERAGE="${2:-true}"

# Activate virtual environment if it exists
if [ -d "$PROJECT_DIR/venv" ]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source "$PROJECT_DIR/venv/bin/activate"
fi

# Install test dependencies
echo -e "${YELLOW}Installing test dependencies...${NC}"
pip install -q -r "$PROJECT_DIR/tests/requirements.txt"

# Set test environment variables
export ENVIRONMENT=test
export DATABASE_URL="${TEST_DATABASE_URL:-postgresql://localhost/goose_slackbot_test}"
export REDIS_URL="${TEST_REDIS_URL:-redis://localhost:6379/15}"
export SLACK_BOT_TOKEN="${TEST_SLACK_BOT_TOKEN:-xoxb-test-token}"
export SLACK_APP_TOKEN="${TEST_SLACK_APP_TOKEN:-xapp-test-token}"
export SLACK_SIGNING_SECRET="${TEST_SLACK_SIGNING_SECRET:-test-secret}"
export JWT_SECRET_KEY="${TEST_JWT_SECRET_KEY:-test-jwt-secret}"
export ENCRYPTION_KEY="${TEST_ENCRYPTION_KEY:-test-encryption-key}"
export MOCK_MODE=true

cd "$PROJECT_DIR"

# Function to run unit tests
run_unit_tests() {
    echo -e "${GREEN}Running unit tests...${NC}"
    
    if [ "$COVERAGE" = "true" ]; then
        pytest tests/unit/ \
            --cov=. \
            --cov-report=html:htmlcov/unit \
            --cov-report=term \
            --cov-report=xml:coverage-unit.xml \
            -v \
            --tb=short \
            --maxfail=5
    else
        pytest tests/unit/ -v --tb=short --maxfail=5
    fi
}

# Function to run integration tests
run_integration_tests() {
    echo -e "${GREEN}Running integration tests...${NC}"
    
    if [ "$COVERAGE" = "true" ]; then
        pytest tests/integration/ \
            --cov=. \
            --cov-report=html:htmlcov/integration \
            --cov-report=term \
            --cov-report=xml:coverage-integration.xml \
            -v \
            --tb=short \
            --maxfail=3
    else
        pytest tests/integration/ -v --tb=short --maxfail=3
    fi
}

# Function to run load tests
run_load_tests() {
    echo -e "${GREEN}Running load tests...${NC}"
    
    # Check if service is running
    if ! curl -s http://localhost:3000/health > /dev/null; then
        echo -e "${RED}Error: Service not running on localhost:3000${NC}"
        echo -e "${YELLOW}Start the service before running load tests${NC}"
        exit 1
    fi
    
    pytest tests/load/ -v --tb=short
}

# Function to run all tests
run_all_tests() {
    echo -e "${GREEN}Running all tests...${NC}"
    
    if [ "$COVERAGE" = "true" ]; then
        pytest tests/ \
            --ignore=tests/load/ \
            --cov=. \
            --cov-report=html:htmlcov \
            --cov-report=term \
            --cov-report=xml:coverage.xml \
            -v \
            --tb=short \
            --maxfail=10
    else
        pytest tests/ --ignore=tests/load/ -v --tb=short --maxfail=10
    fi
}

# Function to run tests in parallel
run_parallel_tests() {
    echo -e "${GREEN}Running tests in parallel...${NC}"
    
    pytest tests/ \
        --ignore=tests/load/ \
        -n auto \
        --dist=loadscope \
        -v
}

# Function to run specific test file
run_specific_test() {
    local test_file="$1"
    echo -e "${GREEN}Running test file: $test_file${NC}"
    
    pytest "$test_file" -v --tb=short
}

# Function to generate coverage report
generate_coverage_report() {
    echo -e "${GREEN}Generating coverage report...${NC}"
    
    coverage html
    coverage report
    
    echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
}

# Function to run linting
run_linting() {
    echo -e "${GREEN}Running code quality checks...${NC}"
    
    echo -e "${YELLOW}Running black...${NC}"
    black --check . || true
    
    echo -e "${YELLOW}Running flake8...${NC}"
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
    
    echo -e "${YELLOW}Running pylint...${NC}"
    pylint *.py --errors-only || true
    
    echo -e "${YELLOW}Running mypy...${NC}"
    mypy . --ignore-missing-imports || true
}

# Main execution
case "$TEST_TYPE" in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    load)
        run_load_tests
        ;;
    all)
        run_all_tests
        ;;
    parallel)
        run_parallel_tests
        ;;
    lint)
        run_linting
        ;;
    coverage)
        run_all_tests
        generate_coverage_report
        ;;
    *)
        if [ -f "$TEST_TYPE" ]; then
            run_specific_test "$TEST_TYPE"
        else
            echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
            echo ""
            echo "Usage: $0 [test_type] [coverage]"
            echo ""
            echo "Test types:"
            echo "  unit         - Run unit tests only"
            echo "  integration  - Run integration tests only"
            echo "  load         - Run load tests only"
            echo "  all          - Run all tests (default)"
            echo "  parallel     - Run tests in parallel"
            echo "  lint         - Run code quality checks"
            echo "  coverage     - Run tests and generate coverage report"
            echo "  <file>       - Run specific test file"
            echo ""
            echo "Coverage: true|false (default: true)"
            exit 1
        fi
        ;;
esac

# Check test results
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo -e "${GREEN}========================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}✗ Some tests failed${NC}"
    echo -e "${RED}========================================${NC}"
    exit 1
fi
