#!/bin/bash
# ================================
# Environment Setup Script
# Sets up the development/production environment
# ================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_ROOT}/.env"
ENV_EXAMPLE="${PROJECT_ROOT}/env.example"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

generate_secret() {
    local length=${1:-32}
    openssl rand -base64 "$length" | tr -d "=+/" | cut -c1-"$length"
}

create_env_file() {
    log_step "Creating .env file..."
    
    if [ -f "$ENV_FILE" ]; then
        log_warn ".env file already exists"
        read -p "Do you want to overwrite it? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            log_info "Keeping existing .env file"
            return 0
        fi
        
        # Backup existing file
        cp "$ENV_FILE" "${ENV_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
        log_info "Backed up existing .env file"
    fi
    
    if [ ! -f "$ENV_EXAMPLE" ]; then
        log_error "env.example file not found"
        exit 1
    fi
    
    # Copy example file
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    
    # Generate secrets
    log_info "Generating secure secrets..."
    
    local jwt_secret=$(generate_secret 64)
    local encryption_key=$(generate_secret 32)
    local postgres_password=$(generate_secret 32)
    local redis_password=$(generate_secret 32)
    
    # Update secrets in .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=${jwt_secret}|" "$ENV_FILE"
        sed -i '' "s|ENCRYPTION_KEY=.*|ENCRYPTION_KEY=${encryption_key}|" "$ENV_FILE"
        sed -i '' "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${postgres_password}|" "$ENV_FILE"
        sed -i '' "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=${redis_password}|" "$ENV_FILE"
    else
        # Linux
        sed -i "s|JWT_SECRET_KEY=.*|JWT_SECRET_KEY=${jwt_secret}|" "$ENV_FILE"
        sed -i "s|ENCRYPTION_KEY=.*|ENCRYPTION_KEY=${encryption_key}|" "$ENV_FILE"
        sed -i "s|POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${postgres_password}|" "$ENV_FILE"
        sed -i "s|REDIS_PASSWORD=.*|REDIS_PASSWORD=${redis_password}|" "$ENV_FILE"
    fi
    
    log_info ".env file created with generated secrets"
    log_warn "Please update the following variables in .env:"
    echo "  - SLACK_BOT_TOKEN"
    echo "  - SLACK_APP_TOKEN"
    echo "  - SLACK_SIGNING_SECRET"
    echo "  - SNOWFLAKE_ACCOUNT (if using Snowflake)"
}

