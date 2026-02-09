from vader_sentiment import SentimentAnalyzer
from vader_sentiment import structure
import sys
import re
try:
    import nltk
    NLTK_AVAILABLE = True
except Exception:
    nltk = None
    NLTK_AVAILABLE = False

def show_pie(scores, text):
    try:
        import matplotlib.pyplot as plt
    except Exception:
        print("matplotlib is required to show charts. Install with: python -m pip install matplotlib")
        return

    labels = ['positive', 'neutral', 'negative']
    sizes = [scores['pos'], scores['neu'], scores['neg']]
    colors = ['#66c2a5', '#8da0cb', '#fc8d62']
    explode = (0.05, 0.05, 0.05)

    plt.figure(figsize=(5,5))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90,
            colors=colors, explode=explode, shadow=True)
    plt.title(f"Sentiment breakdown\n\"{text}\"")
    plt.axis('equal')
    plt.show()

def sentiment_label(compound):
    if compound >= 0.05:
        return "positive"
    elif compound <= -0.05:
        return "negative"
    else:
        return "neutral"

def split_sentences(text):
    # simple sentence splitter: splits on . ! ? followed by whitespace
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p for p in parts if p]

def split_words(text):
    # basic word tokenization using nltk for better tokens if available
    if NLTK_AVAILABLE:
        try:
            tokens = nltk.word_tokenize(text)
        except LookupError:
            # try to download 'punkt' once and retry
            try:
                print("NLTK punkt tokenizer not found — downloading...")
                nltk.download('punkt', quiet=True)
                tokens = nltk.word_tokenize(text)
            except Exception:
                tokens = re.findall(r"\b[\w']+\b|[^\s\w]", text)
        except Exception:
            tokens = re.findall(r"\b[\w']+\b|[^\s\w]", text)
    else:
        tokens = re.findall(r"\b[\w']+\b|[^\s\w]", text)
    return tokens

# new: structure-aware per-word analysis
def analyze_with_structure(sentence, analyzer, negation_window=3):
    """
    Returns a dict with:
      - word_contributions: list of (word, base_valence, adjusted_valence, notes)
      - structure_score: sum of adjusted valences (simple aggregator)
      - vader_scores: analyzer.polarity_scores(sentence)
    """
    lex = getattr(analyzer, "lexicon", {})
    words = split_words(sentence)
    lower_words = [w.lower() for w in words]

    # simple lists: can be expanded or loaded from resources
    NEGATIONS = set(["not","n't","no","never","none","nobody","nothing","neither","nowhere","hardly","rarely","scarcely"])
    BOOSTERS = { "very":1.5, "extremely":2.0, "really":1.4, "quite":1.2, "too":1.2, "so":1.4, "absolutely":1.8, "slightly":0.5, "barely":0.5 }
    NEGATION_SCALAR = -0.74  # use VADER-like negation inversion factor

    word_contribs = []
    sentence_score = 0.0

    # punctuation emphasis factor (exclamation/question marks)
    punct_factor = 1.0
    exclaims = sentence.count('!')
    questions = sentence.count('?')
    punct_factor += min(3, exclaims) * 0.08
    punct_factor += min(2, questions) * 0.03

    for i, w in enumerate(words):
        lw = lower_words[i]
        base = 0.0
        notes = []

        # lookup lexicon valence
        if lw in lex:
            base = lex[lw]
            notes.append("lexicon")
        else:
            # try stripped punctuation and simple normalization
            stripped = re.sub(r"^[^\w]+|[^\w]+$", "", lw)
            if stripped in lex:
                base = lex[stripped]
                notes.append("lexicon(stripped)")

        adjusted = base

        # check boosters immediately before current word (1 token)
        if i-1 >= 0:
            prev = lower_words[i-1]
            if prev in BOOSTERS:
                adjusted *= BOOSTERS[prev]
                notes.append(f"booster({prev}={BOOSTERS[prev]})")

        # check negation within window before the word
        neg_found = False
        for j in range(max(0, i-negation_window), i):
            if lower_words[j] in NEGATIONS:
                neg_found = True
                break
        if neg_found and base != 0:
            adjusted *= NEGATION_SCALAR
            notes.append("negation")

        # apply punctuation emphasis
        if base != 0:
            adjusted *= punct_factor
            if punct_factor != 1.0:
                notes.append(f"punct({punct_factor:.2f})")

        sentence_score += adjusted
        word_contribs.append((w, base, adjusted, notes))

    # fallback: also include VADER's own aggregate for comparison
    vader_scores = analyzer.polarity_scores(sentence)

    return {
        "words": word_contribs,
        "structure_score": sentence_score,
        "vader_scores": vader_scores
    }

# small helper to print detailed breakdown
def print_structure_analysis(result):
    print("\n--- STRUCTURE-AWARE WORD CONTRIBUTIONS ---")
    for i, (w, base, adj, notes) in enumerate(result["words"], start=1):
        note_str = ",".join(notes) if notes else ""
        print(f"{i:2d}. {w:15} base={base:6.3f} adj={adj:7.3f} {note_str}")
    print(f"\nstructure_score (sum of adjusted valences): {result['structure_score']:.3f}")
    vs = result["vader_scores"]
    print(f"vader scores: pos={vs['pos']:.3f}, neu={vs['neu']:.3f}, neg={vs['neg']:.3f}, compound={vs['compound']:.3f}")

