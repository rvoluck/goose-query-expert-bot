#!/bin/bash
set -euo pipefail

# Goose Slackbot Production Deployment Script
# This script handles building, testing, and deploying the application

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-}"
IMAGE_NAME="${IMAGE_NAME:-goose-slackbot}"
VERSION="${VERSION:-$(git rev-parse --short HEAD)}"
ENVIRONMENT="${ENVIRONMENT:-production}"
NAMESPACE="${NAMESPACE:-goose-slackbot}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handling
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log_error "Deployment failed with exit code $exit_code"
    fi
    exit $exit_code
}

trap cleanup EXIT

# Help function
show_help() {
    cat << EOF
Goose Slackbot Deployment Script

Usage: $0 [OPTIONS] COMMAND

COMMANDS:
    build           Build Docker images
    test            Run tests
    push            Push images to registry
    deploy          Deploy to Kubernetes
    rollback        Rollback to previous version
    status          Check deployment status
    logs            Show application logs
    cleanup         Clean up old resources

OPTIONS:
    -e, --environment ENV    Target environment (default: production)
    -v, --version VERSION    Image version/tag (default: git commit hash)
    -r, --registry REGISTRY  Docker registry URL
    -n, --namespace NS       Kubernetes namespace (default: goose-slackbot)
    --dry-run               Show what would be done without executing
    --skip-tests            Skip running tests
    --force                 Force deployment even if checks fail
    -h, --help              Show this help message

EXAMPLES:
    $0 build                                    # Build images
    $0 -e staging deploy                        # Deploy to staging
    $0 -v v1.2.3 --registry myregistry.com push # Push specific version
    $0 rollback                                 # Rollback deployment
    $0 status                                   # Check deployment status

ENVIRONMENT VARIABLES:
    DOCKER_REGISTRY         Docker registry URL
    IMAGE_NAME             Docker image name (default: goose-slackbot)
    VERSION                Image version/tag
    ENVIRONMENT            Target environment
    NAMESPACE              Kubernetes namespace
    KUBECONFIG             Kubernetes config file path

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -v|--version)
                VERSION="$2"
                shift 2
                ;;
            -r|--registry)
                DOCKER_REGISTRY="$2"
                shift 2
                ;;
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --force)
                FORCE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            -*)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                COMMAND="$1"
                shift
                ;;
        esac
    done
}

# Validation functions
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check required tools
    local required_tools=("docker" "kubectl" "git")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is required but not installed"
            exit 1
        fi
    done
    
    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    # Check Kubernetes connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace '$NAMESPACE' does not exist, will create it"
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build production image
    local full_image_name="${IMAGE_NAME}:${VERSION}"
    if [ -n "$DOCKER_REGISTRY" ]; then
        full_image_name="${DOCKER_REGISTRY}/${full_image_name}"
    fi
    
    log_info "Building image: $full_image_name"
    
    if [ "${DRY_RUN:-false}" = "true" ]; then
        log_info "[DRY RUN] Would build: docker build -t $full_image_name --target production ."
        return 0
    fi
    
    docker build \
        -t "$full_image_name" \
        --target production \
        --build-arg VERSION="$VERSION" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --build-arg VCS_REF="$(git rev-parse HEAD)" \
        .
    
    # Also tag as latest for the environment
    local latest_tag="${IMAGE_NAME}:${ENVIRONMENT}-latest"
    if [ -n "$DOCKER_REGISTRY" ]; then
        latest_tag="${DOCKER_REGISTRY}/${latest_tag}"
    fi
    
    docker tag "$full_image_name" "$latest_tag"
    
    log_success "Images built successfully"
    log_info "Built images:"
    log_info "  - $full_image_name"
    log_info "  - $latest_tag"
}

# Run tests
run_tests() {
    if [ "${SKIP_TESTS:-false}" = "true" ]; then
        log_warning "Skipping tests as requested"
        return 0
    fi
    
    log_info "Running tests..."
    
    cd "$PROJECT_ROOT"
    
    if [ "${DRY_RUN:-false}" = "true" ]; then
        log_info "[DRY RUN] Would run tests"
        return 0
    fi
    
    # Build test image
    docker build -t "${IMAGE_NAME}:test" --target development .
    
    # Run unit tests
    log_info "Running unit tests..."
    docker run --rm \
        -v "$PROJECT_ROOT:/app" \
        "${IMAGE_NAME}:test" \
        python -m pytest tests/ -v --cov=. --cov-report=term-missing
    
    # Run security scan
    log_info "Running security scan..."
    if command -v trivy &> /dev/null; then
        trivy image "${IMAGE_NAME}:${VERSION}"
    else
        log_warning "Trivy not found, skipping security scan"
    fi
    
    # Run linting
    log_info "Running code quality checks..."
    docker run --rm \
        -v "$PROJECT_ROOT:/app" \
        "${IMAGE_NAME}:test" \
        sh -c "black --check . && flake8 . && mypy ."
    
    log_success "All tests passed"
}