setup_python_env() {
    log_step "Setting up Python environment..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi
    
    local python_version=$(python3 --version | cut -d' ' -f2)
    log_info "Python version: $python_version"
    
    # Create virtual environment
    if [ ! -d "${PROJECT_ROOT}/venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv "${PROJECT_ROOT}/venv"
    else
        log_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "${PROJECT_ROOT}/venv/bin/activate"
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel
    
    # Install dependencies
    log_info "Installing dependencies..."
    pip install -r "${PROJECT_ROOT}/requirements.txt"
    pip install -r "${PROJECT_ROOT}/requirements-db.txt"
    
    log_info "Python environment setup complete"
}

setup_database() {
    log_step "Setting up database..."
    
    # Check if PostgreSQL is running
    if ! command -v psql &> /dev/null; then
        log_warn "PostgreSQL client not found. Skipping database setup."
        log_warn "Please ensure PostgreSQL is installed and running."
        return 0
    fi
    
    # Source .env file
    if [ -f "$ENV_FILE" ]; then
        set -a
        source "$ENV_FILE"
        set +a
    fi
    
    # Check if database exists
    if psql -lqt | cut -d \| -f 1 | grep -qw goose_slackbot; then
        log_info "Database already exists"
    else
        log_info "Creating database..."
        createdb goose_slackbot
    fi
    
    # Run migrations
    log_info "Running database migrations..."
    python "${PROJECT_ROOT}/migrations.py" upgrade
    
    log_info "Database setup complete"
}

setup_directories() {
    log_step "Setting up directories..."
    
    local dirs=(
        "${PROJECT_ROOT}/logs"
        "${PROJECT_ROOT}/data"
        "${PROJECT_ROOT}/backups"
        "${PROJECT_ROOT}/data/postgres"
        "${PROJECT_ROOT}/data/redis"
        "${PROJECT_ROOT}/data/app"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
    done
    
    log_info "Directories setup complete"
}

setup_git_hooks() {
    log_step "Setting up Git hooks..."
    
    local hooks_dir="${PROJECT_ROOT}/.git/hooks"
    
    if [ ! -d "$hooks_dir" ]; then
        log_warn "Git repository not initialized. Skipping Git hooks setup."
        return 0
    fi
    
    # Pre-commit hook
    cat > "${hooks_dir}/pre-commit" << 'EOF'
#!/bin/bash
# Pre-commit hook for code quality checks

echo "Running pre-commit checks..."

# Run black formatter
if command -v black &> /dev/null; then
    black --check . || {
        echo "Code formatting issues found. Run 'black .' to fix."
        exit 1
    }
fi

# Run flake8 linter
if command -v flake8 &> /dev/null; then
    flake8 . || {
        echo "Linting issues found. Please fix before committing."
        exit 1
    }
fi

# Run tests
if command -v pytest &> /dev/null; then
    pytest tests/ || {
        echo "Tests failed. Please fix before committing."
        exit 1
    }
fi

echo "Pre-commit checks passed!"
EOF
    
    chmod +x "${hooks_dir}/pre-commit"
    log_info "Git hooks setup complete"
}

check_docker() {
    log_step "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        log_warn "Docker is not installed"
        log_info "Please install Docker from: https://docs.docker.com/get-docker/"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        log_warn "Docker daemon is not running"
        log_info "Please start Docker"
        return 1
    fi
    
    log_info "Docker is installed and running"
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_warn "Docker Compose is not installed"
        log_info "Please install Docker Compose from: https://docs.docker.com/compose/install/"
        return 1
    fi
    
    log_info "Docker Compose is installed"
    return 0
}

run_tests() {
    log_step "Running tests..."
    
    # Activate virtual environment
    if [ -d "${PROJECT_ROOT}/venv" ]; then
        source "${PROJECT_ROOT}/venv/bin/activate"
    fi
    
    # Run pytest
    if command -v pytest &> /dev/null; then
        pytest "${PROJECT_ROOT}/tests/" -v
        log_info "Tests completed"
    else
        log_warn "pytest not found. Skipping tests."
    fi
}

show_summary() {
    echo ""
    echo "================================"
    log_info "Environment setup complete!"
    echo "================================"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Update .env file with your Slack credentials:"
    echo "   - SLACK_BOT_TOKEN"
    echo "   - SLACK_APP_TOKEN"
    echo "   - SLACK_SIGNING_SECRET"
    echo ""
    echo "2. Start the application:"
    echo "   Development: ./scripts/deploy-docker.sh deploy dev"
    echo "   Production:  ./scripts/deploy-docker.sh deploy prod"
    echo ""
    echo "3. Access the application:"
    echo "   - Application: http://localhost:3000"
    echo "   - Health check: http://localhost:3000/health"
    echo "   - Metrics: http://localhost:9090"
    echo ""
    echo "For more information, see:"
    echo "   - README.md"
    echo "   - SETUP.md"
    echo "   - ADMIN_GUIDE.md"
    echo ""
}

show_help() {
    cat << EOF
Environment Setup Script for Goose Slackbot

Usage: $0 [COMMAND]

Commands:
    all             Run all setup steps (default)
    env             Create .env file with generated secrets
    python          Setup Python virtual environment
    database        Setup database
    directories     Create necessary directories
    git-hooks       Setup Git hooks
    docker          Check Docker installation
    test            Run tests
    help            Show this help message

Examples:
    $0              Run all setup steps
    $0 env          Create .env file only
    $0 python       Setup Python environment only

EOF
}

# Main script
main() {
    cd "$PROJECT_ROOT"
    
    local command=${1:-all}
    
    case $command in
        all)
            log_info "Running full environment setup..."
            create_env_file
            setup_directories
            check_docker
            setup_python_env
            setup_git_hooks
            show_summary
            ;;
        
        env)
            create_env_file
            ;;
        
        python)
            setup_python_env
            ;;
        
        database)
            setup_database
            ;;
        
        directories)
            setup_directories
            ;;
        
        git-hooks)
            setup_git_hooks
            ;;
        
        docker)
            check_docker
            ;;
        
        test)
            run_tests
            ;;
        
        help|*)
            show_help
            ;;
    esac
}

# Run main function
main "$@"
