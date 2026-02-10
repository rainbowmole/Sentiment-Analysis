# Vader Sentiment Project

Quick guide — which file to run / open and known problem file.

Modes
- Server mode (Flask + VADER — recommended for full Python analyzer)
  - Run the Flask app:
    ```powershell
    # from project root
    python vader-sentiment-project\src\web_app.py
    ```
  - Open in browser:
    ```
    http://127.0.0.1:8000
    ```
  - Files used:
    - Server entry: vader-sentiment-project\src\web_app.py
    - Template served by Flask: vader-sentiment-project\src\templates\index.html

  - Test API from PowerShell:
    ```powershell
    Invoke-RestMethod -Uri 'http://127.0.0.1:8000/analyze' -Method Post -ContentType 'application/json' -Body (@{ text = 'I love matcha' } | ConvertTo-Json)
    ```
  - Or use real curl (avoid PowerShell alias):
    ```powershell
    curl.exe -v -X POST -H "Content-Type: application/json" -d '{"text":"I love matcha"}' http://127.0.0.1:8000/analyze
    ```

- Static / client-only mode (no Python required)
  - Open directly in a browser (double-click) or serve statically:
    ```
    vader-sentiment-project\src\templates\index_static.html
    ```
  - To serve with a simple HTTP server:
    ```powershell
    python -m http.server 8000
    # then open:
    http://127.0.0.1:8000/vader-sentiment-project/src/templates/index_static.html
    ```

### S.E.N.T.R.I — Smart Evaluation & Notification for Ticket Ranking Intelligence

This repository contains the S.E.N.T.R.I system (built on the original Vader-based analyzer) — a lightweight sentiment-driven ticket prioritization and notification pipeline.

## Quick overview
- **Purpose:** Analyze incoming user messages (support issues, suggestions, recommendations), score them with a multi-factor prioritizer, store results in SQLite, and surface prioritized tickets in a dashboard.
- **Main components:**
  - Server: `src/support_server.py` (Flask + dashboard)
  - Dashboard template: `src/templates/support_dashboard.html`
  - Analyzer & prioritizer: `src/vader_sentiment` (VADER analyzer, `ticket_prioritizer.py`)
  - Storage: `src/vader_sentiment/ticket_store.py` (SQLite `support_tickets.db`)

## Quickstart
1. Create and activate a virtual environment (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Start the S.E.N.T.R.I server (from project root):

```powershell
python src/support_server.py
```

4. Open the dashboard in your browser:

```
http://127.0.0.1:5000
```

## Core API endpoints
- `POST /api/tickets` — submit a ticket payload: `{ customer_name, message, ticket_type, category }`.
- `GET /api/tickets` — returns tickets grouped by priority and dashboard stats.
- `POST /api/analyze` — run analysis on text without storing (returns `priority_data`).
- `PATCH /api/tickets/{id}/status` — update ticket status (new, in-progress, resolved).
- `DELETE /api/tickets/{id}` — delete ticket.
- `GET /api/stats` — summary metrics.

## Data pipeline (Input / Process / Output)
- **Input:**
  - Sources: Dashboard form, Email ingestors, Webhooks (Zendesk, Jira, GitHub), Slack, or external connectors.
  - Payload: JSON with `message` and optional metadata (`customer_name`, `ticket_type`, `category`).

- **Process:**
  - Ingest: Flask API normalizes payloads and forwards them to the analyzer.
  - Sentiment Analysis: Uses the VADER lexicon via `SentimentAnalyzer` to compute sentiment and compound scores.
  - Emotion & Keyword Detection: Lightweight heuristics detect anger/joy/sadness plus urgent/severe keywords.
  - Prioritization: `TicketPrioritizer` combines compound score, emotion boosts, keyword flags, and ticket-type adjustments to compute a `priority_score` (0..1) and map to a tier:
    - Critical: score >= 0.70
    - High: 0.40 <= score < 0.70
    - Normal: score < 0.40

- **Output:**
  - Stored ticket object: `{ id, message, ticket_type, category, priority, priority_score, emotion, compound, flagged_keywords, reason, status, created_at }` persisted in `support_tickets.db`.
  - Dashboard: displays grouped tickets, metrics, and actions for agents.
  - Integrations: Notifier can send webhooks/Slack/email for critical/high tickets.

## Visual flowchart (Mermaid)
```mermaid
flowchart LR
  UI[User Dashboard / API]
  Ingest[Flask API / Ingest Worker]
  Analyzer[Sentiment Analyzer (VADER)]
  Prioritizer[TicketPrioritizer (keywords, emotion, rules)]
  Store[SQLite TicketStore]
  Dashboard[Support Dashboard (S.E.N.T.R.I)]
  Integrations[Slack / Jira / Email / Webhooks]

  UI --> Ingest --> Analyzer --> Prioritizer --> Store
  Store --> Dashboard
  Prioritizer --> Integrations
```

## Notes & tips
- If you already have a `support_tickets.db` from a prior run and you changed the schema, back it up before starting the server (the app will recreate the DB if missing).
- To test quickly with PowerShell:

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:5000/api/tickets' -Method Post -ContentType 'application/json' -Body (@{ customer_name='QA'; message='The system is down'; ticket_type='support'; category='performance' } | ConvertTo-Json)
```

## Where to look in the code
- Server: `src/support_server.py`
- Dashboard template: `src/templates/support_dashboard.html`
- Prioritizer: `src/vader_sentiment/ticket_prioritizer.py`
- Store: `src/vader_sentiment/ticket_store.py`
- Analyzer & utilities: `src/vader_sentiment/*.py`

---
Updated to S.E.N.T.R.I naming and documentation.