# Push images to registry
push_images() {
    if [ -z "$DOCKER_REGISTRY" ]; then
        log_error "DOCKER_REGISTRY not set, cannot push images"
        exit 1
    fi
    
    log_info "Pushing images to registry..."
    
    local full_image_name="${DOCKER_REGISTRY}/${IMAGE_NAME}:${VERSION}"
    local latest_tag="${DOCKER_REGISTRY}/${IMAGE_NAME}:${ENVIRONMENT}-latest"
    
    if [ "${DRY_RUN:-false}" = "true" ]; then
        log_info "[DRY RUN] Would push:"
        log_info "  - $full_image_name"
        log_info "  - $latest_tag"
        return 0
    fi
    
    # Login to registry if credentials are available
    if [ -n "${DOCKER_USERNAME:-}" ] && [ -n "${DOCKER_PASSWORD:-}" ]; then
        echo "$DOCKER_PASSWORD" | docker login "$DOCKER_REGISTRY" -u "$DOCKER_USERNAME" --password-stdin
    fi
    
    docker push "$full_image_name"
    docker push "$latest_tag"
    
    log_success "Images pushed successfully"
}

# Deploy to Kubernetes
deploy_to_kubernetes() {
    log_info "Deploying to Kubernetes environment: $ENVIRONMENT"
    
    cd "$PROJECT_ROOT"
    
    # Create namespace if it doesn't exist
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "Creating namespace: $NAMESPACE"
        if [ "${DRY_RUN:-false}" != "true" ]; then
            kubectl create namespace "$NAMESPACE"
        fi
    fi
    
    # Apply Kubernetes manifests
    local k8s_dir="k8s"
    local manifests=(
        "namespace.yaml"
        "secret-templates.yaml"
        "configmap.yaml"
        "rbac.yaml"
        "pvc.yaml"
        "deployment.yaml"
        "service.yaml"
        "ingress.yaml"
        "hpa.yaml"
    )
    
    # Update image references in deployment
    local full_image_name="${IMAGE_NAME}:${VERSION}"
    if [ -n "$DOCKER_REGISTRY" ]; then
        full_image_name="${DOCKER_REGISTRY}/${full_image_name}"
    fi
    
    # Create temporary deployment file with updated image
    local temp_deployment="/tmp/deployment-${VERSION}.yaml"
    sed "s|image: goose-slackbot:latest|image: ${full_image_name}|g" \
        "$k8s_dir/deployment.yaml" > "$temp_deployment"
    
    if [ "${DRY_RUN:-false}" = "true" ]; then
        log_info "[DRY RUN] Would apply Kubernetes manifests:"
        for manifest in "${manifests[@]}"; do
            log_info "  - $k8s_dir/$manifest"
        done
        log_info "  - $temp_deployment (modified deployment)"
        rm -f "$temp_deployment"
        return 0
    fi
    
    # Apply manifests
    for manifest in "${manifests[@]}"; do
        local manifest_path="$k8s_dir/$manifest"
        if [ -f "$manifest_path" ]; then
            log_info "Applying $manifest..."
            kubectl apply -f "$manifest_path" -n "$NAMESPACE"
        else
            log_warning "Manifest not found: $manifest_path"
        fi
    done
    
    # Apply modified deployment
    log_info "Applying deployment with image: $full_image_name"
    kubectl apply -f "$temp_deployment" -n "$NAMESPACE"
    rm -f "$temp_deployment"
    
    # Wait for deployment to complete
    log_info "Waiting for deployment to complete..."
    kubectl rollout status deployment/goose-slackbot-app -n "$NAMESPACE" --timeout=600s
    
    # Verify deployment
    verify_deployment
    
    log_success "Deployment completed successfully"
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check pod status
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" -l app=goose-slackbot,component=app -o jsonpath='{.items[*].metadata.name}')
    
    if [ -z "$pods" ]; then
        log_error "No pods found for the application"
        return 1
    fi
    
    # Check if pods are ready
    local ready_pods
    ready_pods=$(kubectl get pods -n "$NAMESPACE" -l app=goose-slackbot,component=app -o jsonpath='{.items[?(@.status.conditions[?(@.type=="Ready")].status=="True")].metadata.name}')
    
    local total_pods
    total_pods=$(echo "$pods" | wc -w)
    local ready_count
    ready_count=$(echo "$ready_pods" | wc -w)
    
    log_info "Pods status: $ready_count/$total_pods ready"
    
    if [ "$ready_count" -eq 0 ]; then
        log_error "No pods are ready"
        return 1
    fi
    
    # Test health endpoint
    log_info "Testing health endpoint..."
    local pod_name
    pod_name=$(echo "$ready_pods" | awk '{print $1}')
    
    if kubectl exec -n "$NAMESPACE" "$pod_name" -- python health_check.py --check health --exit-code; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        return 1
    fi
    
    log_success "Deployment verification completed"
}

