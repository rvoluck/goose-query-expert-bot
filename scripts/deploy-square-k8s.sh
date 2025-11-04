#!/bin/bash
# Square Kubernetes Deployment Script
# Interactive deployment helper for Goose Query Expert Slackbot

set -e

echo "🚀 Square Kubernetes Deployment Helper"
echo "======================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check kubectl
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl not found${NC}"
    echo "Install with: brew install kubectl"
    exit 1
fi
echo -e "${GREEN}✅ kubectl found${NC}"

# Check docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found${NC}"
    echo "Install with: brew install --cask docker"
    exit 1
fi
echo -e "${GREEN}✅ Docker found${NC}"

# Check kubectl context
echo ""
echo "🔍 Current kubectl context:"
kubectl config current-context || echo -e "${YELLOW}⚠️  No context set${NC}"

echo ""
echo "📝 What would you like to do?"
echo ""
echo "1) Check Square k8s access"
echo "2) Build Docker image"
echo "3) Configure deployment manifests"
echo "4) Deploy to Kubernetes"
echo "5) Check deployment status"
echo "6) View logs"
echo "7) Update Slack app URLs"
echo "8) Full deployment (all steps)"
echo "9) Exit"
echo ""
read -p "Enter choice [1-9]: " choice

case $choice in
    1)
        echo ""
        echo "🔍 Checking Square Kubernetes access..."
        echo ""
        
        echo "Available contexts:"
        kubectl config get-contexts
        
        echo ""
        read -p "Enter the Square k8s context name: " context_name
        
        if kubectl config use-context "$context_name" 2>/dev/null; then
            echo -e "${GREEN}✅ Successfully switched to context: $context_name${NC}"
            
            echo ""
            echo "Testing cluster access..."
            if kubectl cluster-info &> /dev/null; then
                echo -e "${GREEN}✅ Cluster access confirmed!${NC}"
                kubectl cluster-info
            else
                echo -e "${RED}❌ Cannot access cluster${NC}"
                echo "You may need to authenticate or request access"
            fi
        else
            echo -e "${RED}❌ Context not found${NC}"
            echo "Request access to Square's k8s cluster from DevOps team"
        fi
        ;;
        
    2)
        echo ""
        echo "🐳 Building Docker image..."
        echo ""
        
        read -p "Enter Square container registry URL (e.g., registry.sqprod.co): " registry_url
        
        echo "Building image..."
        docker build -t goose-slackbot:latest -f Dockerfile.optimized .
        
        echo "Tagging for registry..."
        docker tag goose-slackbot:latest "$registry_url/goose-slackbot:latest"
        
        echo ""
        read -p "Push to registry now? (y/n): " push_choice
        
        if [ "$push_choice" = "y" ]; then
            echo "Pushing to $registry_url..."
            docker push "$registry_url/goose-slackbot:latest"
            echo -e "${GREEN}✅ Image pushed successfully!${NC}"
        else
            echo "Skipped push. Push manually with:"
            echo "docker push $registry_url/goose-slackbot:latest"
        fi
        ;;
        
    3)
        echo ""
        echo "⚙️  Configuring deployment manifests..."
        echo ""
        
        read -p "Enter Square container registry URL: " registry_url
        read -p "Enter your domain (e.g., goose-slackbot.sqprod.co): " domain
        
        echo ""
        echo "Updating k8s/deployment-complete.yaml..."
        
        # Update image URL
        sed -i.bak "s|image: goose-slackbot:latest|image: $registry_url/goose-slackbot:latest|g" k8s/deployment-complete.yaml
        
        echo -e "${GREEN}✅ Manifests updated!${NC}"
        echo ""
        echo "⚠️  IMPORTANT: You still need to update secrets manually!"
        echo "Edit k8s/deployment-complete.yaml and update:"
        echo "  - SLACK_BOT_TOKEN"
        echo "  - SLACK_CLIENT_ID"
        echo "  - SLACK_CLIENT_SECRET"
        echo "  - SLACK_SIGNING_SECRET"
        echo "  - JWT_SECRET_KEY"
        echo "  - ENCRYPTION_KEY"
        ;;
        
    4)
        echo ""
        echo "🚀 Deploying to Kubernetes..."
        echo ""
        
        read -p "Deploy to namespace 'goose-slackbot'? (y/n): " deploy_choice
        
        if [ "$deploy_choice" = "y" ]; then
            echo "Applying manifests..."
            kubectl apply -f k8s/deployment-complete.yaml
            
            echo ""
            echo "Waiting for pods to start..."
            kubectl wait --for=condition=ready pod -l app=goose-slackbot -n goose-slackbot --timeout=300s
            
            echo -e "${GREEN}✅ Deployment complete!${NC}"
            
            echo ""
            echo "📊 Deployment status:"
            kubectl get pods -n goose-slackbot
            kubectl get services -n goose-slackbot
            kubectl get ingress -n goose-slackbot
        else
            echo "Deployment cancelled"
        fi
        ;;
        
    5)
        echo ""
        echo "📊 Checking deployment status..."
        echo ""
        
        echo "Pods:"
        kubectl get pods -n goose-slackbot
        
        echo ""
        echo "Services:"
        kubectl get services -n goose-slackbot
        
        echo ""
        echo "Ingress:"
        kubectl get ingress -n goose-slackbot
        
        echo ""
        echo "Recent events:"
        kubectl get events -n goose-slackbot --sort-by='.lastTimestamp' | tail -10
        ;;
        
    6)
        echo ""
        echo "📋 Viewing logs..."
        echo ""
        
        echo "Available pods:"
        kubectl get pods -n goose-slackbot
        
        echo ""
        read -p "Enter pod name (or press Enter for app logs): " pod_name
        
        if [ -z "$pod_name" ]; then
            echo "Showing app logs..."
            kubectl logs -f deployment/goose-slackbot-app -n goose-slackbot
        else
            kubectl logs -f "$pod_name" -n goose-slackbot
        fi
        ;;
        
    7)
        echo ""
        echo "🔗 Slack App URL Configuration"
        echo ""
        
        read -p "Enter your deployed domain (e.g., goose-slackbot.sqprod.co): " domain
        
        echo ""
        echo "Update your Slack app with these URLs:"
        echo ""
        echo "1. Event Subscriptions URL:"
        echo "   https://$domain/slack/events"
        echo ""
        echo "2. Interactivity URL:"
        echo "   https://$domain/slack/events"
        echo ""
        echo "3. OAuth Redirect URL:"
        echo "   https://$domain/slack/oauth_redirect"
        echo ""
        echo "4. Test health endpoint:"
        echo "   https://$domain/health"
        echo ""
        
        read -p "Open Slack App settings? (y/n): " open_choice
        if [ "$open_choice" = "y" ]; then
            open "https://api.slack.com/apps"
        fi
        ;;
        
    8)
        echo ""
        echo "🎯 Full deployment process"
        echo ""
        echo "This will:"
        echo "1. Check k8s access"
        echo "2. Build Docker image"
        echo "3. Push to registry"
        echo "4. Deploy to k8s"
        echo "5. Show status"
        echo ""
        read -p "Continue? (y/n): " continue_choice
        
        if [ "$continue_choice" = "y" ]; then
            # Run all steps
            echo "Starting full deployment..."
            # Add full deployment logic here
            echo -e "${YELLOW}⚠️  Full deployment not yet implemented${NC}"
            echo "Please run steps individually for now"
        fi
        ;;
        
    9)
        echo "Goodbye! 👋"
        exit 0
        ;;
        
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo "✅ Done!"
