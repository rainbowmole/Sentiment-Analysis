# Support Ticket Prioritization System

A customer support system that automatically prioritizes tickets based on **sentiment analysis**, **emotion detection**, and **urgency keywords**. Intelligently routes support requests to focus on what matters most.

## Features

✅ **Automatic Priority Classification**
- Analyzes each ticket and assigns: **Critical**, **High**, or **Normal** priority
- Combines multiple signals: sentiment intensity, emotion detection, urgency keywords, anomalies

✅ **Intelligent Scoring**
- **Negative sentiment** → higher priority (compound score)
- **Anger/frustration detected** → elevated to high/critical
- **Urgency keywords** → systems down, broken, emergency, etc.
- **Severe keywords** → weapons, theft, security breach, etc. → automatic Critical flag

✅ **Web Dashboard**
- Real-time ticket queue organized by priority
- Submit tickets directly from the dashboard
- Mark tickets as "in-progress" or "resolved"
- View detailed sentiment analysis for each ticket

✅ **Persistent Storage**
- SQLite database (`support_tickets.db`) stores all tickets
- Tracks customer name, sentiment metrics, emotion, timestamps, status
- Query by priority, status, or date range

✅ **REST API**
- Submit tickets programmatically
- Query priorities without storing
- Analyze text in bulk

## Installation

### 1. Install Dependencies
```powershell
pip install -r vader-sentiment-project\requirements.txt
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

### 2. Start the Server
```powershell
python vader-sentiment-project\src\support_server.py
```

Opens automatically at: **http://127.0.0.1:5000**

## Quick Start

### Dashboard (Web UI)
1. Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)
2. Submit a ticket directly via the form
3. View all tickets organized by priority (Critical → High → Normal)
4. Click actions to manage ticket status

### Programmatic API
Submit a ticket:
```powershell
curl -X POST http://127.0.0.1:5000/api/tickets `
  -H "Content-Type: application/json" `
  -d '{"customer_name":"John","message":"System is DOWN!"}'
```

Analyze text (without storing):
```powershell
curl -X POST http://127.0.0.1:5000/api/analyze `
  -H "Content-Type: application/json" `
  -d '{"text":"I am extremely angry..."}'
```

Get all tickets:
```powershell
curl http://127.0.0.1:5000/api/tickets
```

Get statistics:
```powershell
curl http://127.0.0.1:5000/api/stats
```

## Priority Scoring Algorithm

### Critical Priority (Priority Score ≥ 0.7)
Automatic escalation when:
- **Severe keywords detected**: weapon, gun, bomb, threat, stole, hacked, security breach
- **Very angry tone** + negative sentiment (emotion: anger detected)
- **Multiple urgent signals** combined (urgency keywords + intense negative sentiment)

### High Priority (0.4 ≤ Score < 0.7)
- Strong negative sentiment (compound ≤ -0.3)
- Detected anger/frustration
- Multiple urgency keywords present
- Account security or service outage keywords

### Normal Priority (Score < 0.4)
- Neutral or slightly negative sentiment
- No urgent keywords
- General inquiries and feedback

### Scoring Components
| Factor | Contribution | Trigger |
|--------|--------------|---------|
| **Severe keywords** | +1.0 (Critical) | weapon, stole, hack, threat, etc. |
| **Very negative sentiment** | +0.4 | compound ≤ -0.7 |
| **Moderately negative** | +0.25 | compound ≤ -0.3 |
| **Anger emotion** | +0.35 | VADER emotion: anger |
| **Urgency keywords** | +0.1-0.25/kw | down, broken, urgent, help, critical, etc. |
| **Punctuation emphasis** | Modifier | Extra ! or ? marks |

## Key Files

```
vader-sentiment-project/
├── src/
│   ├── support_server.py              # Main Flask server (PORT 5000)
│   ├── vader_sentiment/
│   │   ├── ticket_prioritizer.py      # Priority scoring logic
│   │   ├── ticket_store.py            # SQLite database layer
│   │   ├── analyzer.py                # VADER sentiment analyzer wrapper
│   │   ├── summarizer.py              # Tone & emotion detection
│   │   ├── structure.py               # Per-word analysis
│   │   └── __init__.py
│   ├── templates/
│   │   └── support_dashboard.html     # Live dashboard UI
│   └── app.py                          # Legacy CLI interface
├── requirements.txt                    # Dependencies (flask, vaderSentiment, nltk, flask-cors)
└── support_tickets.db                  # SQLite database (auto-created)
```

## API Endpoints

### Tickets
- **GET** `/api/tickets` — Get all tickets grouped by priority
- **GET** `/api/tickets/<id>` — Get single ticket details
- **POST** `/api/tickets` — Submit new ticket
  - Body: `{"customer_name": "John", "message": "Issue..."}`
