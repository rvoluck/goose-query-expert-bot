#!/bin/bash
# ================================
# Docker Deployment Script
# Builds and deploys the application using Docker Compose
# ================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${PROJECT_ROOT}/.env"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.yml"
COMPOSE_PROD_FILE="${PROJECT_ROOT}/docker-compose.prod.yml"

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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

check_env_file() {
    log_info "Checking environment file..."
    
    if [ ! -f "$ENV_FILE" ]; then
        log_warn ".env file not found. Creating from env.example..."
        
        if [ -f "${PROJECT_ROOT}/env.example" ]; then
            cp "${PROJECT_ROOT}/env.example" "$ENV_FILE"
            log_warn "Please update .env file with your actual configuration"
            log_error "Deployment cannot continue without proper configuration"
            exit 1
        else
            log_error "env.example file not found. Cannot create .env file."
            exit 1
        fi
    fi
    
    # Check for required variables
    required_vars=(
        "SLACK_BOT_TOKEN"
        "SLACK_APP_TOKEN"
        "SLACK_SIGNING_SECRET"
        "JWT_SECRET_KEY"
        "ENCRYPTION_KEY"
        "POSTGRES_PASSWORD"
        "REDIS_PASSWORD"
    )
    
    missing_vars=()
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE" || grep -q "^${var}=$" "$ENV_FILE"; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "Missing or empty required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        exit 1
    fi
    
    log_info "Environment file check passed"
}

build_images() {
    local environment=$1
    log_info "Building Docker images for $environment environment..."
    
    if [ "$environment" = "production" ]; then
        docker-compose -f "$COMPOSE_PROD_FILE" build --no-cache
    else
        docker-compose -f "$COMPOSE_FILE" build
    fi
    
    log_info "Docker images built successfully"
}

start_services() {
    local environment=$1
    log_info "Starting services for $environment environment..."
    
    if [ "$environment" = "production" ]; then
        docker-compose -f "$COMPOSE_PROD_FILE" up -d
    else
        docker-compose -f "$COMPOSE_FILE" up -d
    fi
    
    log_info "Services started successfully"
}

stop_services() {
    local environment=$1
    log_info "Stopping services for $environment environment..."
    
    if [ "$environment" = "production" ]; then
        docker-compose -f "$COMPOSE_PROD_FILE" down
    else
        docker-compose -f "$COMPOSE_FILE" down
    fi
    
    log_info "Services stopped successfully"
}

show_status() {
    local environment=$1
    log_info "Service status:"
    
    if [ "$environment" = "production" ]; then
        docker-compose -f "$COMPOSE_PROD_FILE" ps
    else
        docker-compose -f "$COMPOSE_FILE" ps
    fi
}

show_logs() {
    local environment=$1
    local service=$2
    
    if [ "$environment" = "production" ]; then
        if [ -n "$service" ]; then
            docker-compose -f "$COMPOSE_PROD_FILE" logs -f "$service"
        else
            docker-compose -f "$COMPOSE_PROD_FILE" logs -f
        fi
    else
        if [ -n "$service" ]; then
            docker-compose -f "$COMPOSE_FILE" logs -f "$service"
        else
            docker-compose -f "$COMPOSE_FILE" logs -f
        fi
    fi
}

run_health_check() {
    log_info "Running health checks..."
    
    # Wait for services to be ready
    sleep 10
    
    # Check app health
    if curl -f http://localhost:3000/health > /dev/null 2>&1; then
        log_info "✓ Application health check passed"
    else
        log_error "✗ Application health check failed"
        return 1
    fi
    
    # Check database
    if docker-compose exec -T postgres pg_isready -U goose_user > /dev/null 2>&1; then
        log_info "✓ Database health check passed"
    else
        log_error "✗ Database health check failed"
        return 1
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_info "✓ Redis health check passed"
    else
        log_error "✗ Redis health check failed"
        return 1
    fi
    
    log_info "All health checks passed"
    return 0
}

backup_database() {
    log_info "Creating database backup..."
    
    local backup_dir="${PROJECT_ROOT}/backups"
    mkdir -p "$backup_dir"
    
    local backup_file="${backup_dir}/backup_$(date +%Y%m%d_%H%M%S).sql"
    
    docker-compose exec -T postgres pg_dump -U goose_user goose_slackbot > "$backup_file"
    
    if [ -f "$backup_file" ]; then
        log_info "Database backup created: $backup_file"
    else
        log_error "Database backup failed"
        return 1
    fi
}

restore_database() {
    local backup_file=$1
    
    if [ ! -f "$backup_file" ]; then
        log_error "Backup file not found: $backup_file"
        return 1
    fi
    
    log_warn "This will restore the database from: $backup_file"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "Database restore cancelled"
        return 0
    fi
    
    log_info "Restoring database..."
    
    docker-compose exec -T postgres psql -U goose_user goose_slackbot < "$backup_file"
    
    log_info "Database restored successfully"
}

show_help() {
    cat << EOF
Docker Deployment Script for Goose Slackbot

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    deploy [env]        Deploy the application (env: dev|prod, default: dev)
    start [env]         Start services
    stop [env]          Stop services
    restart [env]       Restart services
    status [env]        Show service status
    logs [service]      Show logs (optionally for specific service)
    health              Run health checks
    backup              Create database backup
    restore [file]      Restore database from backup
    clean               Stop services and remove volumes
    help                Show this help message

Environment:
    dev                 Development environment (default)
    prod                Production environment

Examples:
    $0 deploy dev       Deploy in development mode
    $0 deploy prod      Deploy in production mode
    $0 logs app         Show application logs
    $0 backup           Create database backup
    $0 health           Run health checks

EOF
}

# Main script
main() {
    cd "$PROJECT_ROOT"
    
    local command=${1:-help}
    local environment=${2:-dev}
    
    case $command in
        deploy)
            check_prerequisites
            check_env_file
            log_info "Deploying in $environment mode..."
            build_images "$environment"
            start_services "$environment"
            run_health_check
            show_status "$environment"
            log_info "Deployment completed successfully!"
            log_info "Access the application at: http://localhost:3000"
            log_info "Access Grafana at: http://localhost:3001 (if monitoring enabled)"
            ;;
        
        start)
            check_prerequisites
            start_services "$environment"
            show_status "$environment"
            ;;
        
        stop)
            stop_services "$environment"
            ;;
        
        restart)
            stop_services "$environment"
            start_services "$environment"
            show_status "$environment"
            ;;
        
        status)
            show_status "$environment"
            ;;
        
        logs)
            show_logs "$environment" "$2"
            ;;
        
        health)
            run_health_check
            ;;
        
        backup)
            backup_database
            ;;
        
        restore)
            if [ -z "$2" ]; then
                log_error "Please specify backup file to restore"
                exit 1
            fi
            restore_database "$2"
            ;;
        
        clean)
            log_warn "This will stop all services and remove volumes"
            read -p "Are you sure? (yes/no): " confirm
            if [ "$confirm" = "yes" ]; then
                docker-compose -f "$COMPOSE_FILE" down -v
                docker-compose -f "$COMPOSE_PROD_FILE" down -v
                log_info "Cleanup completed"
            fi
            ;;
        
        help|*)
            show_help
            ;;
    esac
}

# Run main function
main "$@"
