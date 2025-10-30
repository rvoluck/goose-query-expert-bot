# 📸 Visual Slack App Setup Guide

This guide shows you exactly what you'll see at each step.

---

## 🌐 Starting Point

**URL**: https://api.slack.com/apps

**What you'll see:**
```
┌─────────────────────────────────────────────┐
│  Your Apps                    [Create New App]│
│                                               │
│  (List of existing apps or empty)            │
└─────────────────────────────────────────────┘
```

---

## 1️⃣ Create New App

**Click**: Green "Create New App" button (top right)

**Popup appears:**
```
┌─────────────────────────────────────┐
│  Create an app                      │
│                                     │
│  ○ From scratch                    │
│  ○ From an app manifest            │
│                                     │
│           [Cancel]  [Next]         │
└─────────────────────────────────────┘
```

**Choose**: "From scratch"

---

## 2️⃣ Name Your App

**Form appears:**
```
┌─────────────────────────────────────┐
│  Name app & choose workspace        │
│                                     │
│  App Name                           │
│  [Goose Query Expert            ]  │
│                                     │
│  Pick a workspace to develop       │
│  [▼ Select workspace            ]  │
│                                     │
│           [Cancel]  [Create App]   │
└─────────────────────────────────────┘
```

**Enter**:
- App Name: `Goose Query Expert`
- Workspace: Select your Block workspace

**Click**: "Create App"

---

## 3️⃣ Basic Information Page

**You'll see:**
```
┌─────────────────────────────────────────────────────┐
│  Goose Query Expert                    [Settings ▼] │
├─────────────────────────────────────────────────────┤
│  ← Back to Your Apps                                │
│                                                      │
│  [Icon]  Goose Query Expert                         │
│          Created just now                           │
│                                                      │
│  ┌─ Building Apps for Slack ─────────────────────┐ │
│  │  Add features and functionality               │ │
│  │  [Incoming Webhooks] [Slash Commands]        │ │
│  └───────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ App Credentials ──────────────────────────────┐│
│  │  Client ID: 1234567890.1234567890            ││
│  │  Client Secret: [Show]                        ││
│  │  Signing Secret: [Show] ← COPY THIS          ││
│  │  Verification Token: abcd1234                 ││
│  └───────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
```

**Action**: Click "Show" next to Signing Secret → Copy it

---

## 4️⃣ Socket Mode (Left Sidebar)

**Click**: "Socket Mode" in left sidebar

**You'll see:**
```
┌─────────────────────────────────────────────┐
│  Socket Mode                                │
│                                             │
│  Enable Socket Mode    [○ OFF]  ← Toggle ON│
│                                             │
│  Socket Mode lets your app receive         │
│  events over WebSocket connections...      │
└─────────────────────────────────────────────┘
```

**Toggle**: Switch to ON

**Popup appears:**
```
┌─────────────────────────────────────┐
│  Generate an app-level token       │
│                                     │
│  Token Name                         │
│  [goose-bot-socket              ]  │
│                                     │
│  Scopes                             │
│  [+ Add Scope]                     │
│                                     │
│           [Cancel]  [Generate]     │
└─────────────────────────────────────┘
```

**Enter**:
- Token Name: `goose-bot-socket`
- Click "+ Add Scope"
- Select: `connections:write`
- Click "Generate"

**Token appears:**
```
┌─────────────────────────────────────┐
│  Your app-level token               │
│                                     │
│  xapp-1-A01234567-1234-abcdef...   │
│                                     │
│  ⚠️  Copy this token now!          │
│  You won't be able to see it again│
│                                     │
│           [Copy]  [Done]           │
└─────────────────────────────────────┘
```

**Action**: Copy the token (starts with `xapp-`)

---

## 5️⃣ OAuth & Permissions (Left Sidebar)

**Click**: "OAuth & Permissions" in left sidebar

