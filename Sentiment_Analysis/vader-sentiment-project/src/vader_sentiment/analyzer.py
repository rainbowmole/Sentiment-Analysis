from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from . import structure, summarizer

class SentimentAnalyzer:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()

    def detect_mode(self, text):
        """
        Auto-detect whether input is a single word, a sentence, or a paragraph.
        """
        sents = structure.split_sentences(text)
        lines = [ln for ln in text.splitlines() if ln.strip()]
        words = structure.split_words(text)
        word_count = sum(1 for t in words if any(c.isalnum() for c in t))
        if len(lines) > 1 or len(sents) > 1:
            return "paragraph"
        if len(sents) == 1 and word_count == 1:
            return "word"
        return "sentence"

    def analyze(self, text, mode=None, structured=True):
        if mode is None:
            mode = self.detect_mode(text)
        result = {"mode": mode, "overall": self.vader.polarity_scores(text)}
        segments = []

        if mode == "word":
            segs = structure.split_words(text)
        elif mode == "sentence":
            segs = structure.split_sentences(text)
        else:
            segs = [text.strip()]

        for s in segs:
            vader_scores = self.vader.polarity_scores(s)
            struct = structure.analyze_with_structure(s, self.vader) if structured and mode != "word" else None
            segments.append({
                "text": s,
                "vader": vader_scores,
                "structure": struct
            })

        result["segments"] = segments
        result["summary"] = summarizer.generate_summary(text, self.vader, mode=mode)
        # new: attach tone/context
        result["context"] = summarizer.detect_tone_context(text, self.vader)
        return result