# Rollback deployment
rollback_deployment() {
    log_info "Rolling back deployment..."
    
    if [ "${DRY_RUN:-false}" = "true" ]; then
        log_info "[DRY RUN] Would rollback deployment"
        return 0
    fi
    
    kubectl rollout undo deployment/goose-slackbot-app -n "$NAMESPACE"
    kubectl rollout status deployment/goose-slackbot-app -n "$NAMESPACE" --timeout=300s
    
    log_success "Rollback completed"
}

# Check deployment status
check_status() {
    log_info "Checking deployment status..."
    
    echo "=== Namespace ==="
    kubectl get namespace "$NAMESPACE" 2>/dev/null || echo "Namespace not found"
    
    echo -e "\n=== Deployments ==="
    kubectl get deployments -n "$NAMESPACE" 2>/dev/null || echo "No deployments found"
    
    echo -e "\n=== Pods ==="
    kubectl get pods -n "$NAMESPACE" 2>/dev/null || echo "No pods found"
    
    echo -e "\n=== Services ==="
    kubectl get services -n "$NAMESPACE" 2>/dev/null || echo "No services found"
    
    echo -e "\n=== Ingress ==="
    kubectl get ingress -n "$NAMESPACE" 2>/dev/null || echo "No ingress found"
    
    echo -e "\n=== HPA ==="
    kubectl get hpa -n "$NAMESPACE" 2>/dev/null || echo "No HPA found"
    
    # Check application health if pods are running
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" -l app=goose-slackbot,component=app -o jsonpath='{.items[?(@.status.phase=="Running")].metadata.name}' 2>/dev/null)
    
    if [ -n "$pods" ]; then
        echo -e "\n=== Application Health ==="
        local pod_name
        pod_name=$(echo "$pods" | awk '{print $1}')
        kubectl exec -n "$NAMESPACE" "$pod_name" -- python health_check.py --check health --json 2>/dev/null || echo "Health check failed"
    fi
}

# Show application logs
show_logs() {
    log_info "Showing application logs..."
    
    local pods
    pods=$(kubectl get pods -n "$NAMESPACE" -l app=goose-slackbot,component=app -o jsonpath='{.items[*].metadata.name}' 2>/dev/null)
    
    if [ -z "$pods" ]; then
        log_error "No application pods found"
        return 1
    fi
    
    # Show logs from all pods
    for pod in $pods; do
        echo "=== Logs from $pod ==="
        kubectl logs -n "$NAMESPACE" "$pod" --tail=100
        echo ""
    done
}

# Cleanup old resources
cleanup_resources() {
    log_info "Cleaning up old resources..."
    
    if [ "${DRY_RUN:-false}" = "true" ]; then
        log_info "[DRY RUN] Would cleanup old resources"
        return 0
    fi
    
    # Remove old ReplicaSets
    kubectl delete rs -n "$NAMESPACE" --cascade=false \
        $(kubectl get rs -n "$NAMESPACE" -o jsonpath='{.items[?(@.spec.replicas==0)].metadata.name}') 2>/dev/null || true
    
    # Remove old Docker images (keep last 5 versions)
    if command -v docker &> /dev/null; then
        docker images "${IMAGE_NAME}" --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}" | \
        tail -n +2 | sort -k2 -r | tail -n +6 | awk '{print $1}' | \
        xargs -r docker rmi 2>/dev/null || true
    fi
    
    log_success "Cleanup completed"
}

# Main execution
main() {
    local command=""
    
    # Parse arguments
    parse_args "$@"
    
    # Validate command
    if [ -z "${COMMAND:-}" ]; then
        log_error "No command specified"
        show_help
        exit 1
    fi
    
    # Set full image name
    FULL_IMAGE_NAME="${IMAGE_NAME}:${VERSION}"
    if [ -n "$DOCKER_REGISTRY" ]; then
        FULL_IMAGE_NAME="${DOCKER_REGISTRY}/${FULL_IMAGE_NAME}"
    fi
    
    log_info "Starting deployment process..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    log_info "Namespace: $NAMESPACE"
    log_info "Image: $FULL_IMAGE_NAME"
    
    # Execute command
    case "$COMMAND" in
        build)
            check_prerequisites
            build_images
            ;;
        test)
            check_prerequisites
            run_tests
            ;;
        push)
            check_prerequisites
            push_images
            ;;
        deploy)
            check_prerequisites
            build_images
            run_tests
            push_images
            deploy_to_kubernetes
            ;;
        rollback)
            check_prerequisites
            rollback_deployment
            ;;
        status)
            check_status
            ;;
        logs)
            show_logs
            ;;
        cleanup)
            cleanup_resources
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            show_help
            exit 1
            ;;
    esac
    
    log_success "Command '$COMMAND' completed successfully"
}

# Run main function
main "$@"
