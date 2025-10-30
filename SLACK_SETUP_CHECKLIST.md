# ✅ Slack App Setup Checklist

Print this out or keep it open while you create your app!

---

## 🎯 Goal
Create a Slack app for Goose Query Expert bot and get 3 credentials

---

## 📋 Step-by-Step Checklist

### ☐ STEP 1: Create App (2 min)
- [ ] Go to https://api.slack.com/apps
- [ ] Click "Create New App"
- [ ] Choose "From scratch"
- [ ] Name: `Goose Query Expert`
- [ ] Select Block workspace
- [ ] Click "Create App"

### ☐ STEP 2: Get Signing Secret (1 min)
- [ ] On "Basic Information" page
- [ ] Scroll to "App Credentials"
- [ ] Click "Show" on Signing Secret
- [ ] Copy and save: `SLACK_SIGNING_SECRET=_______________`

### ☐ STEP 3: Enable Socket Mode (2 min)
- [ ] Click "Socket Mode" in left sidebar
- [ ] Toggle "Enable Socket Mode" ON
- [ ] Token name: `goose-bot-socket`
- [ ] Add scope: `connections:write`
- [ ] Click "Generate"
- [ ] Copy and save: `SLACK_APP_TOKEN=xapp-_______________`

### ☐ STEP 4: Add OAuth Scopes (3 min)
- [ ] Click "OAuth & Permissions" in left sidebar
- [ ] Scroll to "Bot Token Scopes"
- [ ] Add these 15 scopes:
  - [ ] `app_mentions:read`
  - [ ] `channels:history`
  - [ ] `channels:read`
  - [ ] `chat:write`
  - [ ] `chat:write.public`
  - [ ] `commands`
  - [ ] `files:write`
  - [ ] `groups:history`
  - [ ] `groups:read`
  - [ ] `im:history`
  - [ ] `im:read`
  - [ ] `im:write`
  - [ ] `mpim:history`
  - [ ] `mpim:read`
  - [ ] `users:read`

### ☐ STEP 5: Install App (1 min)
- [ ] Scroll to top of "OAuth & Permissions" page
- [ ] Click "Install to Workspace"
- [ ] Click "Allow"
- [ ] Copy and save: `SLACK_BOT_TOKEN=xoxb-_______________`

### ☐ STEP 6: Enable Events (2 min)
- [ ] Click "Event Subscriptions" in left sidebar
- [ ] Toggle "Enable Events" ON
- [ ] Scroll to "Subscribe to bot events"
- [ ] Add these 5 events:
  - [ ] `app_mention`
  - [ ] `message.channels`
  - [ ] `message.groups`
  - [ ] `message.im`
  - [ ] `message.mpim`
- [ ] Click "Save Changes"

### ☐ STEP 7: Configure App Home (1 min)
- [ ] Click "App Home" in left sidebar
- [ ] Toggle "Messages Tab" ON
- [ ] Check "Allow users to send Slash commands..."
- [ ] Display Name: `Goose Query Expert`
- [ ] Default Username: `goose-bot`

### ☐ STEP 8: Verify Configuration (2 min)
- [ ] I have all 3 tokens saved
- [ ] All 15 scopes are added
- [ ] All 5 events are subscribed
- [ ] Socket Mode is enabled

---

## 📝 Your Credentials

Write your tokens here (or in a secure password manager):

```
SLACK_BOT_TOKEN=xoxb-

SLACK_APP_TOKEN=xapp-

SLACK_SIGNING_SECRET=
```

---

## ⏱️ Total Time: ~15 minutes

---

## 🚀 After Completion

1. Create `.env` file with your tokens
2. Generate security keys
3. Run the bot locally
4. Test in Slack!

See `SLACK_APP_SETUP_GUIDE.md` for detailed instructions.

---

## ❓ Stuck?

- **Can't find a setting?** Use the search bar in Slack API portal
- **Missing a scope?** Go to OAuth & Permissions → Bot Token Scopes
- **Events not working?** Make sure Socket Mode is enabled
- **Need help?** Check TROUBLESHOOTING.md

---

**You've got this! 💪**
