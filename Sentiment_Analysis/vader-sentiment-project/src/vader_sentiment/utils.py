def load_data(file_path):
    """Load text data from a specified file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def preprocess_text(text):
    """Clean and prepare text for sentiment analysis."""
    # Convert to lowercase
    text = text.lower()
    # Remove any unwanted characters or punctuation
    text = ''.join(char for char in text if char.isalnum() or char.isspace())
    return text.strip()