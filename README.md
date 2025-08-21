# Telegram Moderation Bot

A user-friendly Telegram bot that automatically moderates your channels and groups. **No programming knowledge required!**

## 🎯 For Non-Technical Users

**[📖 Read the User Guide](USER_GUIDE.md)** - Step-by-step instructions for beginners

This bot protects your Telegram channels by automatically:
- 🚫 Removing spam and ads
- 😡 Blocking harassment and bullying  
- 🔞 Filtering adult content
- 💬 Stopping excessive shouting (ALL CAPS)
- 🗣️ Detecting hate speech

## ⚡ Quick Start

### Windows
1. **Download** this folder to your computer
2. **Double-click** `install.bat` (first time only)
3. **Double-click** `start_bot.bat` to run
4. **Follow** the setup wizard in the window that opens

### Mac/Linux
1. **Download** this folder to your computer  
2. **Run** `./install.sh` in Terminal (first time only)
3. **Run** `./start_bot.sh` to start
4. **Follow** the setup wizard in the window that opens

## 🔧 What You'll Need

1. **Telegram Bot Token** - Get one from [@BotFather](https://t.me/botfather) (free)
2. **Python 3.8+** - The installer will help you check this
3. **Internet connection** - For downloading the AI models (one time)
4. **Admin access** - To your Telegram channels

## 🖥️ Easy-to-Use Interface

- **Setup Tab**: Enter your bot token and download AI models
- **Control Panel**: Start/stop the bot and see statistics  
- **Violations**: Review what the bot has detected
- **Settings**: Adjust how strict the bot should be

## 🛡️ Privacy & Security

- ✅ **All processing happens on your computer** - Nothing sent to external servers
- ✅ **Your bot token stays private** - Never shared with anyone
- ✅ **Local AI models** - No cloud dependencies for content analysis
- ✅ **Admin-only operation** - Bot only works in channels where you're admin

## 📋 Technical Features

- **Intelligent Text Analysis**: Detects spam, harassment, and inappropriate content
- **Basic Image Filtering**: Flags large images and suspicious content
- **Simple Video Checks**: Monitors file sizes and duration
- **Real-time Processing**: Instant moderation as messages arrive
- **Comprehensive Logging**: Track all bot activity and decisions
- **Configurable Rules**: Adjust sensitivity and actions for different violation types

## Configuration

Create `config/config.yaml` with:

```yaml
telegram:
  token: "YOUR_BOT_TOKEN"
  
moderation:
  text_model: "path/to/local/llm"
  vision_model: "path/to/local/vlm"
  multimodal_model: "path/to/local/mm-llm"
  
policies:
  - type: "spam"
    threshold: 0.8
  - type: "harassment"
    threshold: 0.7
  - type: "nsfw"
    threshold: 0.9
```

## Usage

1. Add the bot to your Telegram channel/group
2. Grant admin permissions to the bot
3. The bot will automatically scan all new messages
4. Violations will be flagged according to your configured policies

## Project Structure

```
telegram_mod_bot/
├── src/
│   ├── bot.py              # Main bot implementation
│   ├── moderation.py       # Content moderation logic
│   └── __init__.py
├── config/
│   └── config.yaml         # Bot configuration
├── tests/
├── docs/
├── requirements.txt
└── README.md
```

## License

This project is intended for defensive security and content moderation purposes only.