# 🚀 START HERE - Deploy Your Slackbot

## Quick Navigation

**New to this?** → Follow the steps below in order

**Just need credentials?** → Jump to Step 2

**Already have tokens?** → Jump to Step 3

---

## 📋 What You Need

- [ ] Access to Block's Slack workspace
- [ ] Permission to create Slack apps (may need admin approval)
- [ ] 15 minutes of time
- [ ] This computer (no Docker needed for basic setup)

---

## 🎯 Three Simple Steps

### **Step 1: See the Demo** (2 minutes)

See how it works without any setup:

```bash
cd /Users/rleach/goose-slackbot
python3 mock_demo.py
```

Choose option 6 to see everything!

---

### **Step 2: Create Slack App** (15 minutes)

**Choose your guide:**

📸 **Visual learner?**
→ Open `VISUAL_SETUP_GUIDE.md` (screenshots and visuals)

📝 **Step-by-step instructions?**
→ Open `SLACK_APP_SETUP_GUIDE.md` (detailed guide)

✅ **Just need a checklist?**
→ Open `SLACK_SETUP_CHECKLIST.md` (quick checklist)

**Go to**: https://api.slack.com/apps

**You'll get 3 tokens:**
- `SLACK_BOT_TOKEN` (starts with `xoxb-`)
- `SLACK_APP_TOKEN` (starts with `xapp-`)
- `SLACK_SIGNING_SECRET`

---

### **Step 3: Setup & Deploy** (5 minutes)

Once you have your tokens:

```bash
cd /Users/rleach/goose-slackbot

# Run the setup script
./setup_env.sh

# It will ask for:
# 1. Your 3 Slack tokens
# 2. Deployment mode (choose option 1 for easy start)
# 3. Goose configuration (can use mock mode)

# Setup creates your .env file automatically!
```

---

### **Step 4: Start the Bot** (1 minute)

```bash
# Install dependencies (first time only)
python3 -m venv venv
source venv/bin/activate
pip install slack-bolt slack-sdk python-dotenv

# Start the bot
python3 slack_bot.py
```

You should see:
```
✅ Configuration loaded successfully
✅ Slack bot initialized
🚀 Bot is running...
```

---

### **Step 5: Test in Slack** (2 minutes)

1. **Open Slack** (Block workspace)

2. **Go to any channel** (or create a test channel)

3. **Invite the bot**:
   ```
   /invite @Goose Query Expert
   ```

4. **Ask a question**:
   ```
   @Goose Query Expert What was our revenue last month?
   ```

5. **Watch the magic!** 🎉

---

## 🆘 Troubleshooting

### "Can't create Slack app"
- You may need admin approval
- Contact your Slack workspace admin
- Show them this documentation

### "Setup script fails"
- Make sure you're in the right directory
- Run: `cd /Users/rleach/goose-slackbot`
- Make script executable: `chmod +x setup_env.sh`

### "Bot doesn't respond"
- Check bot is running (see Step 4)
- Make sure bot is invited to channel
- Verify tokens in `.env` are correct
- Check for errors in terminal

### "Import errors"
- Make sure virtual environment is activated
- Run: `source venv/bin/activate`
- Install dependencies: `pip install slack-bolt slack-sdk python-dotenv`

---

## 📚 Full Documentation

**Setup Guides:**
- `VISUAL_SETUP_GUIDE.md` - Visual walkthrough with screenshots
- `SLACK_APP_SETUP_GUIDE.md` - Complete detailed instructions
- `SLACK_SETUP_CHECKLIST.md` - Quick checklist format
- `QUICK_START.md` - 15-minute quick start

**Usage Guides:**
- `USER_MANUAL.md` - How to use the bot
- `ADMIN_GUIDE.md` - Managing users and permissions
- `FAQ.md` - Common questions

**Technical Docs:**
- `README.md` - Project overview
- `API.md` - API documentation
- `DEPLOYMENT.md` - Production deployment
- `TROUBLESHOOTING.md` - Problem solving

**Reference:**
- `FINAL_SUMMARY.md` - Complete project summary
- `PROJECT_COMPLETE.md` - What was built
- `DOCUMENTATION_INDEX.md` - All documentation

---

## 🎯 Quick Commands Reference

```bash
# See the demo
python3 mock_demo.py

# Setup environment
./setup_env.sh

# Start bot (development)
source venv/bin/activate
python3 slack_bot.py

# Run tests
python3 -m pytest tests/

# Check configuration
python3 -c "from config import settings; print('✅ Config OK')"
```

---

## 💡 Tips

1. **Start with mock mode** - Test without real Goose/Snowflake first
2. **Use a test channel** - Create #goose-bot-test for testing
3. **Check the logs** - Terminal shows what's happening
4. **Read error messages** - They usually tell you what's wrong
5. **Ask for help** - Check FAQ.md or TROUBLESHOOTING.md

---

## 🎉 Success Looks Like

When everything is working, you'll see:

**In Terminal:**
```
✅ Configuration loaded successfully
✅ Database connection pool initialized
✅ Authentication system initialized
✅ Slack bot initialized successfully
🚀 Bot is running in development mode...
```

**In Slack:**
```
You: @Goose Query Expert What was our revenue last month?

Bot: 🔍 Searching for relevant data tables...
     ⚡ Generating optimized SQL query...
     🏃 Executing query against Snowflake...
     
     📊 Query Results (4 rows)
     [Beautiful formatted table with data]
     
     ⏱️ Executed in 2.34s | 📄 4 rows
```

---

## 🚀 Ready to Start?

1. **Run the demo**: `python3 mock_demo.py`
2. **Create Slack app**: Follow `VISUAL_SETUP_GUIDE.md`
3. **Setup environment**: `./setup_env.sh`
4. **Start the bot**: `python3 slack_bot.py`
5. **Test in Slack**: Ask a question!

---

## 📞 Need Help?

**Documentation:**
- Check `FAQ.md` for common questions
- Read `TROUBLESHOOTING.md` for solutions
- Review `SLACK_APP_SETUP_GUIDE.md` for setup help

**Can't find what you need?**
- All docs are in `/Users/rleach/goose-slackbot/`
- See `DOCUMENTATION_INDEX.md` for complete list

---

**Let's build something amazing! 🎉🚀📊**

---

*Last updated: 2025-10-27*
*Version: 1.0.0*
