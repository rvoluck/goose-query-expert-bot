# 🚀 Square Kubernetes Deployment Guide

Complete guide to deploy Goose Query Expert Slackbot to Square's internal Kubernetes infrastructure.

---

## 📋 **PREREQUISITES**

### **1. Tools Required**
```bash
# Install kubectl
brew install kubectl

# Install Docker
brew install --cask docker

# Verify installations
kubectl version --client
docker --version
```

### **2. Square Access Required**
- [ ] Access to Square's Kubernetes cluster
- [ ] kubectl configured with Square credentials
- [ ] Access to Square's container registry
- [ ] Namespace/project created in k8s

### **3. Credentials Needed**
- [ ] Slack Bot Token
- [ ] Slack App Token  
- [ ] Slack Signing Secret
- [ ] Slack Client ID & Secret
- [ ] Snowflake credentials (if using)

---

## 🏗️ **DEPLOYMENT STEPS**

### **STEP 1: Build Docker Image**

```bash
cd /Users/rleach/goose-slackbot

# Build the image
docker build -t goose-slackbot:latest -f Dockerfile.optimized .

# Tag for Square's registry (UPDATE WITH ACTUAL REGISTRY URL)
docker tag goose-slackbot:latest registry.sqprod.co/goose-slackbot:latest

# Push to registry
docker push registry.sqprod.co/goose-slackbot:latest
```

**Note:** Replace `registry.sqprod.co` with Square's actual container registry URL.

---

### **STEP 2: Update Kubernetes Manifests**

Edit `k8s/deployment-complete.yaml` and update:

#### **A. Container Image URL (Line ~250)**
```yaml
containers:
- name: app
  image: registry.sqprod.co/goose-slackbot:latest  # UPDATE THIS
```

#### **B. Secrets (Lines ~95-130)**
Update with your actual credentials:
```yaml
stringData:
  # Slack Credentials
  SLACK_BOT_TOKEN: "xoxb-YOUR-ACTUAL-TOKEN"
  SLACK_CLIENT_ID: "YOUR-CLIENT-ID"
  SLACK_CLIENT_SECRET: "YOUR-CLIENT-SECRET"
  SLACK_SIGNING_SECRET: "YOUR-SIGNING-SECRET"
  SLACK_APP_ID: "YOUR-APP-ID"
  SLACK_OAUTH_REDIRECT_URL: "https://your-domain.sqprod.co/slack/oauth_redirect"
  
  # Security Keys (generate new ones)
  JWT_SECRET_KEY: "$(openssl rand -base64 32)"
  ENCRYPTION_KEY: "$(openssl rand -base64 32)"
  
  # Database (auto-configured if using in-cluster postgres)
  DATABASE_URL: "postgresql://goose_user:goose_password@postgres-service:5432/goose_slackbot"
  
  # Redis (auto-configured if using in-cluster redis)
  REDIS_URL: "redis://:redis_password@redis-service:6379/0"
```

#### **C. Ingress/Load Balancer**
Create an ingress for external access:

```yaml
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: goose-slackbot-ingress
  namespace: goose-slackbot
  annotations:
    # UPDATE WITH SQUARE'S INGRESS ANNOTATIONS
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - goose-slackbot.sqprod.co  # UPDATE WITH YOUR DOMAIN
    secretName: goose-slackbot-tls
  rules:
  - host: goose-slackbot.sqprod.co  # UPDATE WITH YOUR DOMAIN
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: goose-slackbot-service
            port:
              number: 3000
```

---

### **STEP 3: Deploy to Kubernetes**

```bash
# Set your kubectl context (if needed)
kubectl config use-context square-prod  # UPDATE WITH ACTUAL CONTEXT

# Create namespace
kubectl apply -f k8s/deployment-complete.yaml

# Verify deployment
kubectl get pods -n goose-slackbot
kubectl get services -n goose-slackbot
kubectl get ingress -n goose-slackbot

# Check logs
kubectl logs -f deployment/goose-slackbot-app -n goose-slackbot

# Check app status
kubectl describe deployment goose-slackbot-app -n goose-slackbot
```

---

### **STEP 4: Verify Deployment**

```bash
# Get the external URL
kubectl get ingress -n goose-slackbot

# Test health endpoint
curl https://goose-slackbot.sqprod.co/health

# Should return:
# {"status": "healthy", "service": "goose-query-expert-slackbot"}
```

---

### **STEP 5: Update Slack App URLs**

Once deployed, update your Slack app with the new URLs:

1. **Event Subscriptions URL:**
   ```
   https://goose-slackbot.sqprod.co/slack/events
   ```

2. **Interactivity URL:**
   ```
   https://goose-slackbot.sqprod.co/slack/events
   ```

