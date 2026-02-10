#!/usr/bin/env python
"""Quick test script for the support prioritization system."""

import sys
sys.path.insert(0, 'src')

from vader_sentiment.ticket_store import TicketStore
from vader_sentiment.ticket_prioritizer import TicketPrioritizer
from vader_sentiment import SentimentAnalyzer

# Initialize
print("Initializing support system...")
analyzer = SentimentAnalyzer()
prioritizer = TicketPrioritizer(analyzer)
store = TicketStore(db_path='test_tickets.db')

# Add test tickets
test_messages = [
    ('John Doe', 'System is completely DOWN! HELP!!!'),
    ('Jane Smith', 'I am extremely angry and frustrated about this service'),
    ('Bob Jones', 'Just a quick question about billing'),
    ('Alice Brown', 'Someone hacked my account! URGENT!!'),
    ('Charlie White', 'Weapon detected in the building'),
]

print("\nAdding test tickets...\n")
for customer, msg in test_messages:
    priority_data = prioritizer.prioritize(msg)
    ticket_id = store.add_ticket(msg, customer, priority_data)
    print(f"✓ Ticket #{ticket_id}: [{priority_data['priority'].upper():8}] {customer:15} | {msg[:50]}")

# Show stats
print("\n" + "="*60)
stats = store.get_stats()
print("DASHBOARD STATS:")
print(f"  Total Tickets:  {stats['total_tickets']}")
print(f"  Critical:       {stats['critical']}")
print(f"  High Priority:  {stats['high']}")
print(f"  New:            {stats['new']}")
print(f"  Avg Sentiment:  {stats['avg_sentiment']}")

# Show tickets by priority
print("\n" + "="*60)
grouped = store.get_tickets_by_priority()
print("\nTICKETS BY PRIORITY:\n")
for priority in ['critical', 'high', 'normal']:
    tickets = grouped[priority]
    print(f"\n{priority.upper()} ({len(tickets)} tickets):")
    for t in tickets:
        print(f"  #{t['id']:2} | {t['customer_name']:15} | {t['message'][:45]:45} | Emotion: {t['emotion'] or 'N/A':10} | Score: {t['priority_score']:.2f}")

print("\n" + "="*60)
print("✓ Test database created: test_tickets.db")
print("✓ Ready to start the server with: python src/support_server.py")
