# Quick Start Guide - Goose Slackbot Deployment

Get your Goose Slackbot up and running in minutes!

## 🚀 Quick Start (5 Minutes)

### Option 1: Using Makefile (Recommended)

```bash
# 1. Setup environment
make setup

# 2. Edit .env file with your Slack credentials
vim .env

# 3. Deploy
make deploy-dev

# 4. Check status
make health
```

### Option 2: Using Scripts

```bash
# 1. Setup environment
./scripts/setup-env.sh

# 2. Edit .env file with your Slack credentials
vim .env

# 3. Deploy
./scripts/deploy-docker.sh deploy dev

# 4. Check status
./scripts/deploy-docker.sh health
```

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ Docker (20.10+)
- ✅ Docker Compose (2.0+)
- ✅ Python 3.11+ (for local development)
- ✅ Slack App credentials (Bot Token, App Token, Signing Secret)

## 🔑 Required Credentials

Get these from your Slack App configuration at https://api.slack.com/apps:

1. **SLACK_BOT_TOKEN**: Starts with `xoxb-`
2. **SLACK_APP_TOKEN**: Starts with `xapp-`
3. **SLACK_SIGNING_SECRET**: Your app's signing secret

## 📝 Step-by-Step Setup

### Step 1: Clone and Setup

```bash
cd /Users/rleach/goose-slackbot

# Run setup script
make setup
# or
./scripts/setup-env.sh
```

This will:
- Create `.env` file from template
- Generate secure random secrets
- Create necessary directories
- Setup Python virtual environment

### Step 2: Configure Environment

Edit the `.env` file:

```bash
vim .env
```

Update these required values:

```bash
# Slack Configuration (REQUIRED)
SLACK_BOT_TOKEN=xoxb-your-actual-token-here
SLACK_APP_TOKEN=xapp-your-actual-token-here
SLACK_SIGNING_SECRET=your-actual-signing-secret-here

# Optional: Admin channel for notifications
SLACK_ADMIN_CHANNEL=C01234567

# Optional: Snowflake configuration (if using)
SNOWFLAKE_ACCOUNT=your-account
SNOWFLAKE_USER=your-user
SNOWFLAKE_PASSWORD=your-password
```

**Note:** Security keys (JWT_SECRET_KEY, ENCRYPTION_KEY) and database passwords are auto-generated.

### Step 3: Deploy

#### Development Deployment

```bash
make deploy-dev
# or
./scripts/deploy-docker.sh deploy dev
```

This starts:
- ✅ Application with hot-reload
- ✅ PostgreSQL database
- ✅ Redis cache
- ✅ Health monitoring

#### Production Deployment

```bash
make deploy-prod
# or
./scripts/deploy-docker.sh deploy prod
```

This adds:
- ✅ Prometheus monitoring
- ✅ Grafana dashboards
- ✅ AlertManager
- ✅ Automated backups
- ✅ Resource limits

### Step 4: Verify Deployment

```bash
# Check health
make health

# View status
make status

# View logs
make logs-app
```

## 🌐 Access Your Application

After deployment, access:

| Service | URL | Credentials |
|---------|-----|-------------|
| **Application** | http://localhost:3000 | - |
| **Health Check** | http://localhost:3000/health | - |
| **Metrics** | http://localhost:9090 | - |
| **Grafana** | http://localhost:3001 | admin/admin |
| **Prometheus** | http://localhost:9091 | - |

## 🎯 Common Commands

### Using Makefile

```bash
# Deployment
make deploy-dev          # Deploy development
make deploy-prod         # Deploy production
make up                  # Start services
make down                # Stop services
make restart             # Restart services

# Monitoring
make health              # Run health checks
make status              # Show status
make logs                # View all logs
make logs-app            # View app logs
make logs-db             # View database logs

# Database
make db-migrate          # Run migrations
make backup              # Backup database
make restore BACKUP=file # Restore database

# Development
make test                # Run tests
make lint                # Run linting
make format              # Format code

# Cleanup
make clean               # Clean temp files
make clean-docker        # Remove containers
```

### Using Scripts

```bash
# Deployment
./scripts/deploy-docker.sh deploy dev
./scripts/deploy-docker.sh deploy prod
./scripts/deploy-docker.sh start
./scripts/deploy-docker.sh stop
./scripts/deploy-docker.sh restart

# Monitoring
./scripts/deploy-docker.sh health
./scripts/deploy-docker.sh status
./scripts/deploy-docker.sh logs app

# Database
./scripts/deploy-docker.sh backup
./scripts/deploy-docker.sh restore backup.sql
```

