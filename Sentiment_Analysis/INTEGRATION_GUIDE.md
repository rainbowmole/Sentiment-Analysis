# Integration Guide – Support System with Ticketing Platforms

This guide shows how to integrate the support prioritization system with popular ticketing platforms.

## Zendesk Integration

### Setup
```python
# pip install zenpy

from zenpy import Zenpy
from src.vader_sentiment.ticket_prioritizer import TicketPrioritizer
from src.vader_sentiment import SentimentAnalyzer

creds = Zenpy(
    email='support@company.com',
    token='YOUR_ZENDESK_API_TOKEN',
    subdomain='company'
)

analyzer = SentimentAnalyzer()
prioritizer = TicketPrioritizer(analyzer)

# Get recent tickets
for ticket in creds.tickets.list(status='new'):
    # Analyze
    priority_data = prioritizer.prioritize(ticket.description)
    
    # Update priority in Zendesk
    priority_map = {
        'critical': 'urgent',
        'high': 'high',
        'normal': 'normal'
    }
    
    ticket.priority = priority_map[priority_data['priority']]
    ticket.tags.add('sentiment-analyzed')
    creds.tickets.update(ticket)
    
    print(f"Ticket {ticket.id}: {priority_data['priority']}")
```

## Jira Integration

### Setup
```python
# pip install jira

from jira import JIRA
from src.vader_sentiment.ticket_prioritizer import TicketPrioritizer
from src.vader_sentiment import SentimentAnalyzer

jira = JIRA(
    'https://company.atlassian.net',
    basic_auth=('user@company.com', 'YOUR_API_TOKEN')
)

analyzer = SentimentAnalyzer()
prioritizer = TicketPrioritizer(analyzer)

# Get open support issues
jql = 'project = SUPPORT AND status = "Open"'
for issue in jira.search_issues(jql):
    # Analyze
    priority_data = prioritizer.prioritize(
        f"{issue.fields.summary} {issue.fields.description}"
    )
    
    # Map priority
    priority_map = {
        'critical': 'Highest',
        'high': 'High',
        'normal': 'Medium'
    }
    
    # Update Jira
    issue.update(
        priority={'name': priority_map[priority_data['priority']]},
        labels=['sentiment-analyzed']
    )
    
    print(f"Issue {issue.key}: {priority_data['priority']}")
```

## Slack Integration

### Setup
```python
# pip install slack-bot-api requests

import requests
import json
from src.vader_sentiment.ticket_prioritizer import TicketPrioritizer
from src.vader_sentiment import SentimentAnalyzer

analyzer = SentimentAnalyzer()
prioritizer = TicketPrioritizer(analyzer)

SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
SUPPORT_API = 'http://127.0.0.1:5000/api'

# Listen for support messages and post to Slack
def post_to_slack(ticket_id, priority_data, message):
    color_map = {
        'critical': 'danger',   # Red
        'high': 'warning',      # Orange
        'normal': 'good'        # Green
    }
    
    slack_message = {
        "attachments": [
            {
                "color": color_map[priority_data['priority']],
                "title": f"New Support Ticket #{ticket_id}",
                "fields": [
                    {
                        "title": "Priority",
                        "value": priority_data['priority'].upper(),
                        "short": True
                    },
                    {
                        "title": "Score",
                        "value": f"{priority_data['priority_score']:.2f}",
                        "short": True
                    },
                    {
                        "title": "Message",
                        "value": message[:200],
                        "short": False
                    },
                    {
                        "title": "Emotion",
                        "value": priority_data['emotion'] or 'N/A',
                        "short": True
                    },
                    {
                        "title": "Sentiment",
                        "value": f"{priority_data['compound']:.3f}",
                        "short": True
                    }
                ]
            }
        ]
    }
    
    requests.post(SLACK_WEBHOOK_URL, json=slack_message)

# Example
priority_data = prioritizer.prioritize("System is DOWN!")
post_to_slack(1, priority_data, "System is DOWN!")
```

## Email Integration (IMAP)

