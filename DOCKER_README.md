# Docker Deployment Guide

This document provides detailed information about the Docker deployment configuration for Goose Slackbot.

## Table of Contents

1. [Docker Files Overview](#docker-files-overview)
2. [Docker Images](#docker-images)
3. [Docker Compose Configurations](#docker-compose-configurations)
4. [Environment Variables](#environment-variables)
5. [Volumes and Persistence](#volumes-and-persistence)
6. [Networking](#networking)
7. [Health Checks](#health-checks)
8. [Resource Limits](#resource-limits)
9. [Monitoring Stack](#monitoring-stack)
10. [Best Practices](#best-practices)

## Docker Files Overview

### Dockerfile.optimized

Multi-stage Dockerfile with the following stages:

1. **python-base**: Base Python image with common configuration
2. **builder**: Builds dependencies in a virtual environment
3. **development**: Development image with debugging tools
4. **production**: Optimized production image
5. **testing**: Image for running tests
6. **security-scan**: Image for security scanning

**Key Features:**
- Multi-stage build for smaller production images
- Non-root user for security
- Health checks built-in
- Optimized layer caching
- Security scanning support

### docker-compose.yml (Development)

Development configuration with:
- Hot-reload enabled
- Debug logging
- Development tools included
- Local volume mounts
- Optional monitoring stack

### docker-compose.prod.yml (Production)

Production configuration with:
- Optimized images
- Resource limits
- Full monitoring stack (Prometheus, Grafana, AlertManager)
- Automated backups
- Nginx reverse proxy (optional)
- Proper logging configuration

## Docker Images

### Building Images

```bash
# Build development image
docker build -t goose-slackbot:dev -f Dockerfile.optimized --target development .

# Build production image
docker build -t goose-slackbot:latest -f Dockerfile.optimized --target production .

# Build with specific version
docker build -t goose-slackbot:v1.0.0 -f Dockerfile.optimized --target production .

# Build testing image
docker build -t goose-slackbot:test -f Dockerfile.optimized --target testing .
```

### Image Sizes

Approximate sizes:
- **Development**: ~800MB (includes dev tools)
- **Production**: ~400MB (optimized)
- **Testing**: ~850MB (includes test frameworks)

### Image Tags

Recommended tagging strategy:
- `latest`: Latest stable production build
- `v1.0.0`: Semantic version tags
- `dev`: Latest development build
- `staging`: Staging environment build
- `<git-sha>`: Specific commit builds

## Docker Compose Configurations

### Development (docker-compose.yml)

**Services:**
- `app`: Main application with hot-reload
- `postgres`: PostgreSQL database
- `redis`: Redis cache
- `goose-mcp`: Mock Goose MCP server
- `prometheus`: Metrics collection (optional)
- `grafana`: Monitoring dashboards (optional)
- `pgadmin`: Database admin UI (optional)
- `redis-commander`: Redis admin UI (optional)

**Profiles:**
- `monitoring`: Enable Prometheus and Grafana
- `dev-tools`: Enable PgAdmin and Redis Commander

**Usage:**
```bash
# Start basic services
docker-compose up -d

# Start with monitoring
docker-compose --profile monitoring up -d

# Start with all dev tools
docker-compose --profile dev-tools up -d
```

### Production (docker-compose.prod.yml)

**Additional Services:**
- `alertmanager`: Alert management
- `nginx`: Reverse proxy (optional)
- `backup`: Automated database backups

**Features:**
- Resource limits enforced
- Proper logging configuration
- Health checks configured
- Restart policies set
- Volume persistence configured

**Usage:**
```bash
# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Start with nginx
docker-compose -f docker-compose.prod.yml --profile with-nginx up -d

# Start with backups
docker-compose -f docker-compose.prod.yml --profile with-backup up -d
```

## Environment Variables

### Required Variables

```bash
# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_SIGNING_SECRET=...

# Security
JWT_SECRET_KEY=...
ENCRYPTION_KEY=...

# Database
POSTGRES_PASSWORD=...
REDIS_PASSWORD=...
```

### Optional Variables

```bash
# Application
WORKERS=4
DEBUG=false
LOG_LEVEL=INFO

# Features
ENABLE_QUERY_HISTORY=true
ENABLE_FILE_UPLOADS=true

# Performance
MAX_RESULT_ROWS=10000
QUERY_TIMEOUT_SECONDS=300
```

### Environment File

Create `.env` file:
```bash
cp env.example .env
# Edit .env with your values
```

## Volumes and Persistence

### Volume Types

1. **Named Volumes** (recommended for production):
   ```yaml
   volumes:
     postgres_data:
       driver: local
   ```

2. **Bind Mounts** (for development):
   ```yaml
   volumes:
     - ./data:/app/data
   ```

### Data Persistence

**PostgreSQL Data:**
- Location: `postgres_data` volume or `./data/postgres`
- Contains: Database files
- Backup: Use `pg_dump` or automated backup service

**Redis Data:**
- Location: `redis_data` volume or `./data/redis`
- Contains: Cache and session data
- Persistence: AOF (Append-Only File) enabled

**Application Data:**
- Location: `app_data` volume or `./data/app`
- Contains: Uploaded files, temporary data
- Backup: Regular file system backups

**Logs:**
- Location: `app_logs` volume or `./logs`
- Contains: Application logs
- Rotation: Configured in logging driver

### Backup Strategy

```bash
# Manual backup
docker-compose exec postgres pg_dump -U goose_user goose_slackbot > backup.sql

# Automated backup (production)
# Configured in docker-compose.prod.yml with cron schedule
```

## Networking

### Network Configuration

**Development:**
```yaml
networks:
  goose-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

**Production:**
- Application network: 172.20.0.0/16
- Monitoring network: 172.21.0.0/16

### Service Communication

Services communicate using service names:
```bash
# Database connection
postgresql://goose_user:password@postgres:5432/goose_slackbot

# Redis connection
redis://:password@redis:6379/0

# Goose MCP
http://goose-mcp:8000
```

### Port Mapping

**Default Ports:**
- Application: 3000
- Metrics: 9090
- PostgreSQL: 5432
- Redis: 6379
- Prometheus: 9091
- Grafana: 3001
- AlertManager: 9093

**Customize Ports:**
```bash
# In .env file
APP_PORT=8080
POSTGRES_PORT=5433
```

## Health Checks

### Application Health Check

```yaml
healthcheck:
  test: ["CMD", "python", "health_check.py", "--check", "liveness", "--exit-code"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

### Database Health Check

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U goose_user -d goose_slackbot"]
  interval: 10s
  timeout: 5s
  retries: 5
  start_period: 10s
```

### Redis Health Check

```yaml
healthcheck:
  test: ["CMD", "redis-cli", "ping"]
  interval: 10s
  timeout: 3s
  retries: 5
  start_period: 10s
```

### Checking Health

```bash
# Check all services
docker-compose ps

# Check specific service
docker-compose exec app python health_check.py --check health

# View health status
docker inspect --format='{{.State.Health.Status}}' goose-slackbot-app
```

## Resource Limits

### Development Limits

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 512M
```

### Production Limits

**Application:**
- CPU: 0.5-2 cores
- Memory: 512MB-2GB

**PostgreSQL:**
- CPU: 0.5-2 cores
- Memory: 512MB-2GB

**Redis:**
- CPU: 0.25-1 core
- Memory: 256MB-1GB

### Adjusting Limits

Edit `docker-compose.prod.yml`:
```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
```

## Monitoring Stack

### Prometheus

**Configuration:** `monitoring/prometheus.yml`

**Metrics Collected:**
- Application metrics (port 9090)
- System metrics
- Container metrics
- Database metrics (if exporter installed)

**Access:** http://localhost:9091

### Grafana

**Configuration:** `monitoring/grafana/`

**Dashboards:**
- Application Overview
- Database Performance
- System Resources
- Custom dashboards in `monitoring/grafana/dashboards/`

**Access:** http://localhost:3001
**Credentials:** admin/admin (change on first login)

### AlertManager

**Configuration:** `monitoring/alertmanager.yml`

**Features:**
- Alert routing
- Slack notifications
- Email notifications (optional)
- PagerDuty integration (optional)

**Access:** http://localhost:9093

### Setting Up Monitoring

1. **Enable monitoring profile:**
   ```bash
   docker-compose --profile monitoring up -d
   ```

2. **Configure Slack webhook:**
   Edit `monitoring/alertmanager.yml`:
   ```yaml
   global:
     slack_api_url: 'YOUR_WEBHOOK_URL'
   ```

3. **Import Grafana dashboards:**
   - Access Grafana
   - Import dashboards from `monitoring/grafana/dashboards/`

## Best Practices

### Security

1. **Use secrets management:**
   ```bash
   # Don't commit .env file
   echo ".env" >> .gitignore
   ```

2. **Run as non-root user:**
   ```dockerfile
   USER appuser
   ```

3. **Scan images regularly:**
   ```bash
   docker scan goose-slackbot:latest
   ```

4. **Keep base images updated:**
   ```bash
   docker pull python:3.11-slim
   docker-compose build --no-cache
   ```

### Performance

1. **Use multi-stage builds:**
   - Smaller images
   - Faster deployments
   - Better caching

2. **Optimize layer caching:**
   - Copy requirements first
   - Install dependencies before code
   - Use .dockerignore

3. **Resource limits:**
   - Set appropriate limits
   - Monitor resource usage
   - Scale horizontally when needed

### Reliability

1. **Health checks:**
   - Configure proper health checks
   - Set appropriate timeouts
   - Monitor health status

2. **Restart policies:**
   ```yaml
   restart: unless-stopped
   ```

3. **Logging:**
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

4. **Backups:**
   - Automated daily backups
   - Test restore procedures
   - Store backups off-site

### Development Workflow

1. **Local development:**
   ```bash
   # Start services
   docker-compose up -d
   
   # View logs
   docker-compose logs -f app
   
   # Run tests
   docker-compose exec app pytest
   
   # Access shell
   docker-compose exec app /bin/bash
   ```

2. **Code changes:**
   - Hot-reload enabled in development
   - No need to rebuild for code changes
   - Restart service if needed: `docker-compose restart app`

3. **Database changes:**
   ```bash
   # Run migrations
   docker-compose exec app python migrations.py upgrade
   
   # Access database
   docker-compose exec postgres psql -U goose_user goose_slackbot
   ```

### Deployment Workflow

1. **Build and test:**
   ```bash
   docker build -t goose-slackbot:test -f Dockerfile.optimized --target testing .
   docker run goose-slackbot:test
   ```

2. **Build production image:**
   ```bash
   docker build -t goose-slackbot:v1.0.0 -f Dockerfile.optimized --target production .
   ```

3. **Tag and push:**
   ```bash
   docker tag goose-slackbot:v1.0.0 registry.example.com/goose-slackbot:v1.0.0
   docker push registry.example.com/goose-slackbot:v1.0.0
   ```

4. **Deploy:**
   ```bash
   docker-compose -f docker-compose.prod.yml pull
   docker-compose -f docker-compose.prod.yml up -d
   ```

5. **Verify:**
   ```bash
   docker-compose -f docker-compose.prod.yml ps
   curl http://localhost:3000/health
   ```

## Troubleshooting

### Common Issues

1. **Container won't start:**
   ```bash
   # Check logs
   docker-compose logs app
   
   # Check health
   docker inspect goose-slackbot-app
   ```

2. **Database connection errors:**
   ```bash
   # Check database is running
   docker-compose exec postgres pg_isready
   
   # Check connection string
   docker-compose exec app env | grep DATABASE_URL
   ```

3. **Port conflicts:**
   ```bash
   # Change ports in .env
   APP_PORT=8080
   POSTGRES_PORT=5433
   ```

4. **Volume permission issues:**
   ```bash
   # Fix permissions
   sudo chown -R 1000:1000 data/
   ```

### Debug Mode

Enable debug logging:
```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG

# Restart
docker-compose restart app
```

### Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker rmi goose-slackbot:latest

# Full cleanup
docker system prune -a
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Dockerfile Best Practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide
- [README.md](README.md) - Project overview
