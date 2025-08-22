# Telegram Moderation Bot

[![Tests](https://img.shields.io/badge/tests-164%20passing-success)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-75%25-green)](tests/)
[![Security](https://img.shields.io/badge/security-A%2B-brightgreen)](src/security.py)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)](requirements.txt)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

A production-ready, secure Telegram bot that automatically moderates your channels and groups with AI-powered content analysis and real-time threat detection.

## 🚀 Features

### Core Moderation
- 🚫 **Spam & Ad Detection** - AI-powered spam filtering
- 😡 **Harassment Prevention** - Real-time toxicity detection  
- 🔞 **NSFW Content Filtering** - Image and text analysis
- 💬 **Caps Lock Detection** - Prevents shouting
- 🗣️ **Hate Speech Blocking** - ML-based detection

### Security & Performance (v2.1.0)
- 🔐 **Encrypted Token Storage** - Fernet cipher encryption
- 🛡️ **ReDoS Attack Prevention** - Regex pattern validation
- ⚡ **High Performance** - LRU cache, concurrent processing
- 📊 **Rate Limiting** - Configurable limits with burst support
- 🏥 **Health Monitoring** - Real-time health checks
- 🔄 **Zero-Downtime Deployment** - Rolling updates

## 📦 Deployment Model

**This is a self-hosted bot** - You run your own instance on your infrastructure:
- ✅ **Your Bot, Your Control** - Complete control over your data and settings
- ✅ **Privacy First** - Messages never leave your server
- ✅ **Customizable** - Modify the code to fit your needs
- ✅ **Free Forever** - No subscriptions, no limits

### Who Is This For?

- **Telegram Group Admins** who want their own moderation bot
- **Communities** needing custom moderation rules
- **Privacy-Conscious Organizations** keeping data in-house
- **Developers** wanting to customize and extend functionality

### How It Works

```
Your Server/Computer → Runs This Bot → Connects to Telegram → Moderates Your Groups
```

Each person who uses this code:
1. Gets their own bot token from @BotFather
2. Runs their own instance
3. Has complete control

**This is NOT a shared service** - Think of it like WordPress: you download and run your own copy.

## 🎯 Quick Links

**[📖 User Guide](USER_GUIDE.md)** - Step-by-step instructions for beginners
**[🚀 Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - How to run your own instance
**[📋 Changelog](CHANGELOG.md)** - See what's new and fixed
**[🔧 CI/CD Setup](docs/CI_CD_SETUP.md)** - Advanced automation setup

This bot protects your Telegram channels by automatically:
- 🚫 Removing spam and ads
- 😡 Blocking harassment and bullying  
- 🔞 Filtering adult content
- 💬 Stopping excessive shouting (ALL CAPS)
- 🗣️ Detecting hate speech

## ⚡ Quick Start

### 🍎 macOS / 🐧 Linux
```bash
# One-line installer
curl -sSL https://raw.githubusercontent.com/yourusername/telegram_mod_bot/main/install.sh | bash

# Or manual installation
git clone https://github.com/yourusername/telegram_mod_bot.git
cd telegram_mod_bot
./install.sh
```

### 🪟 Windows
```powershell
# Download the repository
git clone https://github.com/yourusername/telegram_mod_bot.git
cd telegram_mod_bot

# Run installer
install.bat
```

### 🐳 Docker (All Platforms)
```bash
# Works on Mac, Linux, and Windows
git clone https://github.com/yourusername/telegram_mod_bot.git
cd telegram_mod_bot
echo "TELEGRAM_BOT_TOKEN=your-token-here" > .env
docker-compose up -d
```

After installation, run: `./start_bot.sh` (Mac/Linux) or `start_bot.bat` (Windows)

For detailed deployment options, see the **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)**

## 🔧 What You'll Need

1. **Telegram Bot Token** - Get one from [@BotFather](https://t.me/botfather) (free)
2. **Python 3.8+** - The installer will help you check this
3. **Internet connection** - For downloading the AI models (one time)
4. **Admin access** - To your Telegram channels

## 🖥️ Modern Web Dashboard

- **Real-time Monitoring**: Live violation feed and statistics
- **Interactive Charts**: Activity timelines and pattern visualization  
- **Violation Analysis**: Detailed view of detected threats
- **Settings Management**: Adjust detection thresholds and actions
- **Demo Mode**: Preview all features without setup

## 🛡️ Privacy & Security

- ✅ **All processing happens on your computer** - Nothing sent to external servers
- ✅ **Your bot token stays private** - Never shared with anyone
- ✅ **Local AI models** - No cloud dependencies for content analysis
- ✅ **Admin-only operation** - Bot only works in channels where you're admin

## 📋 Technical Features

- **Intelligent Text Analysis**: Detects spam, harassment, and inappropriate content
- **Advanced Image Analysis**: AI-powered NSFW detection with vision models
- **Video Frame Extraction**: Smart video analysis with key frame extraction and content moderation
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

### Option 1: Using Environment Variable (Recommended for Production)

Set your bot token as an environment variable:
```bash
export TELEGRAM_BOT_TOKEN="your-bot-token-here"
python src/bot.py
```

### Option 2: Using Configuration File

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