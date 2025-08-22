# Deployment Guide

This guide explains how to deploy your own instance of the Telegram Moderation Bot.

## 🎯 Understanding Self-Hosted Deployment

### What Does "Self-Hosted" Mean?

When we say this bot is "self-hosted," it means:
- **You run the software** on your own server or computer
- **You control everything** - the data, settings, and operations
- **Your messages stay private** - nothing goes to third parties
- **Each installation is independent** - your bot doesn't connect to ours or anyone else's

### Analogy: It's Like Having Your Own Email Server

Think of it this way:
- **Gmail** = Someone else runs the email service for you
- **This Bot** = You run your own email server

Just like how companies run their own email servers for privacy and control, you run your own moderation bot.

## 🚀 Deployment Options

### Option 1: Local Computer (Easiest for Testing)

Perfect for testing or small groups.

**Pros:**
- Free (uses your existing computer)
- Easy to set up
- Good for learning

**Cons:**
- Computer must stay on 24/7
- Uses your internet bandwidth
- Not ideal for production

**Quick Start:**
```bash
# 1. Clone the repository
git clone https://github.com/yourusername/telegram_mod_bot.git
cd telegram_mod_bot

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your bot token
export TELEGRAM_BOT_TOKEN="your-token-from-botfather"

# 4. Run the bot
python src/bot.py
```

### Option 2: VPS (Recommended for Production)

A Virtual Private Server gives you a dedicated cloud computer.

**Recommended Providers:**
- **DigitalOcean** - $5/month, easy to use
- **Vultr** - $5/month, good performance
- **Hetzner** - €4/month, European
- **AWS EC2** - Free tier available

**Minimum Requirements:**
- 1 CPU core
- 1GB RAM
- 10GB storage
- Ubuntu 20.04 or newer

**Deployment Steps:**
```bash
# 1. SSH into your VPS
ssh user@your-server-ip

# 2. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# 3. Clone the repository
git clone https://github.com/yourusername/telegram_mod_bot.git
cd telegram_mod_bot

# 4. Create environment file
cat > .env << EOF
TELEGRAM_BOT_TOKEN=your-token-here
LOG_LEVEL=INFO
EOF

# 5. Run with Docker Compose
docker-compose up -d

# 6. Check logs
docker-compose logs -f
```

### Option 3: Cloud Platforms (Scalable)

For larger deployments or multiple groups.

#### Heroku (Simple)
```bash
# 1. Install Heroku CLI
# 2. Create app
heroku create your-bot-name

# 3. Set config
heroku config:set TELEGRAM_BOT_TOKEN=your-token

# 4. Deploy
git push heroku main
```

#### Google Cloud Run (Serverless)
```bash
# 1. Build container
gcloud builds submit --tag gcr.io/PROJECT-ID/telegram-bot

# 2. Deploy
gcloud run deploy --image gcr.io/PROJECT-ID/telegram-bot
```

#### Kubernetes (Enterprise)
```bash
# Use provided k8s manifests
kubectl apply -f k8s/deployment.yaml
```

### Option 4: Raspberry Pi (Home Server)

Great for home use with low power consumption.

**Requirements:**
- Raspberry Pi 3 or newer
- 8GB+ SD card
- Stable internet connection

**Setup:**
```bash
# Same as VPS deployment, but use ARM-compatible Docker images
docker build -f Dockerfile.arm . -t telegram-bot:arm
```

## 🔑 Getting Your Bot Token

Every instance needs its own unique bot token from Telegram:

1. **Open Telegram** and search for `@BotFather`
2. **Send** `/newbot`
3. **Choose a name** for your bot (e.g., "John's Group Moderator")
4. **Choose a username** (must end in 'bot', e.g., "johns_moderator_bot")
5. **Save the token** - looks like `1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ`

⚠️ **Important:** Keep this token secret! It's like a password.

## 🔧 Configuration

### Basic Configuration

Create `config/config.yaml`:
```yaml
telegram:
  token: "YOUR_BOT_TOKEN"  # Can also use environment variable
  
moderation:
  thresholds:
    spam: 0.7        # 0-1, higher = stricter
    toxicity: 0.8    # 0-1, higher = stricter
    harassment: 0.6  # 0-1, higher = stricter
    
rate_limiting:
  messages_per_second: 10
  burst_size: 20
```

### Environment Variables (Recommended)

