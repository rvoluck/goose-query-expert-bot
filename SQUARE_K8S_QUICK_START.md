# 🚀 Square K8s Quick Start

**5-minute guide to deploy your Slackbot to Square's Kubernetes**

---

## ⚡ **FASTEST PATH TO DEPLOYMENT**

### **Option 1: Use the Interactive Script** (Recommended)

```bash
cd /Users/rleach/goose-slackbot
./scripts/deploy-square-k8s.sh
```

Follow the prompts to:
1. Check k8s access
2. Build & push Docker image
3. Deploy to Kubernetes
4. Get Slack URLs

---

### **Option 2: Manual Steps** (If you know what you're doing)

```bash
# 1. Set kubectl context
kubectl config use-context square-prod  # Replace with your context

# 2. Build & push image
REGISTRY="registry.sqprod.co"  # Replace with actual registry
docker build -t goose-slackbot:latest -f Dockerfile.optimized .
docker tag goose-slackbot:latest $REGISTRY/goose-slackbot:latest
docker push $REGISTRY/goose-slackbot:latest

# 3. Update manifests with your registry URL
sed -i '' "s|image: goose-slackbot:latest|image: $REGISTRY/goose-slackbot:latest|g" k8s/deployment-complete.yaml

# 4. Update secrets in k8s/deployment-complete.yaml
# Edit lines 95-130 with your Slack credentials

# 5. Deploy
kubectl apply -f k8s/deployment-complete.yaml

# 6. Check status
kubectl get pods -n goose-slackbot
kubectl get ingress -n goose-slackbot

# 7. Get your URL
kubectl get ingress -n goose-slackbot -o jsonpath='{.items[0].spec.rules[0].host}'
```

---

## 🆘 **NEED HELP?**

### **Don't have kubectl access?**
Contact Square DevOps team to request:
- Kubernetes cluster access
- kubectl credentials
- Namespace creation

### **Don't have Docker?**
```bash
brew install --cask docker
```

### **Don't know your registry URL?**
Ask in Square's internal DevOps Slack channel or check internal docs.

### **Don't know your kubectl context?**
```bash
kubectl config get-contexts
```

---

## 📋 **WHAT YOU NEED**

Before starting, gather:

1. **Square Access:**
   - [ ] kubectl configured for Square k8s
   - [ ] Container registry credentials
   - [ ] Namespace/project name

2. **Slack Credentials:**
   - [ ] Bot Token (`xoxb-...`)
   - [ ] Client ID
   - [ ] Client Secret
   - [ ] Signing Secret
   - [ ] App ID

3. **Domain:**
   - [ ] Your app's domain (e.g., `goose-slackbot.sqprod.co`)

---

## ✅ **AFTER DEPLOYMENT**

Once deployed, update your Slack app:

1. Go to https://api.slack.com/apps
2. Click your app
3. Update these URLs (replace `YOUR-DOMAIN`):
   - **Event Subscriptions:** `https://YOUR-DOMAIN/slack/events`
   - **Interactivity:** `https://YOUR-DOMAIN/slack/events`
   - **OAuth Redirect:** `https://YOUR-DOMAIN/slack/oauth_redirect`

4. Test health endpoint: `https://YOUR-DOMAIN/health`

5. Send shareable URL to security team for approval

---

## 🎯 **TROUBLESHOOTING**

### **Pods not starting?**
```bash
kubectl logs -f deployment/goose-slackbot-app -n goose-slackbot
kubectl describe pod <pod-name> -n goose-slackbot
```

### **Can't access cluster?**
```bash
kubectl cluster-info
# If this fails, you need to authenticate or request access
```

### **Image pull errors?**
Check if you have registry access:
```bash
docker login registry.sqprod.co  # Replace with actual registry
```

---

## 📚 **FULL DOCUMENTATION**

For detailed instructions, see:
- [SQUARE_K8S_DEPLOYMENT.md](./SQUARE_K8S_DEPLOYMENT.md) - Complete deployment guide
- [DEPLOYMENT.md](./DEPLOYMENT.md) - General deployment options
- [k8s/](./k8s/) - Kubernetes manifests

---

**Ready to deploy? Run the script!** 🚀

```bash
./scripts/deploy-square-k8s.sh
```
