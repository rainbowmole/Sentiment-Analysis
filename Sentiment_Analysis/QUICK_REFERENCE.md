# Support System – Quick Reference Card

## Start the System
```powershell
python vader-sentiment-project\src\support_server.py
```
→ Opens automatically at **http://127.0.0.1:5000**

## API Endpoints

### Submit Ticket
```powershell
curl -X POST http://127.0.0.1:5000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{"customer_name":"John","message":"System is DOWN!"}'
```

### Analyze Text (No Storage)
```powershell
curl -X POST http://127.0.0.1:5000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"text":"I am very frustrated"}'
```

### Get All Tickets
```powershell
curl http://127.0.0.1:5000/api/tickets
```

### Get Statistics
```powershell
curl http://127.0.0.1:5000/api/stats
```

### Update Ticket Status
```powershell
curl -X PATCH http://127.0.0.1:5000/api/tickets/1/status \
  -H "Content-Type: application/json" \
  -d '{"status":"in-progress"}'
```

### Delete Ticket
```powershell
curl -X DELETE http://127.0.0.1:5000/api/tickets/1
```

## Priority Tiers

| Tier | Score | Examples |
|------|-------|----------|
| 🔴 **Critical** | ≥ 0.7 | "System DOWN!", "Account hacked", very angry |
| 🟠 **High** | 0.4-0.7 | "Broken feature", frustrated tone |
| 🟢 **Normal** | < 0.4 | "Quick question", positive feedback |

## Key Files

| File | Purpose |
|------|---------|
| `src/support_server.py` | Main Flask API server |
| `src/templates/support_dashboard.html` | Web dashboard UI |
| `src/vader_sentiment/ticket_prioritizer.py` | Priority scoring logic |
| `src/vader_sentiment/ticket_store.py` | SQLite database layer |
| `SUPPORT_SYSTEM_README.md` | Full documentation |
| `quick_start_example.py` | Demo script |

## Dashboard Stats

- **Total Tickets** — All tickets in database
- **🔴 Critical** — Count of critical tickets
- **🟠 High** — Count of high priority tickets
- **📋 New** — Unaddressed tickets (status: new)
- **😊 Avg Sentiment** — Average VADER compound score

## Scoring Factors

| Factor | Max Contribution |
|--------|-----------------|
| Severe keywords (weapon, hack, stole) | +1.0 |
| Very negative sentiment | +0.4 |
| Anger/frustration emotion | +0.35 |
| Multiple urgency keywords | +0.25 |

## Sample Ticket Responses

### Critical Priority
```
"System is DOWN! HELP!!!"
→ Priority: CRITICAL (Score: 1.0)
→ Keywords: down, help
```

### High Priority
```
"I'm extremely angry about this service"
→ Priority: HIGH (Score: 0.75)
→ Emotion: anger
→ Compound: -0.88 (very negative)
```

### Normal Priority
```
"Just a quick question about billing"
→ Priority: NORMAL (Score: 0.0)
→ Compound: 0.00 (neutral)
```

## Python Usage

```python
from src.vader_sentiment import SentimentAnalyzer
from src.vader_sentiment.ticket_prioritizer import TicketPrioritizer
from src.vader_sentiment.ticket_store import TicketStore

# Initialize
analyzer = SentimentAnalyzer()
prioritizer = TicketPrioritizer(analyzer)
store = TicketStore()

# Process ticket
priority = prioritizer.prioritize("System broken!")
ticket_id = store.add_ticket("System broken!", "John", priority)

# Query
ticket = store.get_ticket(ticket_id)
stats = store.get_stats()
grouped = store.get_tickets_by_priority()

# Update status
store.update_ticket_status(ticket_id, 'in-progress')
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 5000 already in use | Change port in `support_server.py` or kill process |
| ModuleNotFoundError: flask_cors | `pip install flask-cors` |
| NLTK resources missing | `python -c "import nltk; nltk.download('punkt')"` |
| Database locked | Delete `support_tickets.db` and restart |

## Dashboard Features

- ✅ Submit new tickets with customer name
- ✅ View tickets organized by priority (Critical → High → Normal)
- ✅ Watch real-time sentiment analysis preview
- ✅ Change ticket status (new/in-progress/resolved)
- ✅ Delete tickets
- ✅ Auto-refresh every 5 seconds
- ✅ Mobile-responsive design

## Testing

```powershell
# Run demo with sample tickets
python quick_start_example.py

# Run basic tests
python test_support_system.py
```

## Customize

**Change priority keywords:**
```python
# Edit src/vader_sentiment/ticket_prioritizer.py
URGENT_KEYWORDS = {"critical", "broken", "down", ...}
ANGER_KEYWORDS = {"angry", "frustrated", ...}
SEVERE_KEYWORDS = {"weapon", "hack", "stole", ...}
```

**Change port:**
```python
# Edit src/support_server.py
app.run(host="127.0.0.1", port=8000, debug=True)
```

**Fine-tune scoreoring:**
```python
# Edit ticket_prioritizer.py
CRITICAL_COMPOUND = -0.7  # Adjust sentiment threshold
HIGH_COMPOUND = -0.3
```

---

**Latest Update:** February 10, 2026 | **Status:** ✅ Production Ready
