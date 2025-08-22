# Self-Hosted FAQ

## What is Self-Hosted Software?

Self-hosted software runs on YOUR infrastructure, not someone else's servers.

## Common Questions

### Q: Do I need to pay you to use this bot?
**A: No!** This is free, open-source software. You run it yourself, no payments to us.

### Q: Can you see my messages or data?
**A: No!** Your bot runs on your server. We have no access to your data, messages, or bot token.

### Q: Will my bot connect to your servers?
**A: No!** Your bot only connects to:
- Telegram's API (to function as a bot)
- Your server (where it runs)
- Nowhere else

### Q: If I stop my server, does the bot stop working?
**A: Yes.** Since it runs on your infrastructure, if your server goes down, your bot goes offline.

### Q: Can multiple people use the same bot instance?
**A: Yes, but** each Telegram group admin typically runs their own instance for maximum control and privacy.

### Q: What's the difference between this and BotFather?
- **BotFather**: Creates your bot account on Telegram (like creating an email address)
- **This Software**: The program that controls what your bot does (like email software)

### Q: Why self-hosted instead of a service?

| Self-Hosted (This Bot) | Service (Like MEE6, Dyno) |
|------------------------|----------------------------|
| You own your data | Company owns the data |
| Free forever | Usually has paid tiers |
| Customize anything | Limited customization |
| You manage updates | Automatic updates |
| Your server costs | No server costs |
| Complete privacy | Data on their servers |

### Q: What happens if you stop maintaining this project?
**A: Your bot keeps working!** Since you have the complete code:
- Your existing bot continues to run
- You can modify it yourself
- You can hire someone to update it
- The community can fork and continue it

### Q: Can I sell this as a service to others?
**A: Check the license,** but generally:
- ✅ You can run it as a service
- ✅ You can charge for hosting/management
- ⚠️ You must follow the open-source license terms
- ⚠️ You should contribute improvements back

### Q: How is this different from Discord bots?

| Aspect | This Bot | Discord Bots |
|--------|----------|--------------|
| Platform | Telegram | Discord |
| Hosting | Always self-hosted | Often shared services |
| Privacy | Complete | Varies |
| Cost | Your hosting only | Often freemium |

### Q: Do I need programming knowledge?
**A: No for basic use,** but it helps for:
- Customization
- Troubleshooting
- Advanced features

### Q: What if I want you to host it for me?
**A: We don't offer hosting,** but you can:
- Use the Docker setup (easiest)
- Hire a developer to set it up
- Use a VPS with our guides
- Ask the community for help

### Q: Will my bot token work on multiple servers?
**A: Yes,** but it's not recommended:
- One token = one bot
- Running on multiple servers = conflicts
- Better to use one server or container orchestration

### Q: Can I contribute improvements?
**A: Absolutely!** We welcome:
- Bug fixes
- New features
- Documentation improvements
- Translations
- Testing

### Q: Is this legal to use?
**A: Yes,** as long as you:
- Follow Telegram's Terms of Service
- Respect user privacy
- Comply with local laws
- Use it for legitimate moderation

### Q: What data does the bot store?
**A: Minimal data:**
- Temporary cache of recent messages (for spam detection)
- Violation logs (optional)
- Configuration settings
- No permanent message storage

### Q: Can I run multiple bots from one server?
**A: Yes!** You can run multiple instances:
```bash
# Bot 1
docker-compose -f docker-compose.bot1.yml up -d

# Bot 2  
docker-compose -f docker-compose.bot2.yml up -d
```

### Q: How do updates work?
**A: You control updates:**
```bash
# Check for updates
git pull origin main

# Test first
make test

# Deploy when ready
docker-compose up -d
```

## The Key Concept

**Think of this bot like a recipe:**
- We provide the recipe (code)
- You provide the ingredients (server, bot token)
- You cook the meal (run the bot)
- You serve it to your guests (your Telegram groups)

Everyone using this recipe cooks their own meal - they don't come to our restaurant!

## Still Confused?

Here's the simplest explanation:

1. **You download our code** (like downloading a game)
2. **You run it on your computer/server** (like installing the game)
3. **It works for your Telegram groups** (like playing the game)
4. **We never see or touch your bot** (like an offline game)

That's it! You're running YOUR OWN bot using OUR CODE as the blueprint. 🎯