More secure than config files:
```bash
# .env file
TELEGRAM_BOT_TOKEN=your-token-here
LOG_LEVEL=INFO
MAX_WORKERS=2
CACHE_SIZE=1000
RATE_LIMIT=10
```

## 📊 Resource Requirements

### Minimum (1-5 groups, <1000 users)
- **CPU:** 1 core
- **RAM:** 512MB
- **Storage:** 5GB
- **Bandwidth:** 10GB/month

### Recommended (5-20 groups, <5000 users)
- **CPU:** 2 cores
- **RAM:** 2GB
- **Storage:** 20GB
- **Bandwidth:** 50GB/month

### Large Scale (20+ groups, 5000+ users)
- **CPU:** 4+ cores
- **RAM:** 4GB+
- **Storage:** 50GB+
- **Bandwidth:** 100GB+/month
- Consider multiple instances

## 🚀 Quick Deployment Scripts

### One-Line Docker Deployment
```bash
curl -sSL https://raw.githubusercontent.com/yourusername/telegram_mod_bot/main/scripts/quick-deploy.sh | bash
```

### Using Make Commands
```bash
# Local testing
make test
make run-docker

# Production deployment
make deploy-production

# Check health
make health-check
```

## 🔄 Updating Your Bot

### Docker Update
```bash
# Pull latest version
docker-compose pull

# Restart with new version
docker-compose up -d

# Check logs
docker-compose logs -f
```

### Manual Update
```bash
# Pull latest code
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Restart bot
supervisorctl restart telegram-bot
```

## 🏥 Monitoring Your Bot

### Health Check Endpoint
```bash
curl http://localhost:8080/health
```

Returns:
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "messages_processed": 1523,
  "violations_detected": 47
}
```

### Logs
```bash
# Docker logs
docker-compose logs -f telegram-bot

# System logs
tail -f logs/bot.log
```

### Metrics
- Messages processed per minute
- Violations detected
- Response time
- Cache hit rate
- Memory usage

## 🆘 Troubleshooting

### Bot Not Responding
1. Check token is correct
2. Verify internet connection
3. Check logs for errors
4. Ensure bot is added as admin in group

### High Memory Usage
1. Reduce cache size in config
2. Restart bot daily with cron
3. Check for memory leaks in logs

### Rate Limiting Issues
1. Adjust rate limits in config
2. Check Telegram API limits
3. Consider multiple bot tokens

## 🔒 Security Best Practices

1. **Never commit tokens to Git**
   ```bash
   # Use environment variables instead
   export TELEGRAM_BOT_TOKEN="..."
   ```

2. **Use HTTPS for webhooks** (if applicable)

3. **Regular updates**
   ```bash
   # Check for updates weekly
   git pull origin main
   make test
   ```

4. **Backup configuration**
   ```bash
   make backup
   ```

5. **Monitor logs for suspicious activity**

## 💡 Tips for Success

1. **Start Small** - Test with one group first
2. **Monitor Closely** - Watch logs for the first week
3. **Adjust Thresholds** - Fine-tune based on your community
4. **Regular Backups** - Backup config and logs weekly
5. **Stay Updated** - Pull updates monthly

## 🤝 Getting Help

### Documentation
- [User Guide](../USER_GUIDE.md)
- [CI/CD Setup](CI_CD_SETUP.md)
- [API Reference](API_REFERENCE.md)

### Community
- GitHub Issues for bug reports
- Discussions for questions
- Wiki for community guides

### Logs to Include When Asking for Help
```bash
# System info
uname -a
python --version
docker --version

# Bot logs (last 100 lines)
docker-compose logs --tail=100 telegram-bot

# Error messages
grep ERROR logs/bot.log
```

## 📜 License Note

This is open-source software. You can:
- ✅ Run it for personal use
- ✅ Run it for your organization
- ✅ Modify it for your needs
- ✅ Share your improvements

Remember: Each deployment is independent. You're not using our service; you're running your own instance of our software.

## 🎉 Success Checklist

- [ ] Got bot token from @BotFather
- [ ] Chose deployment platform
- [ ] Configured environment variables
- [ ] Bot responds to `/start` command
- [ ] Added bot to test group
- [ ] Granted admin permissions
- [ ] Tested moderation features
- [ ] Set up monitoring
- [ ] Configured backups
- [ ] Documented your setup

Congratulations! You're now running your own Telegram moderation bot! 🚀