# new: summary generator (sentence-level and overall)
def _ensure_nltk_resource(name):
    if not NLTK_AVAILABLE:
        return False
    try:
        nltk.data.find(name)
        return True
    except LookupError:
        try:
            print(f"NLTK resource {name} not found — downloading...")
            nltk.download(name.split('/')[-1], quiet=True)
            return True
        except Exception:
            return False

def get_nearest_noun(tokens, target_index):
    """
    Return nearest noun token to target_index using POS tags if available,
    otherwise simple heuristic (previous/next alphabetic token).
    """
    if NLTK_AVAILABLE and _ensure_nltk_resource('taggers/averaged_perceptron_tagger'):
        try:
            tags = nltk.pos_tag(tokens)
            # search outward from target_index
            for dist in range(0, max(len(tokens), 5)):
                for idx in (target_index - dist, target_index + dist):
                    if 0 <= idx < len(tags):
                        if tags[idx][1].startswith('NN'):  # NN, NNS, NNP, NNPS
                            return tags[idx][0]
        except Exception:
            pass
    # fallback: look left then right for an alphanumeric token
    for idx in range(target_index, -1, -1):
        if re.match(r"\w", tokens[idx]):
            return tokens[idx]
    for idx in range(target_index+1, len(tokens)):
        if re.match(r"\w", tokens[idx]):
            return tokens[idx]
    return None

def generate_summary(text, analyzer, mode="structured", sentences_limit=5):
    """
    Produce short textual summary:
      - overall sentiment label
      - per-sentence short statement with main sentiment words and likely target (noun)
    """
    overall_scores = analyzer.polarity_scores(text)
    overall_label = sentiment_label(overall_scores["compound"])
    summary_lines = [f"Overall sentiment: {overall_label} (compound={overall_scores['compound']:.3f})"]

    # prepare sentences
    sents = split_sentences(text)
    if not sents:
        sents = [text]

    for si, s in enumerate(sents[:sentences_limit], start=1):
        res = analyze_with_structure(s, analyzer)
        # pick top 1-2 contributors by absolute adjusted valence
        words_info = res["words"]
        if not words_info:
            summary_lines.append(f"Sentence {si}: no strong sentiment words detected.")
            continue
        sorted_words = sorted(enumerate(words_info), key=lambda iv: abs(iv[1][2]), reverse=True)
        top = sorted_words[:2]
        parts = []
        for idx, (w, base, adj, notes) in top:
            polarity = "positive" if adj > 0 else ("negative" if adj < 0 else "neutral")
            target = get_nearest_noun([tok for tok in split_words(s)], idx)
            if target:
                parts.append(f"'{w}' ({polarity}) -> {target}")
            else:
                parts.append(f"'{w}' ({polarity})")
        sent_label = sentiment_label(res["vader_scores"]["compound"])
        summary_lines.append(f"Sentence {si}: mostly {sent_label}. Key: " + "; ".join(parts))

    if len(sents) > sentences_limit:
        summary_lines.append(f"...and {len(sents)-sentences_limit} more sentences omitted from summary.")

    return "\n".join(summary_lines)

def analyze_segments(text, analyzer, mode):
    segments = []
    if mode == "paragraph":
        segments = [text.strip()]
    elif mode == "sentence":
        segments = split_sentences(text)
    elif mode == "word":
        segments = split_words(text)
    elif mode == "all":
        segments = {
            "paragraph": [text.strip()],
            "sentences": split_sentences(text),
            "words": split_words(text)
        }
    else:
        segments = [text.strip()]

    results = []
    if mode == "all":
        for typ, segs in segments.items():
            results.append((typ, [
                (s, analyzer.polarity_scores(s)) for s in segs
            ]))
    else:
        results = [(s, analyzer.polarity_scores(s)) for s in segments]

    return results

def print_analysis_item(idx, text, scores):
    compound = scores["compound"]
    label = sentiment_label(compound)
    print(f"[{idx}] \"{text}\"")
    print(f"    compound: {compound:.3f} -> {label}")
    print(f"    scores: pos={scores['pos']:.3f}, neu={scores['neu']:.3f}, neg={scores['neg']:.3f}")

def print_cli_result(res):
    print(f"mode: {res['mode']}")
    print("\n--- OVERALL ---")
    o = res['overall']
    print(f"compound: {o['compound']:.3f}, pos={o['pos']:.3f}, neu={o['neu']:.3f}, neg={o['neg']:.3f}")
    print("\n=== SUMMARY ===")
    print(res.get('summary',''))
    print("\n--- SEGMENTS ---")
    for i, seg in enumerate(res['segments'], start=1):
        print(f"\n[{i}] {seg['text']}")
        v = seg['vader']
        print(f"  vader: compound={v['compound']:.3f}, pos={v['pos']:.3f}, neu={v['neu']:.3f}, neg={v['neg']:.3f}")
        if seg.get('structure'):
            s = seg['structure']
            print(f"  structure_score={s['structure_score']:.3f}")
            for w in s['words'][:8]:
                print(f"    {w['word']:12} base={w['base']:6.3f} adj={w['adjusted']:7.3f}")

def main():
    analyzer = SentimentAnalyzer()
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        res = analyzer.analyze(text)
        print_cli_result(res)
        return

    print("Interactive CLI. Type text (empty or 'quit' to exit).")
    while True:
        try:
            text = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break
        if not text or text.lower() == "quit":
            break
        res = analyzer.analyze(text)
        print_cli_result(res)

if __name__ == "__main__":
    main()