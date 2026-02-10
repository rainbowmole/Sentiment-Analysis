"""
Ticket prioritization logic for customer support.
Combines emotion detection, urgency keywords, and sentiment intensity.
"""

from . import structure, summarizer

class TicketPrioritizer:
    """
    Prioritizes support tickets based on:
    - Emotion detection (anger, frustration, etc.)
    - Urgency keywords (critical, emergency, down, broken, etc.)
    - Sentiment intensity (compound VADER score)
    """

    # Severity thresholds
    CRITICAL_COMPOUND = -0.7  # Very negative
    HIGH_COMPOUND = -0.3      # Moderately negative
    
    # Urgency keywords that escalate priority
    URGENT_KEYWORDS = {
        "critical", "emergency", "urgent", "asap", "immediately", "broken",
        "down", "not working", "crash", "fail", "failed", "unable", "cannot",
        "help", "help!", "dying", "disaster", "catastrophe", "worst", "terrible",
        "account compromised", "account hacked", "hack", "compromise", "security breach"
    }
    
    # Severe negative keywords (weapons, violence, theft, etc.)
    SEVERE_KEYWORDS = {
        "weapon", "gun", "knife", "bomb", "shoot", "stab", "attack",
        "threat", "threatening", "will hurt", "going to kill",
        "stole", "stolen", "theft", "rob", "robbery", "hacked", "hack", "security breach"
    }
    
    # Anger/frustration emotions
    ANGER_KEYWORDS = {
        "angry", "furious", "enraged", "hate", "disgusted", "frustrated",
        "annoyed", "irritated", "pissed", "mad", "livid", "outraged"
    }

    def __init__(self, analyzer):
        """analyzer: vader_sentiment.analyzer.SentimentAnalyzer instance"""
        self.analyzer = analyzer

    def prioritize(self, text):
        """
        Score and prioritize a support ticket.
        
        Returns:
        {
            'priority': 'critical' | 'high' | 'normal',
            'priority_score': float (0-1),
            'emotion': str or None,
            'compound': float,
            'intensity': str ('very', 'moderately', 'mildly', 'neutral'),
            'urgency_flagged': bool,
            'flagged_keywords': list,
            'reason': str
        }
        """
        # Get base sentiment analysis
        analysis = self.analyzer.analyze(text)
        overall = analysis.get('overall', {})
        compound = overall.get('compound', 0.0)
        
        # Detect context/tone
        context = analysis.get('context', {})
        emotion = context.get('main_emotion')
        
        # Check for severe keywords
        text_lower = text.lower()
        severe_hits = [kw for kw in self.SEVERE_KEYWORDS if kw in text_lower]
        if severe_hits:
            return {
                'priority': 'critical',
                'priority_score': 1.0,
                'emotion': emotion,
                'compound': compound,
                'intensity': 'severe',
                'urgency_flagged': True,
                'flagged_keywords': severe_hits,
                'reason': f'Severe keywords detected: {", ".join(severe_hits)}'
            }
        
        # Check for anger/frustration
        anger_hits = [kw for kw in self.ANGER_KEYWORDS if kw in text_lower]
        is_angry = len(anger_hits) > 0 or emotion == 'anger'
        
        # Check for urgency
        urgency_hits = [kw for kw in self.URGENT_KEYWORDS if kw in text_lower]
        is_urgent = len(urgency_hits) > 0
        
        # Compute priority based on combination
        priority_score = self._compute_priority_score(
            compound,
            is_angry,
            is_urgent,
            anger_hits,
            urgency_hits
        )
        
        # Determine intensity
        if abs(compound) >= 0.6:
            intensity = 'very'
        elif abs(compound) >= 0.25:
            intensity = 'moderately'
        elif abs(compound) > 0:
            intensity = 'mildly'
        else:
            intensity = 'neutral'
        
        # Determine priority tier
        if priority_score >= 0.7:
            priority = 'critical'
        elif priority_score >= 0.4:
            priority = 'high'
        else:
            priority = 'normal'
        
        # Build reason
        reasons = []
        if severe_hits:
            reasons.append(f"Severe keywords: {', '.join(severe_hits)}")
        if is_angry:
            reasons.append(f"Angry/frustrated (emotion: {emotion})")
        if is_urgent:
            reasons.append(f"Urgent keywords: {', '.join(urgency_hits)}")
        if compound <= self.CRITICAL_COMPOUND:
            reasons.append(f"Very negative sentiment ({compound:.2f})")
        elif compound <= self.HIGH_COMPOUND:
            reasons.append(f"Moderately negative sentiment ({compound:.2f})")
        
        reason = " | ".join(reasons) if reasons else "Neutral sentiment"
        
        return {
            'priority': priority,
            'priority_score': priority_score,
            'emotion': emotion,
            'compound': compound,
            'intensity': intensity,
            'urgency_flagged': is_urgent or is_angry,
            'flagged_keywords': list(set(anger_hits + urgency_hits)),
            'reason': reason
        }
    
    def _compute_priority_score(self, compound, is_angry, is_urgent, anger_hits, urgency_hits):
        """
        Compute a priority score (0-1) from sentiment and keyword signals.
        """
        score = 0.0
        
        # Sentiment contribution (0 to 0.4)
        if compound <= self.CRITICAL_COMPOUND:
            score += 0.4
        elif compound <= self.HIGH_COMPOUND:
            score += 0.25
        elif compound < -0.05:
            score += 0.1
        
        # Anger contribution (0 to 0.35)
        if is_angry:
            score += 0.35
        
        # Urgency contribution (0 to 0.25)
        if is_urgent:
            score += min(0.25, len(urgency_hits) * 0.10)  # Increased per-keyword score
        
        return min(score, 1.0)