## 🐛 Troubleshooting

### Issue: Container won't start

```bash
# Check logs
make logs-app

# Check environment
docker-compose exec app env | grep SLACK
```

### Issue: Database connection error

```bash
# Check database
docker-compose exec postgres pg_isready -U goose_user

# Verify connection string
echo $DATABASE_URL
```

### Issue: Slack API errors

```bash
# Verify tokens
# - Bot token should start with xoxb-
# - App token should start with xapp-
# - Check token scopes in Slack app settings
```

### Issue: Port already in use

```bash
# Change ports in .env
APP_PORT=8080
POSTGRES_PORT=5433
REDIS_PORT=6380

# Restart
make restart
```

## 📊 Monitoring Your Application

### View Metrics

```bash
# Open Grafana
make grafana
# or
open http://localhost:3001

# Login: admin/admin
```

### Check Health

```bash
# Quick health check
curl http://localhost:3000/health

# Detailed health check
make health-check

# View metrics
curl http://localhost:9090/metrics
```

### View Logs

```bash
# All logs
make logs

# Application logs only
make logs-app

# Follow logs
docker-compose logs -f app
```

## 🔄 Updates and Maintenance

### Update Application

```bash
# Pull latest code
git pull

# Rebuild and restart
make down
make deploy-dev
```

### Backup Database

```bash
# Create backup
make backup

# Backups are stored in ./backups/
ls -lh backups/
```

### Restore Database

```bash
# Restore from backup
make restore BACKUP=backups/backup_20231028_120000.sql
```

## 🚢 Kubernetes Deployment

### Deploy to Kubernetes

```bash
# Full deployment
make k8s-deploy
# or
./scripts/deploy-k8s.sh deploy

# Check status
make k8s-status

# View logs
make k8s-logs

# Port forward to access locally
make k8s-port-forward
```

### Scale Application

```bash
# Scale to 5 replicas
make k8s-scale REPLICAS=5

# Check scaling
kubectl get pods -n goose-slackbot
```

## 📚 Additional Documentation

For more detailed information, see:

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide
- **[DOCKER_README.md](DOCKER_README.md)** - Docker configuration details
- **[DEPLOYMENT_FILES_SUMMARY.md](DEPLOYMENT_FILES_SUMMARY.md)** - All deployment files
- **[README.md](README.md)** - Project overview
- **[ADMIN_GUIDE.md](ADMIN_GUIDE.md)** - Administration guide
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Detailed troubleshooting

## 🆘 Getting Help

### Check Documentation

```bash
# View available make commands
make help

# View deployment script help
./scripts/deploy-docker.sh help
./scripts/deploy-k8s.sh help
```

### Debug Mode

```bash
# Enable debug logging
# In .env file:
DEBUG=true
LOG_LEVEL=DEBUG

# Restart application
make restart

# View detailed logs
make logs-app
```

### Common Solutions

1. **Reset everything:**
   ```bash
   make clean-docker
   make deploy-dev
   ```

2. **Check service health:**
   ```bash
   make health
   docker-compose ps
   ```

3. **Access container shell:**
   ```bash
   make shell
   # or
   docker-compose exec app /bin/bash
   ```

4. **Check database:**
   ```bash
   make db-shell
   # or
   docker-compose exec postgres psql -U goose_user goose_slackbot
   ```

## ✅ Verification Checklist

After deployment, verify:

- [ ] Application is running: `curl http://localhost:3000/health`
- [ ] Database is accessible: `docker-compose exec postgres pg_isready`
- [ ] Redis is running: `docker-compose exec redis redis-cli ping`
- [ ] Slack bot responds in Slack
- [ ] Metrics are being collected: `curl http://localhost:9090/metrics`
- [ ] Logs are being written: `make logs-app`

## 🎉 Success!

Your Goose Slackbot is now running! 

### Next Steps:

1. **Test in Slack**: Send a message to your bot
2. **Monitor**: Check Grafana dashboards at http://localhost:3001
3. **Customize**: Adjust settings in `.env` file
4. **Scale**: Add more replicas if needed
5. **Secure**: Review security settings for production

### Quick Commands Reference

```bash
# Start
make deploy-dev

# Stop
make down

# Restart
make restart

# Logs
make logs-app

# Health
make health

# Backup
make backup

# Help
make help
```

## 📞 Support

For issues or questions:
1. Check logs: `make logs-app`
2. Run health checks: `make health`
3. Review documentation in this repository
4. Check monitoring dashboards

---

**Happy Deploying! 🚀**
