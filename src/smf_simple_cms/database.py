"""Database layer for SMF Simple CMS."""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from .models import Lead, Contact, Note, Task, LeadStatus, LeadSource, Priority

logger = logging.getLogger(__name__)


class Database:
    """SQLite database for SMF Simple CMS."""
    
    def __init__(self, db_path: str = "data/cms.db"):
        """Initialize database."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_tables()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_tables(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            # Leads table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    company TEXT,
                    source TEXT DEFAULT 'website',
                    status TEXT DEFAULT 'new',
                    priority INTEGER DEFAULT 2,
                    budget TEXT,
                    timeline TEXT,
                    service_interest TEXT,
                    notes TEXT,
                    score INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    assigned_to TEXT,
                    last_contact TIMESTAMP,
                    next_follow_up TIMESTAMP
                )
            """)
            
            # Contacts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    phone TEXT,
                    company TEXT,
                    job_title TEXT,
                    website TEXT,
                    linkedin TEXT,
                    twitter TEXT,
                    type TEXT DEFAULT 'lead',
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Notes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    lead_id INTEGER,
                    contact_id INTEGER,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES leads (id),
                    FOREIGN KEY (contact_id) REFERENCES contacts (id)
                )
            """)
            
            # Tasks table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    lead_id INTEGER,
                    assigned_to TEXT,
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 2,
                    due_date TIMESTAMP,
                    completed_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES leads (id)
                )
            """)
            
            # Activity log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER,
                    details TEXT,
                    created_by TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    # Lead operations
    def create_lead(self, lead: Lead) -> int:
        """Create a new lead."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO leads (name, email, phone, company, source, status, priority,
                                 budget, timeline, service_interest, notes, score,
                                 assigned_to, next_follow_up)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead.name, lead.email, lead.phone, lead.company,
                lead.source.value if isinstance(lead.source, LeadSource) else lead.source,
                lead.status.value if isinstance(lead.status, LeadStatus) else lead.status,
                lead.priority.value if isinstance(lead.priority, Priority) else lead.priority,
                lead.budget, lead.timeline, lead.service_interest, lead.notes,
                lead.score, lead.assigned_to, lead.next_follow_up
            ))
            lead_id = cursor.lastrowid
            
            # Log activity
            self._log_activity(conn, "lead_created", "lead", lead_id, {"name": lead.name})
            
            conn.commit()
            return lead_id
    
    def get_lead(self, lead_id: int) -> Optional[Lead]:
        """Get lead by ID."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM leads WHERE id = ?", (lead_id,)
            ).fetchone()
            
            if row:
                return self._row_to_lead(row)
            return None
    
    def get_leads(self, status: Optional[str] = None, 
                  assigned_to: Optional[str] = None,
                  limit: int = 100, offset: int = 0) -> List[Lead]:
        """Get leads with optional filters."""
        query = "SELECT * FROM leads WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if assigned_to:
            query += " AND assigned_to = ?"
            params.append(assigned_to)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_lead(row) for row in rows]
    
    def update_lead(self, lead: Lead) -> bool:
        """Update lead."""
        if not lead.id:
            return False
        
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE leads SET
                    name = ?, email = ?, phone = ?, company = ?,
                    source = ?, status = ?, priority = ?,
                    budget = ?, timeline = ?, service_interest = ?,
                    notes = ?, score = ?, updated_at = ?,
                    assigned_to = ?, last_contact = ?, next_follow_up = ?
                WHERE id = ?
            """, (
                lead.name, lead.email, lead.phone, lead.company,
                lead.source.value if isinstance(lead.source, LeadSource) else lead.source,
                lead.status.value if isinstance(lead.status, LeadStatus) else lead.status,
                lead.priority.value if isinstance(lead.priority, Priority) else lead.priority,
                lead.budget, lead.timeline, lead.service_interest,
                lead.notes, lead.score, datetime.now(),
                lead.assigned_to, lead.last_contact, lead.next_follow_up,
                lead.id
            ))
            
            self._log_activity(conn, "lead_updated", "lead", lead.id, {"name": lead.name})
            conn.commit()
            return True
    
    def delete_lead(self, lead_id: int) -> bool:
        """Delete lead."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
            conn.execute("DELETE FROM notes WHERE lead_id = ?", (lead_id,))
            conn.execute("DELETE FROM tasks WHERE lead_id = ?", (lead_id,))
            conn.commit()
            return True
    
    def get_lead_stats(self) -> Dict[str, Any]:
        """Get lead statistics."""
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            
            by_status = {}
            for row in conn.execute("SELECT status, COUNT(*) FROM leads GROUP BY status"):
                by_status[row[0]] = row[1]
            
            new_this_week = conn.execute("""
                SELECT COUNT(*) FROM leads 
                WHERE created_at > datetime('now', '-7 days')
            """).fetchone()[0]
            
            return {
                "total_leads": total,
                "by_status": by_status,
                "new_this_week": new_this_week
            }
    
    # Contact operations
    def create_contact(self, contact: Contact) -> int:
        """Create contact."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO contacts (name, email, phone, company, job_title,
                                    website, linkedin, twitter, type, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                contact.name, contact.email, contact.phone, contact.company,
                contact.job_title, contact.website, contact.linkedin,
                contact.twitter, contact.type, json.dumps(contact.tags)
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_contacts(self, type: Optional[str] = None) -> List[Contact]:
        """Get contacts."""
        query = "SELECT * FROM contacts"
        params = []
        
        if type:
            query += " WHERE type = ?"
            params.append(type)
        
        query += " ORDER BY name"
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_contact(row) for row in rows]
    
    # Task operations
    def create_task(self, task: Task) -> int:
        """Create task."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO tasks (title, description, lead_id, assigned_to,
                                 status, priority, due_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                task.title, task.description, task.lead_id, task.assigned_to,
                task.status, task.priority.value if isinstance(task.priority, Priority) else task.priority,
                task.due_date
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_tasks(self, status: Optional[str] = None, 
                  assigned_to: Optional[str] = None) -> List[Task]:
        """Get tasks."""
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if assigned_to:
            query += " AND assigned_to = ?"
            params.append(assigned_to)
        
        query += " ORDER BY due_date ASC"
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_task(row) for row in rows]
    
    def complete_task(self, task_id: int) -> bool:
        """Mark task as complete."""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE tasks SET status = 'completed', completed_at = ?
                WHERE id = ?
            """, (datetime.now(), task_id))
            conn.commit()
            return True
    
    # Note operations
    def add_note(self, note: Note) -> int:
        """Add note."""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO notes (content, lead_id, contact_id, created_by)
                VALUES (?, ?, ?, ?)
            """, (note.content, note.lead_id, note.contact_id, note.created_by))
            conn.commit()
            return cursor.lastrowid
    
    def get_notes(self, lead_id: Optional[int] = None,
                  contact_id: Optional[int] = None) -> List[Note]:
        """Get notes."""
        query = "SELECT * FROM notes WHERE 1=1"
        params = []
        
        if lead_id:
            query += " AND lead_id = ?"
            params.append(lead_id)
        
        if contact_id:
            query += " AND contact_id = ?"
            params.append(contact_id)
        
        query += " ORDER BY created_at DESC"
        
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [self._row_to_note(row) for row in rows]
    
    # Activity log
    def _log_activity(self, conn: sqlite3.Connection, action: str, 
                     entity_type: str, entity_id: int, details: Dict):
        """Log activity."""
        conn.execute("""
            INSERT INTO activity_log (action, entity_type, entity_id, details)
            VALUES (?, ?, ?, ?)
        """, (action, entity_type, entity_id, json.dumps(details)))
    
    def get_activity_log(self, limit: int = 50) -> List[Dict]:
        """Get recent activity."""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM activity_log
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            
            return [dict(row) for row in rows]
    
    # Helper methods
    def _row_to_lead(self, row: sqlite3.Row) -> Lead:
        """Convert row to Lead."""
        return Lead(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            phone=row["phone"],
            company=row["company"],
            source=row["source"],
            status=row["status"],
            priority=row["priority"],
            budget=row["budget"],
            timeline=row["timeline"],
            service_interest=row["service_interest"],
            notes=row["notes"],
            score=row["score"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
            assigned_to=row["assigned_to"],
            last_contact=datetime.fromisoformat(row["last_contact"]) if row["last_contact"] else None,
            next_follow_up=datetime.fromisoformat(row["next_follow_up"]) if row["next_follow_up"] else None
        )
    
    def _row_to_contact(self, row: sqlite3.Row) -> Contact:
        """Convert row to Contact."""
        return Contact(
            id=row["id"],
            name=row["name"],
            email=row["email"],
            phone=row["phone"],
            company=row["company"],
            job_title=row["job_title"],
            website=row["website"],
            linkedin=row["linkedin"],
            twitter=row["twitter"],
            type=row["type"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
        )
    
    def _row_to_task(self, row: sqlite3.Row) -> Task:
        """Convert row to Task."""
        return Task(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            lead_id=row["lead_id"],
            assigned_to=row["assigned_to"],
            status=row["status"],
            priority=row["priority"],
            due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        )
    
    def _row_to_note(self, row: sqlite3.Row) -> Note:
        """Convert row to Note."""
        return Note(
            id=row["id"],
            content=row["content"],
            lead_id=row["lead_id"],
            contact_id=row["contact_id"],
            created_by=row["created_by"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
        )