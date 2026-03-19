# SMF Simple CMS

A lightweight, cost-effective CMS/CRM for small businesses. No expensive APIs, no complex setup.

## 🎯 Philosophy

- **Zero API costs** - No SendGrid, Twilio, or expensive SaaS
- **Works with what you have** - Uses SMTP (Gmail/Google Workspace), WhatsApp, Telegram
- **Optional integrations** - HubSpot, Salesforce only if you already have them
- **Simple deployment** - SQLite default, upgrade to PostgreSQL when needed

## ✨ Features

- 📧 **Email notifications** via SMTP (Google Workspace/Gmail) - FREE
- 💬 **WhatsApp/Telegram** for urgent alerts (free with WhatsApp Business API or Telegram Bot)
- 🏷️ **Simple lead management** - Track prospects from first contact to close
- 📊 **Basic analytics** - Dashboard with key metrics
- 🌐 **Website contact forms** - Embeddable forms for your site
- 📱 **Mobile-friendly** dashboard
- 📝 **Task management** - Follow-up reminders
- 📓 **Notes & activity log** - Keep track of conversations

## 🚀 Quick Start

```bash
git clone https://github.com/smfworks/smf-simple-cms.git
cd smf-simple-cms
pip install -r requirements.txt
python -m uvicorn smf_simple_cms.app:create_app --factory --reload
```

Visit http://localhost:8000

## ⚙️ Configuration

Create `.env`:

```bash
# Required
SECRET_KEY=your-secret-key
SMTP_USER=michael@smfworks.com
SMTP_PASSWORD=your-gmail-app-password

# Optional - for urgent alerts via messaging
WHATSAPP_ENABLED=true
WHATSAPP_ACCESS_TOKEN=your-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-id

TELEGRAM_ENABLED=true
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

### Gmail App Password Setup

1. Go to Google Account → Security → 2-Step Verification
2. Enable 2FA if not already on
3. Go to Security → App passwords
4. Generate new app password for "Mail"
5. Use that password in `SMTP_PASSWORD`

## 📊 Dashboard

Access your leads, tasks, and activity from the simple dashboard at `/`.

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/leads` | Create new lead |
| GET | `/api/leads` | List leads |
| GET | `/api/leads/{id}` | Get lead details |
| PATCH | `/api/leads/{id}` | Update lead |
| GET | `/api/stats` | Dashboard stats |
| POST | `/api/tasks` | Create task |
| POST | `/api/notes` | Add note |

## 🐳 Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/

EXPOSE 8000

CMD ["uvicorn", "smf_simple_cms.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
```

## 📈 Cost Comparison

| Service | Traditional | SMF Simple CMS |
|---------|-------------|----------------|
| Email (SendGrid) | $14.95+/mo | $0 (uses Gmail) |
| SMS (Twilio) | $0.0075/message | $0 (uses WhatsApp/Telegram) |
| Database | $15+/mo (Postgres) | $0 (SQLite) |
| **Total** | **$30+/mo** | **$0** |

## 🔗 Integrations (Optional)

- **HubSpot** - Sync leads to HubSpot CRM
- **WhatsApp Business API** - Receive/send WhatsApp messages
- **Telegram Bot API** - Bot notifications

## 🛣️ Roadmap

- [ ] Contact form builder
- [ ] Email templates
- [ ] Multi-user support
- [ ] Pipeline view
- [ ] Email campaign basics
- [ ] Mobile app

## 📄 License

MIT - Free for personal and commercial use.

Built by SMF Works for small businesses who need CRM without the enterprise price tag.