### Setup
```python
import imaplib
import email
from src.vader_sentiment.ticket_prioritizer import TicketPrioritizer
from src.vader_sentiment.ticket_store import TicketStore
from src.vader_sentiment import SentimentAnalyzer

analyzer = SentimentAnalyzer()
prioritizer = TicketPrioritizer(analyzer)
store = TicketStore()

# Connect to email
imap = imaplib.IMAP4_SSL('imap.gmail.com')
imap.login('support@company.com', 'APP_PASSWORD')

# Read unread emails
imap.select('INBOX')
status, data = imap.search(None, 'UNSEEN')

for msg_id in data[0].split():
    status, msg_data = imap.fetch(msg_id, '(RFC822)')
    msg = email.message_from_bytes(msg_data[0][1])
    
    # Extract text
    body = msg.get_payload()
    subject = msg['Subject']
    sender = msg['From']
    
    # Analyze
    full_text = f"{subject}\n{body}"
    priority_data = prioritizer.prioritize(full_text)
    
    # Store ticket
    ticket_id = store.add_ticket(full_text, sender, priority_data)
    
    print(f"Email from {sender} → Ticket #{ticket_id} ({priority_data['priority']})")

imap.close()
```

## GitHub Issues Integration

### Setup
```python
# pip install PyGithub

from github import Github
from src.vader_sentiment.ticket_prioritizer import TicketPrioritizer
from src.vader_sentiment import SentimentAnalyzer

g = Github('YOUR_GITHUB_TOKEN')
analyzer = SentimentAnalyzer()
prioritizer = TicketPrioritizer(analyzer)

repo = g.get_repo('company/support-repo')

# Get open issues
for issue in repo.get_issues(state='open'):
    # Analyze
    priority_data = prioritizer.prioritize(
        f"{issue.title}\n{issue.body}"
    )
    
    # Update labels
    labels = ['sentiment-analyzed', f"priority-{priority_data['priority']}"]
    issue.set_labels(*labels)
    
    print(f"Issue #{issue.number}: {priority_data['priority']}")
```

## Webhook Integration (Generic)

### Setup
```python
# Add to support_server.py

from flask import request

TICKETING_WEBHOOK_URLS = {
    'zendesk': 'https://your-service.example.com/zendesk-update',
    'jira': 'https://your-service.example.com/jira-update',
}

@app.route("/api/tickets", methods=["POST"])
def submit_ticket():
    # ... existing code ...
    
    if data.success:
        ticket = store.get_ticket(ticket_id)
        
        # Send to external systems
        for service, url in TICKETING_WEBHOOK_URLS.items():
            try:
                requests.post(url, json={
                    'ticket': ticket,
                    'priority_data': priority_data
                }, timeout=5)
            except Exception as e:
                app.logger.warning(f"Webhook to {service} failed: {e}")
        
        return jsonify({'success': True, 'ticket_id': ticket_id})
```

## Batch Processing (Existing Tickets)

### Zendesk Bulk Scan
```python
from zenpy import Zenpy
from src.vader_sentiment.ticket_prioritizer import TicketPrioritizer
from src.vader_sentiment import SentimentAnalyzer

creds = Zenpy(email='...', token='...', subdomain='...')
analyzer = SentimentAnalyzer()
prioritizer = TicketPrioritizer(analyzer)

# Analyze all tickets created in last week
import datetime
since = datetime.datetime.now() - datetime.timedelta(days=7)

for ticket in creds.tickets.list(created_after=since):
    priority_data = prioritizer.prioritize(ticket.description)
    ticket.priority = priority_data['priority']
    creds.tickets.update(ticket)
    print(f"Updated ticket {ticket.id}")
```

## Custom Webhook Receiver (For External Systems)

