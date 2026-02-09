def main():
    import sys
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

    analyzer = SentimentIntensityAnalyzer()

    if len(sys.argv) < 2:
        print("Usage: python cli.py <text>")
        sys.exit(1)

    text = ' '.join(sys.argv[1:])
    sentiment_score = analyzer.polarity_scores(text)

    print(f"Sentiment Score: {sentiment_score['compound']}")
    if sentiment_score['compound'] >= 0.05:
        print("Sentiment Type: Positive")
    elif sentiment_score['compound'] <= -0.05:
        print("Sentiment Type: Negative")
    else:
        print("Sentiment Type: Neutral")

if __name__ == "__main__":
    main()