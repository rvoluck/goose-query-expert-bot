# 🚀 Complete Slack App Setup Guide for Goose Query Expert Bot

## Step-by-Step Instructions

Follow these steps exactly to create your Slack app at https://api.slack.com/apps

---

## STEP 1: Create New App (2 minutes)

### 1.1 Navigate to Slack API
- Go to: **https://api.slack.com/apps**
- Sign in with your Block Slack account

### 1.2 Create App
1. Click **"Create New App"** button (green button, top right)
2. Choose **"From scratch"** (not from manifest)
3. Fill in the form:
   - **App Name**: `Goose Query Expert`
   - **Pick a workspace**: Select your Block workspace
4. Click **"Create App"**

✅ You should now see your app's Basic Information page

---

## STEP 2: Configure App Settings (3 minutes)

### 2.1 App Icon (Optional but Recommended)
1. Scroll down to **"Display Information"**
2. Upload an icon (I can help create one, or use a 🦆 emoji)
3. Add description:
   ```
   AI-powered data analysis bot that helps teams query Snowflake data using natural language. 
   Powered by Goose Query Expert.
   ```
4. Background color: `#4A90E2` (or your preference)
5. Click **"Save Changes"**

### 2.2 Get Your Signing Secret
1. Still on **"Basic Information"** page
2. Scroll to **"App Credentials"** section
3. Find **"Signing Secret"**
4. Click **"Show"** then copy it
5. **SAVE THIS**: `SLACK_SIGNING_SECRET=<your-secret>`

---

## STEP 3: Enable Socket Mode (5 minutes)

### 3.1 Navigate to Socket Mode
1. In left sidebar, click **"Socket Mode"**
2. Toggle **"Enable Socket Mode"** to ON
3. You'll see a popup: **"Generate an app-level token"**

### 3.2 Create App-Level Token
1. In the popup, enter token name: `goose-bot-socket`
2. Add scope: `connections:write`
3. Click **"Generate"**
4. **COPY THE TOKEN** (starts with `xapp-`)
5. **SAVE THIS**: `SLACK_APP_TOKEN=xapp-1-...`
6. Click **"Done"**

⚠️ **IMPORTANT**: You can't see this token again! Save it now.

---

## STEP 4: Configure OAuth & Permissions (5 minutes)

### 4.1 Navigate to OAuth
1. In left sidebar, click **"OAuth & Permissions"**

### 4.2 Add Bot Token Scopes
Scroll down to **"Scopes"** → **"Bot Token Scopes"**

Click **"Add an OAuth Scope"** and add these scopes one by one:

**Required Scopes:**
- `app_mentions:read` - Read messages that mention the bot
- `channels:history` - View messages in public channels
- `channels:read` - View basic channel info
- `chat:write` - Send messages
- `chat:write.public` - Send messages to channels without joining
- `commands` - Add slash commands
- `files:write` - Upload files (for CSV results)
- `groups:history` - View messages in private channels
- `groups:read` - View basic private channel info
- `im:history` - View messages in direct messages
- `im:read` - View basic DM info
- `im:write` - Send DMs
- `mpim:history` - View messages in group DMs
- `mpim:read` - View basic group DM info
- `users:read` - View user information
- `reactions:read` - View reactions (optional, for interactive features)

### 4.3 Install App to Workspace
1. Scroll back to top of **"OAuth & Permissions"** page
2. Click **"Install to Workspace"** button
3. Review permissions
4. Click **"Allow"**
5. **COPY THE BOT TOKEN** (starts with `xoxb-`)
6. **SAVE THIS**: `SLACK_BOT_TOKEN=xoxb-...`

---

## STEP 5: Enable Events (3 minutes)

### 5.1 Navigate to Event Subscriptions
1. In left sidebar, click **"Event Subscriptions"**
2. Toggle **"Enable Events"** to ON

### 5.2 Subscribe to Bot Events
Scroll down to **"Subscribe to bot events"**

Click **"Add Bot User Event"** and add these events:

**Required Events:**
- `app_mention` - Bot is mentioned
- `message.channels` - Messages in public channels
- `message.groups` - Messages in private channels  
- `message.im` - Direct messages
- `message.mpim` - Group direct messages

3. Click **"Save Changes"** at bottom

---

## STEP 6: Add Slash Command (Optional, 2 minutes)

### 6.1 Navigate to Slash Commands
1. In left sidebar, click **"Slash Commands"**
2. Click **"Create New Command"**

