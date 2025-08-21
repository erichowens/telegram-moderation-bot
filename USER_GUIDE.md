# Telegram Moderation Bot - User Guide

## For Non-Technical Users

This guide will help you set up and use the Telegram Moderation Bot even if you're not familiar with programming or technical concepts.

## What This Bot Does

**Simple Explanation**: This bot watches your Telegram channels and automatically removes bad messages, spam, and inappropriate content so you don't have to do it manually.

**What it can detect**:
- 🚫 Spam messages (ads, promotional content)
- 😡 Bullying and harassment  
- 🔞 Adult content
- 💬 Excessive shouting (ALL CAPS)
- 🗣️ Hate speech
- 📱 Large files that might slow down your channel

## Getting Started

### Step 1: Get Your Bot Token

1. Open Telegram and search for `@BotFather`
2. Start a chat and type `/newbot`
3. Follow the instructions to create your bot
4. **Save the token** - it looks like: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`

### Step 2: Install the Bot

**Windows Users:**
1. Double-click `install.bat`
2. Wait for installation to complete
3. Double-click `start_bot.bat` to run

**Mac/Linux Users:**
1. Open Terminal and navigate to the bot folder
2. Run `./install.sh`  
3. Run `./start_bot.sh` to start

### Step 3: First-Time Setup

1. The bot will open with a welcome message
2. Go to the "Setup" tab
3. Paste your bot token in the "Bot Token" field
4. Click "Download Required Models" (this may take a few minutes)
5. Click "Start Bot"

### Step 4: Add Bot to Your Channel

1. Go to your Telegram channel
2. Add your bot as an administrator
3. Give it these permissions:
   - ✅ Delete messages
   - ✅ Restrict members (optional)
   - ✅ Pin messages (optional)

## Using the Interface

### Setup Tab
- **Bot Token**: Paste your @BotFather token here
- **Download Models**: One-time setup for the AI that detects bad content
- **Start/Stop Bot**: Control whether the bot is running

### Control Panel Tab
- **Bot Status**: Shows if your bot is running or stopped
- **Statistics**: Shows how many messages were checked and violations found
- **Activity Log**: Real-time log of what the bot is doing

### Violations Tab
- **Filter by Type**: See only specific types of violations
- **Violations Table**: List of all detected violations with details
- **Double-click** any row to see more details

### Settings Tab
- **Strictness Sliders**: Control how strict the bot is (0 = lenient, 100 = very strict)
- **Action Checkboxes**: Choose what the bot should do when it finds violations

## Recommended Settings for Beginners

### Strictness Levels:
- **Spam Detection**: 70 (catches most spam without false positives)
- **Harassment Detection**: 80 (strict on bullying)
- **Adult Content**: 90 (very strict on inappropriate content)
- **Hate Speech**: 85 (strict but allows some heated discussions)
- **Violence Detection**: 85 (removes graphic content)

### Actions:
- ✅ Delete violating messages
- ✅ Warn users about violations  
- ✅ Log all violations
- ⬜ Send alerts to admins (can be noisy)

## Troubleshooting

### Bot Not Starting
- Make sure you have Python 3.8+ installed
- Check that your bot token is correct
- Try running the installer again

### Bot Not Detecting Messages
- Make sure the bot is added to your channel as admin
- Check that the bot has "Delete messages" permission
- Verify the bot is running (green status in Control Panel)

### Too Many False Positives
- Lower the strictness levels in Settings
- Check the violations log to see what's being detected
- Adjust individual category settings

### Bot Missing Real Violations
- Increase strictness levels for specific categories
- Check if the content uses words not in the detection list
- Review the activity log for missed content

## Understanding the Terms

- **AI/Models**: The "brain" of the bot that analyzes content
- **Confidence**: How sure the bot is (higher % = more certain)
- **False Positive**: When the bot incorrectly flags good content
- **Token**: Your unique bot password from @BotFather
- **Admin**: Channel administrator with management permissions

## Getting Help

1. Check the Activity Log for error messages
2. Try restarting the bot
3. Make sure all files are in the same folder
4. Verify your internet connection for model downloads

## Privacy & Security

- ✅ All content analysis happens on your computer
- ✅ No messages are sent to external servers
- ✅ Your bot token stays on your machine
- ✅ The bot only processes messages in channels where it's admin

## Advanced Tips

- The bot learns from your manual corrections over time
- You can add custom words to the detection lists by editing the code
- Multiple channels can be monitored simultaneously  
- Log files are saved automatically for review

---

**Need More Help?** Check the README.md file for technical details or contact your system administrator.