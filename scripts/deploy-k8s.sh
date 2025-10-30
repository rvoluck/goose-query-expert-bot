#!/bin/bash
# ================================
# Kubernetes Deployment Script
# Deploys the application to Kubernetes cluster
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
K8S_DIR="${PROJECT_ROOT}/k8s"
NAMESPACE="goose-slackbot"
APP_NAME="goose-slackbot"
IMAGE_NAME="${IMAGE_NAME:-goose-slackbot}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if kubectl can connect to cluster
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    # Check Docker (for building images)
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    log_info "Prerequisites check passed"
    log_info "Connected to cluster: $(kubectl config current-context)"
}

create_namespace() {
    log_step "Creating namespace..."
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_info "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace "$NAMESPACE"
        log_info "Namespace $NAMESPACE created"
    fi
}

create_secrets() {
    log_step "Creating secrets..."
    
    # Check if secrets file exists
    local secrets_file="${K8S_DIR}/secrets.yaml"
    
    if [ ! -f "$secrets_file" ]; then
        log_warn "Secrets file not found: $secrets_file"
        log_warn "Please create secrets manually or use secret-templates.yaml"
        
        # Create secrets from environment variables if available
        if [ -f "${PROJECT_ROOT}/.env" ]; then
            log_info "Creating secrets from .env file..."
            
            # Source .env file
            set -a
            source "${PROJECT_ROOT}/.env"
            set +a
            
            # Create secrets
            kubectl create secret generic goose-slackbot-secrets \
                --from-literal=SLACK_BOT_TOKEN="${SLACK_BOT_TOKEN}" \
                --from-literal=SLACK_APP_TOKEN="${SLACK_APP_TOKEN}" \
                --from-literal=SLACK_SIGNING_SECRET="${SLACK_SIGNING_SECRET}" \
                --from-literal=JWT_SECRET_KEY="${JWT_SECRET_KEY}" \
                --from-literal=ENCRYPTION_KEY="${ENCRYPTION_KEY}" \
                --from-literal=DATABASE_URL="${DATABASE_URL}" \
                --from-literal=REDIS_URL="${REDIS_URL}" \
                --namespace="$NAMESPACE" \
                --dry-run=client -o yaml | kubectl apply -f -
            
            kubectl create secret generic postgres-secrets \
                --from-literal=POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
                --namespace="$NAMESPACE" \
                --dry-run=client -o yaml | kubectl apply -f -
            
            kubectl create secret generic redis-secrets \
                --from-literal=REDIS_PASSWORD="${REDIS_PASSWORD}" \
                --namespace="$NAMESPACE" \
                --dry-run=client -o yaml | kubectl apply -f -
            
            log_info "Secrets created from .env file"
        else
            log_error "No .env file found. Cannot create secrets automatically."
            log_error "Please create secrets manually before deploying."
            exit 1
        fi
    else
        kubectl apply -f "$secrets_file" -n "$NAMESPACE"
        log_info "Secrets applied from $secrets_file"
    fi
}

build_and_push_image() {
    log_step "Building and pushing Docker image..."
    
    local full_image="${IMAGE_NAME}:${IMAGE_TAG}"
    
    log_info "Building image: $full_image"
    
    cd "$PROJECT_ROOT"
    docker build -t "$full_image" -f Dockerfile.optimized --target production .
    
    # If registry is specified, push the image
    if [ -n "$DOCKER_REGISTRY" ]; then
        local registry_image="${DOCKER_REGISTRY}/${full_image}"
        log_info "Tagging image for registry: $registry_image"
        docker tag "$full_image" "$registry_image"
        
        log_info "Pushing image to registry..."
        docker push "$registry_image"
        
        log_info "Image pushed successfully"
        
        # Update image name to use registry
        IMAGE_NAME="${DOCKER_REGISTRY}/${IMAGE_NAME}"
    else
        log_warn "No DOCKER_REGISTRY specified. Skipping push to registry."
        log_warn "Make sure the image is available in your cluster."
    fi
}

apply_manifests() {
    log_step "Applying Kubernetes manifests..."
    
    # Apply in order
    local manifests=(
        "namespace.yaml"
        "configmap.yaml"
        "pvc.yaml"
        "rbac.yaml"
        "deployment-complete.yaml"
        "service.yaml"
        "hpa.yaml"
        "ingress.yaml"
    )
    
    for manifest in "${manifests[@]}"; do
        local manifest_file="${K8S_DIR}/${manifest}"
        
        if [ -f "$manifest_file" ]; then
            log_info "Applying $manifest..."
            
            # Replace image placeholders
            sed "s|IMAGE_NAME|${IMAGE_NAME}|g; s|IMAGE_TAG|${IMAGE_TAG}|g" "$manifest_file" | \
                kubectl apply -f - -n "$NAMESPACE"
        else
            log_warn "Manifest not found: $manifest_file"
        fi
    done
    
    log_info "All manifests applied successfully"
}