### 6.2 Configure Command
Fill in the form:
- **Command**: `/goose-query`
- **Request URL**: `https://your-domain.com/slack/commands` (we'll update this later)
- **Short Description**: `Ask Goose Query Expert a data question`
- **Usage Hint**: `What was our revenue last month?`

3. Click **"Save"**

**Note**: For Socket Mode, the Request URL isn't used, but Slack requires it. You can use a placeholder for now.

---

## STEP 7: Configure App Home (Optional, 2 minutes)

### 7.1 Navigate to App Home
1. In left sidebar, click **"App Home"**

### 7.2 Enable Home Tab (Optional)
- Toggle **"Home Tab"** ON if you want a bot home page

### 7.3 Enable Messages Tab
- Toggle **"Messages Tab"** ON
- Check **"Allow users to send Slash commands and messages from the messages tab"**

### 7.4 Set Display Name
- **Display Name**: `Goose Query Expert`
- **Default Username**: `goose-bot`

---

## STEP 8: Verify Your Configuration

### 8.1 Check You Have All Three Tokens

You should have saved:

```bash
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_SIGNING_SECRET=...
```

### 8.2 Verify Scopes
Go back to **"OAuth & Permissions"** and verify you have all the scopes listed above.

### 8.3 Verify Events
Go back to **"Event Subscriptions"** and verify all events are subscribed.

---

## STEP 9: Create Your .env File

Now create your environment file:

```bash
cd /Users/rleach/goose-slackbot
cp env.example .env
```

Edit `.env` and add your tokens:

```bash
# Slack Configuration (REQUIRED)
SLACK_BOT_TOKEN=xoxb-YOUR-ACTUAL-TOKEN-HERE
SLACK_APP_TOKEN=xapp-YOUR-ACTUAL-TOKEN-HERE
SLACK_SIGNING_SECRET=YOUR-ACTUAL-SECRET-HERE

# Slack Admin Channel (Optional)
SLACK_ADMIN_CHANNEL=#data-team-alerts

# Goose Integration (REQUIRED)
GOOSE_MCP_SERVER_URL=http://localhost:8000
GOOSE_MCP_TIMEOUT=300
GOOSE_MAX_CONCURRENT_QUERIES=10

# Database Configuration (Use SQLite for testing)
DATABASE_URL=sqlite:///./slackbot.db
REDIS_URL=redis://localhost:6379/0

# Security Configuration (REQUIRED - Generate these)
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-to-random-string
ENCRYPTION_KEY=your-32-byte-encryption-key-change-this

# Application Configuration
DEBUG=true
ENVIRONMENT=development
LOG_LEVEL=INFO
MOCK_MODE=true

# Feature Flags
ENABLE_QUERY_HISTORY=true
ENABLE_QUERY_SHARING=true
ENABLE_INTERACTIVE_BUTTONS=true
ENABLE_FILE_UPLOADS=true
```

---

## STEP 10: Generate Security Keys

Generate secure random keys:

```bash
# Generate JWT secret (run in terminal)
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate encryption key (run in terminal)
python3 -c "import secrets; print('ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
```

Copy these into your `.env` file.

---

## STEP 11: Test Your Configuration

Test that everything is configured correctly:

```bash
cd /Users/rleach/goose-slackbot

# Verify environment variables
python3 -c "from config import settings; print('✅ Config loaded successfully')"
```

---

## STEP 12: Invite Bot to Channels

Once your bot is running:

1. Go to any Slack channel
2. Type: `/invite @Goose Query Expert`
3. Or mention the bot: `@Goose Query Expert`

---

## 🎯 Quick Reference Card

### Your Three Tokens:

| Token | Starts With | Where to Find |
|-------|-------------|---------------|
| Bot Token | `xoxb-` | OAuth & Permissions → Install App |
| App Token | `xapp-` | Socket Mode → Generate Token |
| Signing Secret | (random) | Basic Information → App Credentials |

### Required Scopes:
```
app_mentions:read, channels:history, channels:read, chat:write,
chat:write.public, commands, files:write, groups:history, groups:read,
im:history, im:read, im:write, mpim:history, mpim:read, users:read
```

### Required Events:
```
app_mention, message.channels, message.groups, message.im, message.mpim
```

---

## 🚨 Troubleshooting

### "Invalid Token" Error
- Make sure you copied the entire token
- Tokens should not have spaces or line breaks
- Bot token starts with `xoxb-`
- App token starts with `xapp-`

### "Missing Scopes" Error
- Go back to OAuth & Permissions
- Add any missing scopes
- Reinstall the app to workspace

### "Events Not Working"
- Make sure Socket Mode is enabled
- Verify all events are subscribed
- Check that the bot is invited to the channel

### "Can't Send Messages"
- Verify `chat:write` scope is added
- Make sure app is installed to workspace
- Check bot is invited to the channel

---

## 📞 Need Help?

If you get stuck:

1. Check the Slack API docs: https://api.slack.com/docs
2. Review the troubleshooting section above
3. Check the bot logs for error messages
4. Verify all tokens are correct in `.env`

---

## ✅ Completion Checklist

Before moving to deployment, verify:

- [ ] App created in Slack workspace
- [ ] Socket Mode enabled with app token
- [ ] All OAuth scopes added (15 scopes)
- [ ] App installed to workspace with bot token
- [ ] All events subscribed (5 events)
- [ ] Signing secret copied
- [ ] All three tokens saved in `.env`
- [ ] Security keys generated
- [ ] Configuration tested successfully

---

## 🚀 Next Steps

Once you complete this setup:

1. **Test locally**: Run `python3 slack_bot.py`
2. **Invite bot**: Add to a test channel
3. **Ask a question**: `@Goose Query Expert What was our revenue last month?`
4. **See it work**: Watch the magic happen!

---

**Ready to create your app? Let's do this! 🎉**
