"""Database models for SMF Simple CMS."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json


class LeadStatus(Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    ARCHIVED = "archived"


class LeadSource(Enum):
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL = "social_media"
    EMAIL = "email"
    PHONE = "phone"
    WALK_IN = "walk_in"
    OTHER = "other"


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Lead:
    """Lead/Potential customer."""
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    phone: Optional[str] = None
    company: Optional[str] = None
    source: LeadSource = LeadSource.WEBSITE
    status: LeadStatus = LeadStatus.NEW
    priority: Priority = Priority.MEDIUM
    
    # Qualification data
    budget: Optional[str] = None
    timeline: Optional[str] = None
    service_interest: Optional[str] = None
    notes: Optional[str] = None
    
    # Scoring
    score: int = 0
    
    # Meta
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    assigned_to: Optional[str] = None
    
    # Communication
    last_contact: Optional[datetime] = None
    next_follow_up: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "source": self.source.value if isinstance(self.source, Enum) else self.source,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "priority": self.priority.value if isinstance(self.priority, Enum) else self.priority,
            "budget": self.budget,
            "timeline": self.timeline,
            "service_interest": self.service_interest,
            "notes": self.notes,
            "score": self.score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "assigned_to": self.assigned_to,
            "last_contact": self.last_contact.isoformat() if self.last_contact else None,
            "next_follow_up": self.next_follow_up.isoformat() if self.next_follow_up else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Lead':
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            email=data.get("email", ""),
            phone=data.get("phone"),
            company=data.get("company"),
            source=LeadSource(data.get("source", "website")),
            status=LeadStatus(data.get("status", "new")),
            priority=Priority(data.get("priority", 2)),
            budget=data.get("budget"),
            timeline=data.get("timeline"),
            service_interest=data.get("service_interest"),
            notes=data.get("notes"),
            score=data.get("score", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now(),
            assigned_to=data.get("assigned_to"),
            last_contact=datetime.fromisoformat(data["last_contact"]) if data.get("last_contact") else None,
            next_follow_up=datetime.fromisoformat(data["next_follow_up"]) if data.get("next_follow_up") else None
        )


@dataclass
class Contact:
    """Contact person (can be customer, vendor, partner)."""
    id: Optional[int] = None
    name: str = ""
    email: str = ""
    phone: Optional[str] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    
    # Social/contact info
    website: Optional[str] = None
    linkedin: Optional[str] = None
    twitter: Optional[str] = None
    
    # Categorization
    type: str = "lead"  # lead, customer, vendor, partner
    tags: List[str] = field(default_factory=list)
    
    # Meta
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "company": self.company,
            "job_title": self.job_title,
            "website": self.website,
            "linkedin": self.linkedin,
            "twitter": self.twitter,
            "type": self.type,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class Note:
    """Note attached to a lead or contact."""
    id: Optional[int] = None
    content: str = ""
    lead_id: Optional[int] = None
    contact_id: Optional[int] = None
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "lead_id": self.lead_id,
            "contact_id": self.contact_id,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class Task:
    """Task/reminder for follow-ups."""
    id: Optional[int] = None
    title: str = ""
    description: Optional[str] = None
    lead_id: Optional[int] = None
    assigned_to: Optional[str] = None
    
    # Status
    status: str = "pending"  # pending, in_progress, completed, cancelled
    priority: Priority = Priority.MEDIUM
    
    # Dates
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "lead_id": self.lead_id,
            "assigned_to": self.assigned_to,
            "status": self.status,
            "priority": self.priority.value if isinstance(self.priority, Enum) else self.priority,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }