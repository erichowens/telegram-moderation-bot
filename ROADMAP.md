# 🚀 Project Roadmap: The "Iron Dome" for Communities

**Goal**: $10k Monthly Recurring Revenue (MRR) within 6 months.
**Product Strategy**: Pivot from a self-hosted generic bot to a high-end SaaS "Community Defense System" for Crypto/DeFi projects.

## 🎯 Business Strategy

### The Niche
*   **Target Customer**: New Token Launches, DeFi Protocols, Paid Alpha Groups.
*   **Problem**: FUD (Fear, Uncertainty, Doubt) campaigns, Raid attacks, and Competitor Shilling destroy token value.
*   **Solution**: "Iron Dome" - An active defense system that detects *patterns* of attack, not just bad words.

### Monetization Tiers
1.  **Raid Shield ($200/mo)**:
    *   Coordinated Spam Detection
    *   Raid Prevention (Mass Join + Flood)
    *   Link Farm Blocking
2.  **Sentiment Guard ($500/mo)**:
    *   AI FUD Detection (Context-aware LLM analysis)
    *   Competitor Shilling Detection
    *   Weekly Sentiment Reports

---

## 🛠 Technical Roadmap

### Phase 1: Foundation (Multi-Tenancy) 🚧 **Current Focus**
*   [ ] **Database Migration**: Replace file-based config/logs with SQLite/PostgreSQL.
*   [ ] **Multi-Tenancy**: Allow one bot instance to serve 100+ distinct groups with different settings.
*   [ ] **Persistence**: Store "Threat Patterns" and user reputation on disk, not in memory.

### Phase 2: The "Iron Dome" Engine
*   [ ] **Redis Integration**: Fast message caching for high-velocity raid detection.
*   [ ] **LLM Pipeline**: Replace simple BERT models with prompt-engineered LLM calls (OpenAI/Anthropic) for FUD detection.
*   [ ] **Reputation System**: Track user behavior across *all* client groups (Global Ban List).

### Phase 3: The Dashboard
*   [ ] **SaaS Web App**: Client login via Telegram.
*   [ ] **Payment Gating**: Integrate Stripe/Crypto payments to unlock features.
*   [ ] **Analytics**: Real-time "Threat Level" charts for clients.

## 📝 Immediate Tasks
1.  Rip out `config.yaml` dependence.
2.  Implement SQLAlchemy ORM (Tenant -> Group -> Config).
3.  Persist Moderation Logs and Threat Patterns.