wait_for_deployment() {
    log_step "Waiting for deployment to be ready..."
    
    local timeout=300
    local start_time=$(date +%s)
    
    while true; do
        local ready=$(kubectl get deployment goose-slackbot-app -n "$NAMESPACE" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
        local desired=$(kubectl get deployment goose-slackbot-app -n "$NAMESPACE" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
        
        if [ "$ready" = "$desired" ] && [ "$ready" != "0" ]; then
            log_info "Deployment is ready! ($ready/$desired replicas)"
            break
        fi
        
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [ $elapsed -gt $timeout ]; then
            log_error "Timeout waiting for deployment to be ready"
            kubectl get pods -n "$NAMESPACE"
            exit 1
        fi
        
        log_info "Waiting for deployment... ($ready/$desired replicas ready, ${elapsed}s elapsed)"
        sleep 5
    done
}

run_health_check() {
    log_step "Running health checks..."
    
    # Get a pod name
    local pod=$(kubectl get pods -n "$NAMESPACE" -l app=goose-slackbot,component=app -o jsonpath='{.items[0].metadata.name}')
    
    if [ -z "$pod" ]; then
        log_error "No pods found"
        return 1
    fi
    
    log_info "Checking health on pod: $pod"
    
    # Run health check
    if kubectl exec -n "$NAMESPACE" "$pod" -- python health_check.py --check health --exit-code; then
        log_info "✓ Health check passed"
    else
        log_error "✗ Health check failed"
        return 1
    fi
}

show_status() {
    log_step "Deployment status:"
    
    echo ""
    log_info "Pods:"
    kubectl get pods -n "$NAMESPACE" -o wide
    
    echo ""
    log_info "Services:"
    kubectl get services -n "$NAMESPACE"
    
    echo ""
    log_info "Deployments:"
    kubectl get deployments -n "$NAMESPACE"
    
    echo ""
    log_info "HPA:"
    kubectl get hpa -n "$NAMESPACE"
    
    echo ""
    log_info "PVCs:"
    kubectl get pvc -n "$NAMESPACE"
}

show_logs() {
    local component=${1:-app}
    
    log_info "Showing logs for component: $component"
    
    kubectl logs -n "$NAMESPACE" -l component="$component" --tail=100 -f
}

rollback_deployment() {
    log_warn "Rolling back deployment..."
    
    kubectl rollout undo deployment/goose-slackbot-app -n "$NAMESPACE"
    
    log_info "Rollback initiated"
    wait_for_deployment
    log_info "Rollback completed"
}

delete_deployment() {
    log_warn "This will delete all resources in namespace: $NAMESPACE"
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "Deletion cancelled"
        return 0
    fi
    
    log_info "Deleting all resources..."
    
    kubectl delete namespace "$NAMESPACE"
    
    log_info "All resources deleted"
}

port_forward() {
    local service=${1:-goose-slackbot-service}
    local local_port=${2:-3000}
    local remote_port=${3:-3000}
    
    log_info "Port forwarding $service:$remote_port to localhost:$local_port"
    log_info "Press Ctrl+C to stop"
    
    kubectl port-forward -n "$NAMESPACE" "service/$service" "$local_port:$remote_port"
}

scale_deployment() {
    local replicas=$1
    
    if [ -z "$replicas" ]; then
        log_error "Please specify number of replicas"
        exit 1
    fi
    
    log_info "Scaling deployment to $replicas replicas..."
    
    kubectl scale deployment/goose-slackbot-app -n "$NAMESPACE" --replicas="$replicas"
    
    log_info "Deployment scaled"
    wait_for_deployment
}

show_help() {
    cat << EOF
Kubernetes Deployment Script for Goose Slackbot

Usage: $0 [COMMAND] [OPTIONS]

Commands:
    deploy              Full deployment (build, push, apply manifests)
    apply               Apply Kubernetes manifests only
    build               Build and push Docker image only
    status              Show deployment status
    logs [component]    Show logs (default: app)
    health              Run health checks
    rollback            Rollback to previous deployment
    scale [replicas]    Scale deployment to N replicas
    port-forward        Port forward service to localhost
    delete              Delete all resources
    help                Show this help message

Environment Variables:
    IMAGE_NAME          Docker image name (default: goose-slackbot)
    IMAGE_TAG           Docker image tag (default: latest)
    DOCKER_REGISTRY     Docker registry URL (optional)
    NAMESPACE           Kubernetes namespace (default: goose-slackbot)

Examples:
    $0 deploy                       Full deployment
    $0 apply                        Apply manifests only
    $0 logs app                     Show application logs
    $0 scale 5                      Scale to 5 replicas
    $0 port-forward                 Port forward to localhost:3000
    
    IMAGE_TAG=v1.2.3 $0 deploy      Deploy with specific tag
    DOCKER_REGISTRY=myregistry.io $0 build    Build and push to registry

EOF
}

# Main script
main() {
    local command=${1:-help}
    
    case $command in
        deploy)
            check_prerequisites
            create_namespace
            create_secrets
            build_and_push_image
            apply_manifests
            wait_for_deployment
            run_health_check
            show_status
            log_info "Deployment completed successfully!"
            log_info "Run '$0 port-forward' to access the application"
            ;;
        
        apply)
            check_prerequisites
            create_namespace
            create_secrets
            apply_manifests
            wait_for_deployment
            show_status
            ;;
        
        build)
            check_prerequisites
            build_and_push_image
            ;;
        
        status)
            show_status
            ;;
        
        logs)
            show_logs "$2"
            ;;
        
        health)
            run_health_check
            ;;
        
        rollback)
            rollback_deployment
            ;;
        
        scale)
            scale_deployment "$2"
            ;;
        
        port-forward)
            port_forward "$2" "$3" "$4"
            ;;
        
        delete)
            delete_deployment
            ;;
        
        help|*)
            show_help
            ;;
    esac
}

# Run main function
main "$@"