**You'll see:**
```
┌─────────────────────────────────────────────┐
│  OAuth & Permissions                        │
│                                             │
│  ┌─ OAuth Tokens for Your Workspace ──────┐│
│  │  [Install to Workspace]                ││
│  └─────────────────────────────────────────┘│
│                                             │
│  ┌─ Scopes ────────────────────────────────┐│
│  │  Bot Token Scopes                       ││
│  │  [+ Add an OAuth Scope]                ││
│  │                                         ││
│  │  (No scopes added yet)                 ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

**Scroll down to "Scopes" section**

**Click**: "+ Add an OAuth Scope" button

**Dropdown appears:**
```
┌─────────────────────────────────────┐
│  Search for a scope...              │
│  [                              ]   │
│                                     │
│  Popular scopes:                    │
│  • chat:write                       │
│  • channels:read                    │
│  • users:read                       │
└─────────────────────────────────────┘
```

**Add these scopes one by one:**
1. Type "app_mentions:read" → Click it
2. Type "channels:history" → Click it
3. Type "channels:read" → Click it
4. Type "chat:write" → Click it
5. Type "chat:write.public" → Click it
6. Type "commands" → Click it
7. Type "files:write" → Click it
8. Type "groups:history" → Click it
9. Type "groups:read" → Click it
10. Type "im:history" → Click it
11. Type "im:read" → Click it
12. Type "im:write" → Click it
13. Type "mpim:history" → Click it
14. Type "mpim:read" → Click it
15. Type "users:read" → Click it

**After adding scopes, you'll see:**
```
┌─────────────────────────────────────────────┐
│  Bot Token Scopes                           │
│  [+ Add an OAuth Scope]                    │
│                                             │
│  ✓ app_mentions:read                       │
│  ✓ channels:history                        │
│  ✓ channels:read                           │
│  ✓ chat:write                              │
│  ✓ chat:write.public                       │
│  ... (all 15 scopes)                       │
└─────────────────────────────────────────────┘
```

---

## 6️⃣ Install App to Workspace

**Scroll back to top of page**

**You'll see:**
```
┌─────────────────────────────────────────────┐
│  OAuth Tokens for Your Workspace           │
│                                             │
│  [Install to Workspace]  ← Click this      │
└─────────────────────────────────────────────┘
```

**Click**: "Install to Workspace"

**Authorization page appears:**
```
┌─────────────────────────────────────────────┐
│  Goose Query Expert is requesting          │
│  permission to access the Block workspace  │
│                                             │
│  This app will be able to:                 │
│  • View messages in channels               │
│  • Send messages                           │
│  • Upload files                            │
│  ... (all permissions listed)              │
│                                             │
│           [Cancel]  [Allow]                │
└─────────────────────────────────────────────┘
```

**Click**: "Allow"

**Success! You'll see:**
```
┌─────────────────────────────────────────────┐
│  OAuth Tokens for Your Workspace           │
│                                             │
│  Bot User OAuth Token                      │
│  xoxb-1234567890-1234567890-abcdef...     │
│  [Copy]  ← COPY THIS TOKEN                │
│                                             │
│  [Reinstall to Workspace]                  │
└─────────────────────────────────────────────┘
```

**Action**: Copy the Bot User OAuth Token (starts with `xoxb-`)

---

## 7️⃣ Event Subscriptions (Left Sidebar)

**Click**: "Event Subscriptions" in left sidebar

**You'll see:**
```
┌─────────────────────────────────────────────┐
│  Event Subscriptions                        │
│                                             │
│  Enable Events    [○ OFF]  ← Toggle ON     │
└─────────────────────────────────────────────┘
```

**Toggle**: Switch to ON

**Page expands:**
```
┌─────────────────────────────────────────────┐
│  Enable Events    [● ON]                   │
│                                             │
│  ┌─ Subscribe to bot events ──────────────┐│
│  │  [+ Add Bot User Event]                ││
│  │                                         ││
│  │  (No events subscribed)                ││
│  └─────────────────────────────────────────┘│
│                                             │
│  [Save Changes]                            │
└─────────────────────────────────────────────┘
```

**Click**: "+ Add Bot User Event"

**Dropdown appears:**
```
┌─────────────────────────────────────┐
│  Filter events...                   │
│  [                              ]   │
│                                     │
│  • app_mention                      │
│  • message.channels                 │
│  • message.groups                   │
└─────────────────────────────────────┘
```

**Add these events:**
1. Click "app_mention"
2. Click "+ Add Bot User Event" again
3. Click "message.channels"
4. Repeat for: message.groups, message.im, message.mpim

**After adding events:**
```
┌─────────────────────────────────────────────┐
│  Subscribe to bot events                    │
│  [+ Add Bot User Event]                    │
│                                             │
│  ✓ app_mention                             │
│  ✓ message.channels                        │
│  ✓ message.groups                          │
│  ✓ message.im                              │
│  ✓ message.mpim                            │
└─────────────────────────────────────────────┘
```

**Click**: "Save Changes" at bottom

---

## 8️⃣ App Home (Left Sidebar)

**Click**: "App Home" in left sidebar

**You'll see:**
```
┌─────────────────────────────────────────────┐
│  App Home                                   │
│                                             │
│  ┌─ Show Tabs ─────────────────────────────┐│
│  │  Home Tab         [○ OFF]              ││
│  │  Messages Tab     [○ OFF] ← Toggle ON  ││
│  └─────────────────────────────────────────┘│
│                                             │
│  ┌─ Your App's Presence in Slack ─────────┐│
│  │  Display Name (Bot Name)               ││
│  │  [Goose Query Expert              ]    ││
│  │                                         ││
│  │  Default username                      ││
│  │  [goose-bot                       ]    ││
│  └─────────────────────────────────────────┘│
└─────────────────────────────────────────────┘
```

**Toggle**: Messages Tab to ON

**Check**: "Allow users to send Slash commands..."

**Enter**:
- Display Name: `Goose Query Expert`
- Default username: `goose-bot`

---

## ✅ Verification Checklist

**Go back through each section and verify:**

```
☐ Basic Information
  ☐ Signing Secret copied

☐ Socket Mode
  ☐ Enabled (toggle is ON)
  ☐ App token copied (xapp-)

☐ OAuth & Permissions
  ☐ 15 scopes added
  ☐ App installed to workspace
  ☐ Bot token copied (xoxb-)

☐ Event Subscriptions
  ☐ Enabled (toggle is ON)
  ☐ 5 events subscribed
  ☐ Changes saved

☐ App Home
  ☐ Messages Tab enabled
  ☐ Display name set
```

---

## 🎯 Final Check

**You should have these 3 tokens:**

```
✓ SLACK_BOT_TOKEN=xoxb-...
✓ SLACK_APP_TOKEN=xapp-...
✓ SLACK_SIGNING_SECRET=...
```

---

## 🚀 Next: Setup Environment

Run the setup script:

```bash
cd /Users/rleach/goose-slackbot
./setup_env.sh
```

This will:
1. Ask for your 3 tokens
2. Generate security keys
3. Create your .env file
4. Verify configuration

---

**You're almost there! 🎉**
