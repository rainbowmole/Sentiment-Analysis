"""
Ticket storage and management using SQLite.
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

class TicketStore:
    """Simple SQLite-based ticket storage."""
    
    def __init__(self, db_path="tickets.db"):
        """Initialize or connect to SQLite database."""
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            message TEXT NOT NULL,
            ticket_type TEXT DEFAULT 'support',
            category TEXT,
            priority TEXT NOT NULL,
            priority_score REAL,
            emotion TEXT,
            compound REAL,
            intensity TEXT,
            urgency_flagged INTEGER,
            flagged_keywords TEXT,
            reason TEXT,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        conn.commit()
        conn.close()
    
    def add_ticket(self, message, customer_name=None, priority_data=None, ticket_type='support', category=None):
        """
        Add a new ticket to the store.
        
        ticket_type: 'support', 'suggestion', 'recommendation'
        category: 'feature', 'bug', 'improvement', 'ui', 'performance', etc.
        priority_data: dict from TicketPrioritizer.prioritize()
        
        Returns: ticket_id
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        now = datetime.now().isoformat()
        flagged_keywords = json.dumps(priority_data.get('flagged_keywords', []) if priority_data else [])
        
        c.execute('''INSERT INTO tickets 
            (customer_name, message, ticket_type, category, priority, priority_score, emotion, compound, intensity, 
             urgency_flagged, flagged_keywords, reason, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (
                customer_name,
                message,
                ticket_type,
                category,
                priority_data.get('priority', 'normal') if priority_data else 'normal',
                priority_data.get('priority_score', 0.0) if priority_data else 0.0,
                priority_data.get('emotion') if priority_data else None,
                priority_data.get('compound', 0.0) if priority_data else 0.0,
                priority_data.get('intensity', 'neutral') if priority_data else 'neutral',
                1 if priority_data and priority_data.get('urgency_flagged') else 0,
                flagged_keywords,
                priority_data.get('reason', '') if priority_data else '',
                now,
                now
            )
        )
        
        ticket_id = c.lastrowid
        conn.commit()
        conn.close()
        
        return ticket_id
    
    def get_ticket(self, ticket_id):
        """Get a single ticket by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute('SELECT * FROM tickets WHERE id = ?', (ticket_id,))
        row = c.fetchone()
        conn.close()
        
        if row:
            return self._row_to_dict(row)
        return None
    
    def get_all_tickets(self, status=None, priority=None, order_by='priority_score DESC, created_at DESC'):
        """
        Get all tickets, optionally filtered.
        
        status: 'new', 'in-progress', 'resolved', or None for all
        priority: 'critical', 'high', 'normal', or None for all
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = 'SELECT * FROM tickets WHERE 1=1'
        params = []
        
        if status:
            query += ' AND status = ?'
            params.append(status)
        if priority:
            query += ' AND priority = ?'
            params.append(priority)
        
        query += f' ORDER BY {order_by}'
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        
        return [self._row_to_dict(row) for row in rows]
    
    def get_tickets_by_priority(self):
        """Get all tickets grouped by priority tier."""
        all_tickets = self.get_all_tickets()
        
        grouped = {
            'critical': [t for t in all_tickets if t['priority'] == 'critical'],
            'high': [t for t in all_tickets if t['priority'] == 'high'],
            'normal': [t for t in all_tickets if t['priority'] == 'normal']
        }
        
        return grouped
    
    def get_tickets_by_type(self):
        """Get all tickets grouped by type (support vs suggestion/recommendation)."""
        all_tickets = self.get_all_tickets()
        
        grouped = {
            'support': [t for t in all_tickets if t.get('ticket_type') == 'support'],
            'suggestion': [t for t in all_tickets if t.get('ticket_type') in ('suggestion', 'recommendation')],
        }
        
        return grouped
    
    def update_ticket_status(self, ticket_id, status):
        """Update ticket status ('new', 'in-progress', 'resolved')."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        now = datetime.now().isoformat()
        
        c.execute('UPDATE tickets SET status = ?, updated_at = ? WHERE id = ?',
                  (status, now, ticket_id))
        
        conn.commit()
        conn.close()
    
    def delete_ticket(self, ticket_id):
        """Delete a ticket."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('DELETE FROM tickets WHERE id = ?', (ticket_id,))
        
        conn.commit()
        conn.close()
    
    def get_stats(self):
        """Get summary stats about tickets."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute('SELECT COUNT(*) FROM tickets')
        total = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM tickets WHERE status = ?', ('new',))
        new = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM tickets WHERE status = ?', ('in-progress',))
        in_progress = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM tickets WHERE priority = ?', ('critical',))
        critical = c.fetchone()[0]
        
        c.execute('SELECT COUNT(*) FROM tickets WHERE priority = ?', ('high',))
        high = c.fetchone()[0]
        
        c.execute('SELECT AVG(compound) FROM tickets')
        avg_compound = c.fetchone()[0] or 0.0
        
        conn.close()
        
        return {
            'total_tickets': total,
            'new': new,
            'in_progress': in_progress,
            'critical': critical,
            'high': high,
            'avg_sentiment': round(avg_compound, 3)
        }
    
    def _row_to_dict(self, row):
        """Convert sqlite3.Row to dict and parse JSON fields."""
        d = dict(row)
        if d.get('flagged_keywords'):
            d['flagged_keywords'] = json.loads(d['flagged_keywords'])
        if d.get('urgency_flagged'):
            d['urgency_flagged'] = bool(d['urgency_flagged'])
        return d
