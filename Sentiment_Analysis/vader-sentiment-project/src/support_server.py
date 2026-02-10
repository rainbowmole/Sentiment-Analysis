"""
Flask API server for ticket management and prioritization.
Run with: python support_server.py
"""

import traceback
import logging
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import webbrowser

# Import support prioritization modules
from vader_sentiment import SentimentAnalyzer
from vader_sentiment.ticket_prioritizer import TicketPrioritizer
from vader_sentiment.ticket_store import TicketStore

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__, template_folder="templates", static_folder="static")
CORS(app)

# Initialize analyzer and prioritizer
analyzer = SentimentAnalyzer()
prioritizer = TicketPrioritizer(analyzer)
store = TicketStore(db_path="support_tickets.db")

# ============ ROUTES ============

@app.route("/")
def index():
    """Serve the dashboard."""
    return render_template("support_dashboard.html")

@app.route("/api/tickets", methods=["GET"])
def get_tickets():
    """Get all tickets, grouped by priority."""
    app.logger.debug("GET /api/tickets")
    try:
        grouped = store.get_tickets_by_priority()
        stats = store.get_stats()
        return jsonify({
            'success': True,
            'tickets': grouped,
            'stats': stats
        })
    except Exception as e:
        app.logger.exception("Error fetching tickets")
        return jsonify({'error': str(e)}), 500

@app.route("/api/tickets/<int:ticket_id>", methods=["GET"])
def get_ticket(ticket_id):
    """Get a single ticket by ID."""
    app.logger.debug(f"GET /api/tickets/{ticket_id}")
    try:
        ticket = store.get_ticket(ticket_id)
        if not ticket:
            return jsonify({'error': 'Ticket not found'}), 404
        return jsonify({'success': True, 'ticket': ticket})
    except Exception as e:
        app.logger.exception("Error fetching ticket")
        return jsonify({'error': str(e)}), 500

@app.route("/api/tickets", methods=["POST"])
def submit_ticket():
    """Submit a new support ticket or suggestion."""
    app.logger.debug("POST /api/tickets")
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    customer_name = data.get("customer_name", "Anonymous").strip()
    ticket_type = data.get("ticket_type", "support").strip().lower()  # 'support' or 'suggestion'
    category = data.get("category", "").strip() or None
    
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400
    
    # Validate ticket type
    if ticket_type not in ('support', 'suggestion', 'recommendation'):
        return jsonify({"error": "Invalid ticket_type. Must be: support, suggestion, or recommendation"}), 400
    
    try:
        # Prioritize the ticket
        priority_data = prioritizer.prioritize(message)
        
        # For suggestions/recommendations, lower the priority by default (unless they're very strong)
        if ticket_type in ('suggestion', 'recommendation'):
            if priority_data['priority'] == 'normal':
                priority_data['priority_score'] *= 0.5  # Reduce score for suggestions
            # Keep critical/high but adjust reason
            priority_data['reason'] = f"[{ticket_type.upper()}] {priority_data['reason']}"
        
        # Store the ticket
        ticket_id = store.add_ticket(
            message, 
            customer_name, 
            priority_data,
            ticket_type=ticket_type,
            category=category
        )
        
        app.logger.info(f"Created {ticket_type} #{ticket_id}: {priority_data['priority']}")
        
        # Return the ticket with priority info
        ticket = store.get_ticket(ticket_id)
        return jsonify({
            'success': True,
            'ticket_id': ticket_id,
            'ticket_type': ticket_type,
            'priority_data': priority_data,
            'ticket': ticket
        }), 201
    except Exception as e:
        app.logger.exception("Error creating ticket")
        tb = traceback.format_exc()
        return jsonify({"error": str(e), "traceback": tb}), 500

@app.route("/api/tickets/<int:ticket_id>/status", methods=["PATCH"])
def update_ticket_status(ticket_id):
    """Update ticket status."""
    app.logger.debug(f"PATCH /api/tickets/{ticket_id}/status")
    data = request.get_json() or {}
    status = data.get("status", "").strip()
    
    valid_statuses = ['new', 'in-progress', 'resolved']
    if status not in valid_statuses:
        return jsonify({"error": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"}), 400
    
    try:
        store.update_ticket_status(ticket_id, status)
        ticket = store.get_ticket(ticket_id)
        return jsonify({'success': True, 'ticket': ticket})
    except Exception as e:
        app.logger.exception("Error updating ticket")
        return jsonify({'error': str(e)}), 500

@app.route("/api/tickets/<int:ticket_id>", methods=["DELETE"])
def delete_ticket(ticket_id):
    """Delete a ticket."""
    app.logger.debug(f"DELETE /api/tickets/{ticket_id}")
    try:
        store.delete_ticket(ticket_id)
        return jsonify({'success': True, 'message': 'Ticket deleted'})
    except Exception as e:
        app.logger.exception("Error deleting ticket")
        return jsonify({'error': str(e)}), 500

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get dashboard statistics."""
    app.logger.debug("GET /api/stats")
    try:
        stats = store.get_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        app.logger.exception("Error fetching stats")
        return jsonify({'error': str(e)}), 500

@app.route("/api/analyze", methods=["POST"])
def analyze_text():
    """Analyze text and return priority without storing."""
    app.logger.debug("POST /api/analyze")
    data = request.get_json() or {}
    text = data.get("text", "").strip()
    
    if not text:
        return jsonify({"error": "Text cannot be empty"}), 400
    
    try:
        analysis = analyzer.analyze(text)
        priority_data = prioritizer.prioritize(text)
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'priority_data': priority_data
        })
    except Exception as e:
        app.logger.exception("Error analyzing text")
        tb = traceback.format_exc()
        return jsonify({"error": str(e), "traceback": tb}), 500

# ============ MAIN ============

if __name__ == "__main__":
    url = "http://127.0.0.1:5000"
    print(f"\nStarting Support Prioritization Server...")
    print(f"Open in browser: {url}")
    print(f"Tickets database: support_tickets.db\n")
    
    webbrowser.open_new_tab(url)
    app.run(host="127.0.0.1", port=5000, debug=True)
