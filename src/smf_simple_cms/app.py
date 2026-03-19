"""FastAPI application for SMF Simple CMS."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .database import Database
from .models import Lead, Contact, Task, Note
from .notifications import NotificationManager


# Global instances
_db = None
_notifications = None


def get_db():
    """Dependency to get database instance."""
    return _db


def get_notifications():
    """Dependency to get notification manager."""
    return _notifications


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _db, _notifications
    
    # Initialize database
    db_path = os.getenv("DATABASE_URL", "data/cms.db").replace("sqlite:///", "")
    _db = Database(db_path)
    
    # Initialize notifications
    notification_config = {
        "smtp": {
            "enabled": os.getenv("SMTP_ENABLED", "true").lower() == "true",
            "host": os.getenv("SMTP_HOST", "smtp.gmail.com"),
            "port": int(os.getenv("SMTP_PORT", "587")),
            "user": os.getenv("SMTP_USER"),
            "password": os.getenv("SMTP_PASSWORD"),
            "from_email": os.getenv("FROM_EMAIL"),
            "from_name": os.getenv("FROM_NAME", "SMF Simple CMS")
        },
        "whatsapp": {
            "enabled": os.getenv("WHATSAPP_ENABLED", "false").lower() == "true",
            "api_url": os.getenv("WHATSAPP_API_URL"),
            "token": os.getenv("WHATSAPP_TOKEN"),
            "phone_number_id": os.getenv("WHATSAPP_PHONE_ID")
        },
        "telegram": {
            "enabled": os.getenv("TELEGRAM_ENABLED", "false").lower() == "true",
            "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
            "chat_id": os.getenv("TELEGRAM_CHAT_ID")
        }
    }
    _notifications = NotificationManager(notification_config)
    
    yield
    
    # Cleanup
    _db = None
    _notifications = None


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="SMF Simple CMS",
        description="Lightweight CRM for small businesses",
        version="0.1.0",
        lifespan=lifespan
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Static files
    static_path = Path(__file__).parent.parent / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=static_path), name="static")
    
    # Health check
    @app.get("/api/health")
    async def health_check():
        return {"status": "ok", "version": "0.1.0"}
    
    # Lead routes
    @app.post("/api/leads")
    async def create_lead(lead_data: dict, db: Database = Depends(get_db)):
        """Create new lead."""
        lead = Lead(
            name=lead_data.get("name", ""),
            email=lead_data.get("email", ""),
            phone=lead_data.get("phone"),
            company=lead_data.get("company"),
            source=lead_data.get("source", "website"),
            budget=lead_data.get("budget"),
            timeline=lead_data.get("timeline"),
            service_interest=lead_data.get("service_interest"),
            notes=lead_data.get("message") or lead_data.get("notes"),
            score=lead_data.get("score", 0)
        )
        
        lead_id = db.create_lead(lead)
        lead.id = lead_id
        
        # Send notifications
        if _notifications:
            _notifications.send_lead_notification(lead)
            _notifications.send_confirmation_email(lead)
        
        return {"id": lead_id, "message": "Lead created"}
    
    @app.get("/api/leads")
    async def list_leads(
        status: str = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        db: Database = Depends(get_db)
    ):
        """List leads."""
        leads = db.get_leads(status=status, limit=limit, offset=skip)
        return {
            "leads": [lead.to_dict() for lead in leads],
            "count": len(leads)
        }
    
    @app.get("/api/leads/{lead_id}")
    async def get_lead(lead_id: int, db: Database = Depends(get_db)):
        """Get single lead."""
        lead = db.get_lead(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        notes = db.get_notes(lead_id=lead_id)
        tasks = db.get_tasks(lead_id=lead_id)
        
        result = lead.to_dict()
        result["notes"] = [n.to_dict() for n in notes]
        result["tasks"] = [t.to_dict() for t in tasks]
        
        return result
    
    @app.patch("/api/leads/{lead_id}")
    async def update_lead(lead_id: int, lead_data: dict, db: Database = Depends(get_db)):
        """Update lead."""
        lead = db.get_lead(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        for field in ["name", "email", "phone", "company", "status",
                      "budget", "timeline", "service_interest", "notes", "score"]:
            if field in lead_data:
                setattr(lead, field, lead_data[field])
        
        success = db.update_lead(lead)
        return {"success": success}
    
    @app.delete("/api/leads/{lead_id}")
    async def delete_lead(lead_id: int, db: Database = Depends(get_db)):
        """Delete lead."""
        success = db.delete_lead(lead_id)
        return {"success": success}
    
    # Stats
    @app.get("/api/stats")
    async def get_stats(db: Database = Depends(get_db)):
        """Get dashboard stats."""
        return db.get_lead_stats()
    
    # Tasks
    @app.post("/api/tasks")
    async def create_task(task_data: dict, db: Database = Depends(get_db)):
        """Create task."""
        task = Task(
            title=task_data["title"],
            description=task_data.get("description"),
            lead_id=task_data.get("lead_id"),
            assigned_to=task_data.get("assigned_to"),
            priority=task_data.get("priority", 2),
            due_date=task_data.get("due_date")
        )
        
        task_id = db.create_task(task)
        return {"id": task_id, "message": "Task created"}
    
    @app.get("/api/tasks")
    async def list_tasks(status: str = Query(None), db: Database = Depends(get_db)):
        """List tasks."""
        tasks = db.get_tasks(status=status)
        return {"tasks": [t.to_dict() for t in tasks]}
    
    @app.patch("/api/tasks/{task_id}/complete")
    async def complete_task(task_id: int, db: Database = Depends(get_db)):
        """Complete task."""
        success = db.complete_task(task_id)
        return {"success": success}
    
    # Notes
    @app.post("/api/notes")
    async def add_note(note_data: dict, db: Database = Depends(get_db)):
        """Add note."""
        note = Note(
            content=note_data["content"],
            lead_id=note_data.get("lead_id"),
            contact_id=note_data.get("contact_id"),
            created_by=note_data.get("created_by", "system")
        )
        
        note_id = db.add_note(note)
        return {"id": note_id, "message": "Note added"}
    
    # Activity log
    @app.get("/api/activity")
    async def get_activity(limit: int = Query(50), db: Database = Depends(get_db)):
        """Get activity log."""
        return db.get_activity_log(limit=limit)
    
    # Dashboard HTML
    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """Serve dashboard."""
        return DASHBOARD_HTML
    
    return app


# Simple HTML dashboard
DASHBOARD_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMF Simple CMS</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        header {
            background: #1a1a2e;
            color: white;
            padding: 20px;
        }
        header h1 { font-size: 24px; margin-bottom: 5px; }
        header p { opacity: 0.8; font-size: 14px; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .stat-card {
            background: white;
            padding: 24px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .stat-card h3 {
            font-size: 14px;
            color: #666;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .stat-card .number {
            font-size: 36px;
            font-weight: 700;
            color: #0066CC;
        }
        .leads-section {
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .leads-section h2 {
            font-size: 20px;
            margin-bottom: 20px;
            color: #1a1a2e;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        th {
            font-weight: 600;
            color: #666;
            font-size: 13px;
            text-transform: uppercase;
        }
        tr:hover { background: #f8f9fa; }
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 500;
        }
        .status-new { background: #e3f2fd; color: #1976d2; }
        .status-contacted { background: #fff3e0; color: #f57c00; }
        .status-qualified { background: #e8f5e9; color: #388e3c; }
        .status-won { background: #d4edda; color: #155724; }
        .status-lost { background: #f8d7da; color: #721c24; }
        .score { font-weight: 600; }
        .score-high { color: #d32f2f; }
        .score-medium { color: #f57c00; }
        .score-low { color: #388e3c; }
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        .empty {
            text-align: center;
            padding: 60px;
            color: #666;
        }
        .refresh-btn {
            float: right;
            background: #0066CC;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
        }
        .refresh-btn:hover { background: #0052a3; }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>SMF Simple CMS</h1>
            <p>Lightweight CRM for Small Businesses</p>
        </div>
    </header>
    
    <div class="container">
        <div class="stats">
            <div class="stat-card">
                <h3>Total Leads</h3>
                <div class="number" id="total-leads">-</div>
            </div>
            <div class="stat-card">
                <h3>New This Week</h3>
                <div class="number" id="new-leads">-</div>
            </div>
            <div class="stat-card">
                <h3>Hot Leads (70+)</h3>
                <div class="number" id="hot-leads">-</div>
            </div>
        </div>
        
        <div class="leads-section">
            <h2>Recent Leads <button class="refresh-btn" onclick="loadData()">Refresh</button></h2>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Company</th>
                        <th>Status</th>
                        <th>Score</th>
                        <th>Date</th>
                    </tr>
                </thead>
                <tbody id="leads-body">
                    <tr><td colspan="6" class="loading">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        async function loadData() {
            try {
                // Load stats
                const statsRes = await fetch('/api/stats');
                const stats = await statsRes.json();
                document.getElementById('total-leads').textContent = stats.total_leads;
                document.getElementById('new-leads').textContent = stats.new_this_week;
                
                // Calculate hot leads
                const leadsRes = await fetch('/api/leads');
                const data = await leadsRes.json();
                const hotLeads = data.leads.filter(l => l.score >= 70).length;
                document.getElementById('hot-leads').textContent = hotLeads;
                
                // Render leads table
                const tbody = document.getElementById('leads-body');
                if (data.leads.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="empty">No leads yet. Your contact form submissions will appear here.</td></tr>';
                    return;
                }
                
                tbody.innerHTML = data.leads.slice(0, 10).map(lead => {
                    const scoreClass = lead.score >= 70 ? 'score-high' : lead.score >= 40 ? 'score-medium' : 'score-low';
                    const date = new Date(lead.created_at).toLocaleDateString('en-US', { 
                        month: 'short', day: 'numeric', year: 'numeric' 
                    });
                    return `
                        <tr>
                            <td>${lead.name || 'Anonymous'}</td>
                            <td>${lead.email}</td>
                            <td>${lead.company || '-'}</td>
                            <td><span class="status-badge status-${lead.status}">${lead.status}</span></td>
                            <td class="score ${scoreClass}">${lead.score}</td>
                            <td>${date}</td>
                        </tr>
                    `;
                }).join('');
                
            } catch (err) {
                console.error('Failed to load:', err);
                document.getElementById('leads-body').innerHTML = 
                    '<tr><td colspan="6" class="empty">Error loading data. Please try again.</td></tr>';
            }
        }
        
        // Initial load
        loadData();
        
        // Auto refresh every 30 seconds
        setInterval(loadData, 30000);
    </script>
</body>
</html>'''