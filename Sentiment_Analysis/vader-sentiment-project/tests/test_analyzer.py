import unittest
from vader_sentiment.analyzer import SentimentAnalyzer

class TestSentimentAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = SentimentAnalyzer()

    def test_positive_sentiment(self):
        text = "I love this product! It's amazing."
        score, sentiment_type = self.analyzer.analyze_sentiment(text)
        self.assertGreater(score, 0)
        self.assertEqual(sentiment_type, 'positive')

    def test_negative_sentiment(self):
        text = "I hate this product. It's the worst."
        score, sentiment_type = self.analyzer.analyze_sentiment(text)
        self.assertLess(score, 0)
        self.assertEqual(sentiment_type, 'negative')

    def test_neutral_sentiment(self):
        text = "This product is okay."
        score, sentiment_type = self.analyzer.analyze_sentiment(text)
        self.assertEqual(score, 0)
        self.assertEqual(sentiment_type, 'neutral')

    def test_mixed_sentiment(self):
        text = "I love the design, but I hate the battery life."
        score, sentiment_type = self.analyzer.analyze_sentiment(text)
        self.assertNotEqual(score, 0)
        self.assertIn(sentiment_type, ['positive', 'negative'])

if __name__ == '__main__':
    unittest.main()