3. **OAuth Redirect URL:**
   ```
   https://goose-slackbot.sqprod.co/slack/oauth_redirect
   ```

---

## 🔧 **TROUBLESHOOTING**

### **Pods Not Starting**
```bash
# Check pod status
kubectl get pods -n goose-slackbot

# View pod logs
kubectl logs <pod-name> -n goose-slackbot

# Describe pod for events
kubectl describe pod <pod-name> -n goose-slackbot
```

### **Database Connection Issues**
```bash
# Check if postgres is running
kubectl get pods -n goose-slackbot | grep postgres

# Test database connection
kubectl exec -it deployment/goose-slackbot-app -n goose-slackbot -- \
  python -c "import psycopg2; conn = psycopg2.connect('postgresql://goose_user:goose_password@postgres-service:5432/goose_slackbot'); print('Connected!')"
```

### **Image Pull Errors**
```bash
# Check if image exists in registry
docker pull registry.sqprod.co/goose-slackbot:latest

# Verify image pull secrets (if needed)
kubectl get secrets -n goose-slackbot
```

---

## 📊 **MONITORING**

### **View Logs**
```bash
# App logs
kubectl logs -f deployment/goose-slackbot-app -n goose-slackbot

# Postgres logs
kubectl logs -f deployment/postgres -n goose-slackbot

# Redis logs
kubectl logs -f deployment/redis -n goose-slackbot
```

### **Check Metrics**
```bash
# Pod metrics
kubectl top pods -n goose-slackbot

# Node metrics
kubectl top nodes
```

### **Access Prometheus Metrics**
```bash
# Port forward to metrics endpoint
kubectl port-forward deployment/goose-slackbot-app 9090:9090 -n goose-slackbot

# Access metrics at: http://localhost:9090/metrics
```

---

## 🔄 **UPDATES & ROLLBACKS**

### **Deploy New Version**
```bash
# Build new image
docker build -t goose-slackbot:v2 .
docker tag goose-slackbot:v2 registry.sqprod.co/goose-slackbot:v2
docker push registry.sqprod.co/goose-slackbot:v2

# Update deployment
kubectl set image deployment/goose-slackbot-app app=registry.sqprod.co/goose-slackbot:v2 -n goose-slackbot

# Watch rollout
kubectl rollout status deployment/goose-slackbot-app -n goose-slackbot
```

### **Rollback**
```bash
# View rollout history
kubectl rollout history deployment/goose-slackbot-app -n goose-slackbot

# Rollback to previous version
kubectl rollout undo deployment/goose-slackbot-app -n goose-slackbot

# Rollback to specific revision
kubectl rollout undo deployment/goose-slackbot-app --to-revision=2 -n goose-slackbot
```

---

## 🗑️ **CLEANUP**

```bash
# Delete entire deployment
kubectl delete namespace goose-slackbot

# Or delete specific resources
kubectl delete deployment goose-slackbot-app -n goose-slackbot
kubectl delete service goose-slackbot-service -n goose-slackbot
```

---

## 📞 **NEED HELP?**

### **Square Internal Resources**
- Internal k8s documentation: [UPDATE WITH LINK]
- Container registry docs: [UPDATE WITH LINK]
- DevOps Slack channel: [UPDATE WITH CHANNEL]
- On-call engineer: [UPDATE WITH CONTACT]

### **Common Issues**
1. **No kubectl access** → Request access from DevOps team
2. **No registry access** → Request credentials from Security team
3. **No namespace** → Request namespace creation from Platform team
4. **Ingress not working** → Check with Network team

---

## ✅ **DEPLOYMENT CHECKLIST**

- [ ] kubectl installed and configured
- [ ] Docker installed
- [ ] Access to Square's k8s cluster
- [ ] Access to container registry
- [ ] Slack credentials ready
- [ ] Docker image built and pushed
- [ ] Kubernetes manifests updated
- [ ] Secrets configured
- [ ] Deployed to k8s
- [ ] Pods running successfully
- [ ] Health check passing
- [ ] Ingress configured
- [ ] Slack app URLs updated
- [ ] Tested in Slack channel

---

## 🎯 **NEXT STEPS AFTER DEPLOYMENT**

1. **Test the bot in Slack:**
   - Invite bot to a test channel
   - @mention the bot with a query
   - Test slash command: `/goose-query`

2. **Monitor for issues:**
   - Watch logs for errors
   - Check metrics dashboard
   - Set up alerts

3. **Share with team:**
   - Send installation link to security team
   - Document usage instructions
   - Create user guide

---

**Deployment Status:** Ready to deploy once Square k8s access is configured! 🚀