```python
from flask import Flask, request, jsonify
from src.vader_sentiment.ticket_prioritizer import TicketPrioritizer
from src.vader_sentiment.ticket_store import TicketStore
from src.vader_sentiment import SentimentAnalyzer

app = Flask(__name__)
analyzer = SentimentAnalyzer()
prioritizer = TicketPrioritizer(analyzer)
store = TicketStore()

@app.route("/webhook/ingest", methods=["POST"])
def ingest_external():
    """
    Accept webhooks from external sources.
    Expected: {"customer_email": "...", "message": "..."}
    """
    data = request.get_json()
    message = data.get('message', '')
    customer = data.get('customer_email', 'Unknown')
    
    # Analyze
    priority_data = prioritizer.prioritize(message)
    
    # Store
    ticket_id = store.add_ticket(message, customer, priority_data)
    
    return jsonify({
        'success': True,
        'ticket_id': ticket_id,
        'priority': priority_data['priority'],
        'priority_score': priority_data['priority_score']
    })

if __name__ == '__main__':
    app.run(port=5001, debug=False)
```

## Zapier/IFTTT Integration

### Setup with N8N (Self-Hosted)
```yaml
# This is what your N8N workflow would look like:

nodes:
  - name: "Trigger"
    type: "webhook"  # Listen for incoming messages
    
  - name: "Send to Support API"
    type: "http"
    method: "POST"
    url: "http://127.0.0.1:5000/api/tickets"
    body:
      customer_name: "{{ $node.Trigger.json.from }}"
      message: "{{ $node.Trigger.json.text }}"
    
  - name: "Log Priority"
    type: "function"
    code: |
      return {
        ticket_id: data[0].json.ticket_id,
        priority: data[0].json.priority_data.priority
      };
    
  - name: "Post to Slack"
    type: "slack"
    channel: "#support"
    message: "Ticket {{ $node['Log Priority'].json.ticket_id }} - {{ $node['Log Priority'].json.priority }}"
```

---

## Monitoring & Alerting

### Datadog Integration
```python
from datadog import initialize, api
from src.vader_sentiment.ticket_store import TicketStore

options = {
    'api_key': 'YOUR_DATADOG_API_KEY',
    'app_key': 'YOUR_DATADOG_APP_KEY'
}

initialize(**options)

store = TicketStore()
stats = store.get_stats()

# Send metrics
api.Metric.send(
    metric='support.tickets.critical',
    points=stats['critical']
)

api.Metric.send(
    metric='support.tickets.total',
    points=stats['total_tickets']
)

api.Metric.send(
    metric='support.sentiment.avg',
    points=stats['avg_sentiment']
)
```

### Prometheus Integration
```python
from prometheus_client import Counter, Gauge, start_http_server, make_wsgi_app
from src.vader_sentiment.ticket_store import TicketStore
import time

store = TicketStore()

critical_tickets = Gauge('support_tickets_critical', 'Critical tickets count')
total_tickets = Gauge('support_tickets_total', 'Total tickets count')
avg_sentiment = Gauge('support_sentiment_avg', 'Average sentiment score')

def update_metrics():
    while True:
        stats = store.get_stats()
        critical_tickets.set(stats['critical'])
        total_tickets.set(stats['total_tickets'])
        avg_sentiment.set(stats['avg_sentiment'])
        time.sleep(60)

# Start metrics server
start_http_server(8000)
update_metrics()
```

---

## Testing Integrations

```bash
# Test API endpoint
curl -X POST http://127.0.0.1:5000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"Test","message":"Test message"}'

# Test webhook receiver
curl -X POST http://127.0.0.1:5001/webhook/ingest \
  -H "Content-Type: application/json" \
  -d '{"customer_email":"test@example.com","message":"Test"}'
```

---

## Best Practices

1. **Rate Limiting** — Add `flask-limiter` to prevent abuse
2. **Authentication** — Secure endpoints with API keys or OAuth
3. **Logging** — Log all integration events for debugging
4. **Error Handling** — Gracefully handle API failures
5. **Testing** — Use staging environments before production
6. **Monitoring** — Track priority distribution over time
7. **Feedback Loop** — Collect manual priority corrections for retraining

---

**Last Updated:** February 10, 2026
