# SMF Simple CMS

A lightweight, cost-effective CMS/CRM for small businesses. No expensive APIs, no complex setup.

## Philosophy

- **Zero API costs** - No SendGrid, Twilio, or expensive SaaS
- **Works with what you have** - Uses SMTP (Gmail/Google Workspace), WhatsApp, Telegram
- **Optional integrations** - HubSpot, Salesforce only if you already have them
- **Simple deployment** - SQLite default, upgrade to PostgreSQL when needed

## Features

- 📧 Email notifications via SMTP (Google Workspace/Gmail)
- 💬 WhatsApp/Telegram for urgent alerts (free)
- 🏷️ Simple lead management
- 📊 Basic analytics dashboard
- 🌐 Website contact forms
- 📱 Mobile-friendly

## Quick Start

```bash
git clone https://github.com/smfworks/smf-simple-cms.git
cd smf-simple-cms
pip install -r requirements.txt
python -m smf_simple_cms
```

Visit http://localhost:8000

## Configuration

Create `.env`:

```bash
# Required
SECRET_KEY=your-secret-key
SMTP_USER=you@gmail.com
SMTP_PASSWORD=your-app-password

# Optional
WHATSAPP_ENABLED=true
WHATSAPP_PHONE=+1234567890
TELEGRAM_BOT_TOKEN=your-bot-token
```

## Deployment

See `docs/DEPLOYMENT.md` for Ubuntu server setup.

## License

MIT - Free for personal and commercial use.