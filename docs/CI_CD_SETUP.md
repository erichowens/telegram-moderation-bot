# CI/CD Setup Guide

This guide explains how to set up Continuous Integration and Continuous Deployment for the Telegram Moderation Bot.

## 📋 Table of Contents

- [Overview](#overview)
- [GitHub Actions Setup](#github-actions-setup)
- [GitLab CI Setup](#gitlab-ci-setup)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Local Development](#local-development)
- [Monitoring](#monitoring)

## Overview

The CI/CD pipeline includes:
- **Automated Testing**: Unit tests, integration tests, security scans
- **Code Quality**: Linting, formatting, type checking
- **Security Scanning**: Dependency vulnerabilities, secret detection
- **Containerization**: Docker image building and pushing
- **Deployment**: Automated deployment to staging/production

## GitHub Actions Setup

### 1. Prerequisites

1. GitHub repository with Actions enabled
2. Required secrets in repository settings:
   ```
   DOCKER_USERNAME       # DockerHub username
   DOCKER_PASSWORD       # DockerHub password
   SNYK_TOKEN           # Snyk security scanning token
   STAGING_HOST         # Staging server IP/hostname
   STAGING_USER         # SSH user for staging
   STAGING_KEY          # SSH private key for staging
   PROD_HOST            # Production server IP/hostname
   PROD_USER            # SSH user for production
   PROD_KEY             # SSH private key for production
   ```

### 2. Workflow Configuration

The workflow is defined in `.github/workflows/ci.yml` and runs on:
- Every push to `main` and `develop` branches
- Every pull request to `main`
- Daily security scans at 2 AM UTC

### 3. Setting Up Environments

1. Go to Settings → Environments
2. Create `staging` and `production` environments
3. Add protection rules for production:
   - Required reviewers
   - Deployment branches: `main` only

### 4. Workflow Jobs

- **Lint**: Code quality checks (Black, Flake8, MyPy, Bandit)
- **Test**: Multi-OS and Python version testing
- **Security**: Trivy and Snyk vulnerability scanning
- **Docker**: Build and push container images
- **Deploy**: Automated deployment to environments

## GitLab CI Setup

### 1. Prerequisites

1. GitLab project with CI/CD enabled
2. Required variables in CI/CD settings:
   ```
   CI_REGISTRY_USER     # GitLab registry username
   CI_REGISTRY_PASSWORD # GitLab registry password
   STAGING_SSH_KEY      # SSH key for staging
   STAGING_USER         # Staging server user
   STAGING_HOST         # Staging server host
   PROD_SSH_KEY         # SSH key for production
   PROD_USER            # Production server user
   PROD_HOST            # Production server host
   ```

### 2. Pipeline Configuration

The pipeline is defined in `.gitlab-ci.yml` with stages:
1. **Lint**: Code quality checks
2. **Test**: Unit and integration tests
3. **Security**: Security scanning
4. **Build**: Docker image building
5. **Deploy**: Deployment to environments

### 3. Manual Deployments

Deployments to staging and production require manual approval:
```bash
# Trigger staging deployment
git push origin develop

# Trigger production deployment
git push origin main
```

## Docker Deployment

### 1. Local Development

```bash
# Build image
make build

# Run with docker-compose
make run-docker

# View logs
make logs

# Stop containers
make stop-docker
```

### 2. Environment Variables

Create `.env` file:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
LOG_LEVEL=INFO
MAX_WORKERS=2
CACHE_SIZE=1000
RATE_LIMIT=10
```

### 3. Docker Compose Profiles

```bash
# Run with monitoring stack
docker-compose --profile monitoring up -d

# Run with Redis cache
docker-compose --profile cache up -d
```

## Kubernetes Deployment

### 1. Prerequisites

- Kubernetes cluster (1.20+)
- kubectl configured
- Namespace created: `kubectl create namespace bots`

### 2. Deploy to Kubernetes

```bash
# Create secrets
kubectl create secret generic telegram-bot-secrets \
  --from-literal=bot-token=YOUR_TOKEN \
  -n bots

# Apply manifests
kubectl apply -f k8s/deployment.yaml

# Check deployment
kubectl get pods -n bots
kubectl logs -f deployment/telegram-mod-bot -n bots
```

### 3. Scaling

```bash
# Manual scaling
kubectl scale deployment telegram-mod-bot --replicas=5 -n bots

# Autoscaling is configured in HPA
kubectl get hpa -n bots
```

## Local Development

### 1. Setup Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

### 2. Available Make Commands

```bash
make help           # Show all available commands
make install        # Install dependencies
make test           # Run tests
make test-coverage  # Run tests with coverage
make lint           # Run linters
make format         # Format code
make security       # Run security checks
make build          # Build Docker image
make deploy-staging # Deploy to staging
```

### 3. Running Tests Locally

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/test_security.py

# With coverage
pytest tests/ --cov=src --cov-report=html

# Security tests only
make test-security
```

## Monitoring

### 1. Health Checks

The bot exposes a health check endpoint that can be monitored:

```python
# Health check returns:
{
    "status": "healthy",
    "uptime_seconds": 3600,
    "bot_info": {
        "username": "bot_name",
        "responsive": true
    },
    "moderator": {
        "status": "healthy",
        "models_loaded": 2,
        "cache_size": 150
    },
    "statistics": {
        "messages_checked": 1000,
        "violations_found": 50
    }
}
```

### 2. Prometheus Metrics

When running with monitoring profile:
```bash
docker-compose --profile monitoring up -d
```

Access metrics at:
- Prometheus: http://localhost:9090
- Node Exporter: http://localhost:9100

### 3. Logging

Logs are stored in `./logs/` directory with rotation:
- Max size: 10MB per file
- Max files: 3
- Format: JSON for structured logging

## Security Best Practices

### 1. Secret Management

- Never commit secrets to repository
- Use environment variables or secret management systems
- Rotate tokens regularly
- Use encrypted secrets in CI/CD

### 2. Dependency Management

```bash
# Check for vulnerabilities
make security

# Update dependencies
make update-deps

# Audit dependencies
make check-deps
```

### 3. Container Security

- Run as non-root user (UID 1000)
- Use minimal base images
- Scan images regularly with Trivy
- Sign images with cosign (optional)

## Troubleshooting

### Common Issues

1. **Tests failing in CI but passing locally**
   - Check Python version differences
   - Ensure all dependencies are in requirements.txt
   - Check for hardcoded paths

2. **Docker build failures**
   ```bash
   # Clear cache and rebuild
   make build-no-cache
   ```

3. **Deployment failures**
   ```bash
   # Check deployment logs
   kubectl logs deployment/telegram-mod-bot -n bots
   
   # Rollback if needed
   kubectl rollout undo deployment/telegram-mod-bot -n bots
   ```

4. **Pre-commit hook failures**
   ```bash
   # Fix formatting
   make format
   
   # Skip hooks temporarily
   git commit --no-verify
   ```

## Support

For issues or questions:
1. Check the [GitHub Issues](https://github.com/yourusername/telegram-mod-bot/issues)
2. Review CI/CD logs in Actions/Pipelines tab
3. Contact the DevOps team

## License

This CI/CD configuration is part of the Telegram Moderation Bot project and follows the same license terms.