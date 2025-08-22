#!/bin/bash

# Deployment script for Telegram Moderation Bot
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
NAMESPACE=${3:-bots}

echo -e "${GREEN}🚀 Deploying Telegram Moderation Bot${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Version: ${YELLOW}$VERSION${NC}"
echo -e "Namespace: ${YELLOW}$NAMESPACE${NC}"

# Function to check prerequisites
check_prerequisites() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"
    
    # Check for required tools
    command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed.${NC}" >&2; exit 1; }
    command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}kubectl is required but not installed.${NC}" >&2; exit 1; }
    
    # Check Docker daemon
    docker info >/dev/null 2>&1 || { echo -e "${RED}Docker daemon is not running.${NC}" >&2; exit 1; }
    
    # Check kubectl connection
    kubectl cluster-info >/dev/null 2>&1 || { echo -e "${RED}Cannot connect to Kubernetes cluster.${NC}" >&2; exit 1; }
    
    echo -e "${GREEN}✓ All prerequisites met${NC}"
}

# Function to run tests
run_tests() {
    echo -e "\n${YELLOW}Running tests...${NC}"
    
    # Run security tests
    echo "Running security checks..."
    bandit -r src/ -ll || { echo -e "${RED}Security check failed${NC}"; exit 1; }
    
    # Run unit tests
    echo "Running unit tests..."
    python -m pytest tests/ --ignore=tests/test_gui.py -q || { echo -e "${RED}Tests failed${NC}"; exit 1; }
    
    echo -e "${GREEN}✓ All tests passed${NC}"
}

# Function to build Docker image
build_image() {
    echo -e "\n${YELLOW}Building Docker image...${NC}"
    
    IMAGE_NAME="telegram-mod-bot"
    IMAGE_TAG="${VERSION}-${ENVIRONMENT}"
    
    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} . || { echo -e "${RED}Docker build failed${NC}"; exit 1; }
    
    # Tag for registry
    docker tag ${IMAGE_NAME}:${IMAGE_TAG} ghcr.io/${GITHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}
    
    echo -e "${GREEN}✓ Docker image built successfully${NC}"
}

# Function to push to registry
push_image() {
    echo -e "\n${YELLOW}Pushing image to registry...${NC}"
    
    # Login to GitHub Container Registry
    echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin
    
    # Push image
    docker push ghcr.io/${GITHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG}
    
    echo -e "${GREEN}✓ Image pushed to registry${NC}"
}

# Function to deploy to Kubernetes
deploy_k8s() {
    echo -e "\n${YELLOW}Deploying to Kubernetes...${NC}"
    
    # Create namespace if it doesn't exist
    kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply configurations
    kubectl apply -f k8s/deployment.yaml -n ${NAMESPACE}
    
    # Update image
    kubectl set image deployment/telegram-mod-bot telegram-bot=ghcr.io/${GITHUB_USER}/${IMAGE_NAME}:${IMAGE_TAG} -n ${NAMESPACE}
    
    # Wait for rollout
    kubectl rollout status deployment/telegram-mod-bot -n ${NAMESPACE}
    
    echo -e "${GREEN}✓ Deployed to Kubernetes${NC}"
}

# Function to deploy with Docker Compose
deploy_docker_compose() {
    echo -e "\n${YELLOW}Deploying with Docker Compose...${NC}"
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Creating .env file...${NC}"
        cat > .env <<EOF
TELEGRAM_BOT_TOKEN=your_token_here
LOG_LEVEL=INFO
MAX_WORKERS=2
CACHE_SIZE=1000
RATE_LIMIT=10
EOF
        echo -e "${RED}⚠️  Please update .env file with your bot token${NC}"
        exit 1
    fi
    
    # Deploy with docker-compose
    docker-compose up -d --build
    
    # Check if containers are running
    docker-compose ps
    
    echo -e "${GREEN}✓ Deployed with Docker Compose${NC}"
}

# Function to check deployment health
check_health() {
    echo -e "\n${YELLOW}Checking deployment health...${NC}"
    
    if [ "$DEPLOYMENT_METHOD" = "k8s" ]; then
        # Get pod status
        kubectl get pods -n ${NAMESPACE} -l app=telegram-mod-bot
        
        # Check pod logs
        POD_NAME=$(kubectl get pods -n ${NAMESPACE} -l app=telegram-mod-bot -o jsonpath="{.items[0].metadata.name}")
        echo -e "\nRecent logs from ${POD_NAME}:"
        kubectl logs ${POD_NAME} -n ${NAMESPACE} --tail=20
    else
        # Check Docker container
        docker-compose logs --tail=20 telegram-bot
    fi
    
    echo -e "${GREEN}✓ Health check complete${NC}"
}

# Function to rollback deployment
rollback() {
    echo -e "\n${RED}Rolling back deployment...${NC}"
    
    if [ "$DEPLOYMENT_METHOD" = "k8s" ]; then
        kubectl rollout undo deployment/telegram-mod-bot -n ${NAMESPACE}
        kubectl rollout status deployment/telegram-mod-bot -n ${NAMESPACE}
    else
        docker-compose down
        docker-compose up -d
    fi
    
    echo -e "${GREEN}✓ Rollback complete${NC}"
}

# Main deployment flow
main() {
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}   Telegram Bot Deployment Script${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
    
    # Check prerequisites
    check_prerequisites
    
    # Run tests (optional, can be skipped with --skip-tests)
    if [[ "$*" != *"--skip-tests"* ]]; then
        run_tests
    fi
    
    # Build image
    build_image
    
    # Determine deployment method
    if kubectl cluster-info >/dev/null 2>&1; then
        DEPLOYMENT_METHOD="k8s"
        push_image
        deploy_k8s
    else
        DEPLOYMENT_METHOD="compose"
        deploy_docker_compose
    fi
    
    # Check health
    check_health
    
    echo -e "\n${GREEN}═══════════════════════════════════════${NC}"
    echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════${NC}"
}

# Handle errors
trap 'echo -e "\n${RED}Deployment failed!${NC}"; rollback' ERR

# Run main function
main "$@"