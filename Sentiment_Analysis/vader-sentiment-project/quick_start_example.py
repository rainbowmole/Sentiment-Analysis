#!/usr/bin/env python
"""
QUICK START: Customer Support Prioritization System

This script demonstrates how to use the support system programmatically.
"""

import sys
import os

# Add src to path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from vader_sentiment import SentimentAnalyzer
from vader_sentiment.ticket_prioritizer import TicketPrioritizer
from vader_sentiment.ticket_store import TicketStore

def main():
    """Example: Create a prioritizer and process support messages."""
    
    print("═" * 70)
    print("SUPPORT PRIORITIZATION SYSTEM - QUICK START")
    print("═" * 70)
    
    # Initialize components
    print("\n[1] Initializing components...")
    analyzer = SentimentAnalyzer()
    prioritizer = TicketPrioritizer(analyzer)
    store = TicketStore(db_path="example_tickets.db")
    print("    ✓ Analyzer, Prioritizer, and Database ready")
    
    # Example tickets
    print("\n[2] Processing example support tickets...\n")
    
    tickets = [
        ("Alice Johnson", "The entire system went down! We cannot access anything! HELP!!!"),
        ("Bob Smith", "I'm extremely frustrated and angry with your service. This is unacceptable."),
        ("Carol White", "Hi, quick question about the billing feature."),
        ("David Brown", "Someone compromised my account. Please help immediately!"),
        ("Emma Davis", "Loved using your product, very satisfied with the service!"),
    ]
    
    ticket_ids = []
    for customer, message in tickets:
        # Analyze and prioritize
        priority_data = prioritizer.prioritize(message)
        
        # Store in database
        ticket_id = store.add_ticket(message, customer, priority_data)
        ticket_ids.append(ticket_id)
        
        # Display result
        priority_color = {
            'critical': '🔴',
            'high': '🟠',
            'normal': '🟢'
        }.get(priority_data['priority'], '⚪')
        
        print(f"{priority_color} Ticket #{ticket_id}: {priority_data['priority'].upper():8} | {customer:15}")
        print(f"   Message: \"{message[:60]}...\"")
        print(f"   Score: {priority_data['priority_score']:.2f} | Emotion: {priority_data['emotion'] or 'N/A':10} | Compound: {priority_data['compound']:.3f}")
        print()
    
    # Show statistics
    print("\n[3] Dashboard Statistics\n")
    stats = store.get_stats()
    print(f"   Total Tickets:    {stats['total_tickets']}")
    print(f"   🔴 Critical:      {stats['critical']}")
    print(f"   🟠 High Priority: {stats['high']}")
    print(f"   🟢 Normal:        {stats['total_tickets'] - stats['critical'] - stats['high']}")
    print(f"   📋 New:           {stats['new']}")
    print(f"   😊 Avg Sentiment: {stats['avg_sentiment']:.3f}")
    
    # Show tickets by priority
    print("\n[4] Tickets Organized by Priority\n")
    grouped = store.get_tickets_by_priority()
    
    for priority, label, icon in [
        ('critical', 'CRITICAL (Needs immediate attention)', '🔴'),
        ('high', 'HIGH PRIORITY (Urgent)', '🟠'),
        ('normal', 'NORMAL (Routine)', '🟢')
    ]:
        tickets_in_priority = grouped[priority]
        print(f"\n{icon} {label}")
        print("   " + "-" * 60)
        
        if not tickets_in_priority:
            print("   (No tickets)\n")
            continue
        
        for t in tickets_in_priority:
            print(f"   Ticket #{t['id']} | {t['customer_name']:15} | Score: {t['priority_score']:.2f}")
            print(f"   └─ {t['message'][:55]}...")
            if t['emotion']:
                print(f"   └─ Emotion: {t['emotion']}, Keywords: {', '.join(t['flagged_keywords']) if t['flagged_keywords'] else 'None'}")
            print()
    
    # Update ticket status
    print("[5] Managing Ticket Status\n")
    if ticket_ids:
        print(f"   Marking ticket #{ticket_ids[0]} as 'in-progress'...")
        store.update_ticket_status(ticket_ids[0], 'in-progress')
        print(f"   Marking ticket #{ticket_ids[1]} as 'resolved'...")
        store.update_ticket_status(ticket_ids[1], 'resolved')
        
        # Show updated stats
        new_stats = store.get_stats()
        print(f"\n   Updated: New={new_stats['new']}, In-Progress=1, Resolved=1")
    
    # Demo: Analyze custom text
    print("\n[6] Analyze Custom Text (without storing)\n")
    custom_texts = [
        "The product is broken and nobody is helping!",
        "Thanks, everything is working great!",
    ]
    
    for text in custom_texts:
        result = prioritizer.prioritize(text)
        print(f"   Text: \"{text}\"")
        print(f"   → Priority: {result['priority'].upper()} | Emotional: {result['intensity']} | Score: {result['priority_score']:.2f}")
        print()
    
    # Final steps
    print("═" * 70)
    print("NEXT STEPS:")
    print("═" * 70)
    print("""
1. START THE WEB SERVER:
   python src/support_server.py
   
   Then open: http://127.0.0.1:5000

2. SUBMIT TICKETS via the web dashboard

3. QUERY via REST API:
   curl http://127.0.0.1:5000/api/tickets
   curl http://127.0.0.1:5000/api/stats

4. CHECK DATABASE:
   Database file: example_tickets.db (SQLite)
   
5. CUSTOMIZE:
   Edit src/vader_sentiment/ticket_prioritizer.py to adjust thresholds/keywords
""")
    print("═" * 70)

if __name__ == "__main__":
    main()