- **PATCH** `/api/tickets/<id>/status` — Update ticket status
  - Body: `{"status": "new|in-progress|resolved"}`
- **DELETE** `/api/tickets/<id>` — Delete ticket

### Analysis
- **POST** `/api/analyze` — Analyze text without storing ticket
  - Body: `{"text": "..."}`
  - Returns: sentiment analysis + priority data

### Dashboard
- **GET** `/api/stats` — Dashboard statistics (total, critical, high, new, avg sentiment)
- **GET** `/` — Load dashboard HTML

## Database Schema

**tickets** table:
```sql
CREATE TABLE tickets (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  customer_name TEXT,
  message TEXT NOT NULL,
  priority TEXT NOT NULL,            -- 'critical', 'high', 'normal'
  priority_score REAL,                -- 0.0 to 1.0
  emotion TEXT,                       -- emotion detected (anger, sadness, etc.)
  compound REAL,                      -- VADER compound sentiment (-1 to 1)
  intensity TEXT,                     -- 'very', 'moderately', 'mildly', 'neutral'
  urgency_flagged INTEGER,            -- 1 if urgent keywords detected
  flagged_keywords TEXT,              -- JSON array of detected keywords
  reason TEXT,                        -- Human-readable reason for priority
  status TEXT DEFAULT 'new',          -- 'new', 'in-progress', 'resolved'
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Testing

### Run Test Suite
```powershell
cd vader-sentiment-project
python test_support_system.py
```

Output shows test tickets created with correct priority assignments.

### Manual Testing
```powershell
# Terminal 1: Start the server
python vader-sentiment-project\src\support_server.py

# Terminal 2: Submit test tickets
curl -X POST http://127.0.0.1:5000/api/tickets `
  -H "Content-Type: application/json" `
  -d '{"customer_name":"Alice","message":"System is DOWN!"}'
```

Browse to http://127.0.0.1:5000 to see results.

## Example Tickets

| Message | Emotion | Sentiment | Priority | Score | Reason |
|---------|---------|-----------|----------|-------|--------|
| "System is DOWN! HELP!!!" | N/A | -0.24 | Normal | 0.25 | Urgent keywords: down, help |
| "I am extremely angry about this" | anger | -0.66 | Critical | 0.75 | Angry/frustrated (emotion: anger) |
| "Just a quick question" | N/A | 0.00 | Normal | 0.00 | Neutral sentiment |
| "Someone hacked my account!" | N/A | -0.46 | Critical | 1.00 | Severe keywords: hacked |
| "Weapon in the building" | N/A | 0.60 | Critical | 1.00 | Severe keywords: weapon |

## Performance & Scaling

- **Small deployments** (<1000 tickets): SQLite sufficient
- **Large deployments**: Migrate to PostgreSQL or MySQL
- **Real-time updates**: Dashboard refreshes every 5 seconds
- **Batch processing**: Use `/api/analyze` endpoint without storage for high volume

## Customization

### Adjust Priority Keywords
Edit `src/vader_sentiment/ticket_prioritizer.py`:
```python
URGENT_KEYWORDS = {
    "critical", "emergency", "broken", "down", ...
}
ANGER_KEYWORDS = {
    "angry", "frustrated", "hate", ...
}
```

### Add Custom Emotions
Extend the emotion lexicon in `src/vader_sentiment/summarizer.py`:
```python
EMO = {
    "joy": {...},
    "anger": {...},
    "your_emotion": {"keyword1", "keyword2", ...}
}
```

### Change Thresholds
Modify score thresholds in `ticket_prioritizer.py`:
```python
CRITICAL_COMPOUND = -0.7  # Sentiment threshold for critical
HIGH_COMPOUND = -0.3      # Sentiment threshold for high
```

## Troubleshooting

**Server won't start**
```powershell
# Kill any process on port 5000
Get-Process | Where-Object { $_.Handles -eq 5000 } | Stop-Process
```

**"ModuleNotFoundError: flask_cors"**
```powershell
pip install flask-cors
```

**Database locked**
```powershell
# Delete old database and restart
rm support_tickets.db
python src/support_server.py
```

**NLTK resources missing**
```powershell
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"
```

## Future Enhancements

- [ ] Email/Slack notification for critical tickets
- [ ] Assign tickets to agents based on expertise tags
- [ ] Historical trend analysis (daily/weekly report)
- [ ] Machine learning retraining on manual labels
- [ ] Integration with Zendesk/Jira APIs
- [ ] Sentiment confidence scoring
- [ ] Multi-language support

## License

MIT
