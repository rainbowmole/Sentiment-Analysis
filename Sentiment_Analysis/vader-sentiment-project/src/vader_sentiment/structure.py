import re
try:
    import nltk
    NLTK_AVAILABLE = True
except Exception:
    nltk = None
    NLTK_AVAILABLE = False

def split_sentences(text):
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [p for p in parts if p]

def split_words(text):
    if NLTK_AVAILABLE:
        try:
            return nltk.word_tokenize(text)
        except LookupError:
            try:
                nltk.download('punkt', quiet=True)
                return nltk.word_tokenize(text)
            except Exception:
                pass
        except Exception:
            pass
    return re.findall(r"\b[\w']+\b|[^\s\w]", text)

def analyze_with_structure(sentence, analyzer, negation_window=3):
    lex = getattr(analyzer, "lexicon", {})
    words = split_words(sentence)
    lower_words = [w.lower() for w in words]

    NEGATIONS = set(["not","n't","no","never","none","nobody","nothing","neither","nowhere","hardly","rarely","scarcely"])
    BOOSTERS = { "very":1.5, "extremely":2.0, "really":1.4, "quite":1.2, "too":1.2, "so":1.4, "absolutely":1.8, "slightly":0.5, "barely":0.5 }
    NEGATION_SCALAR = -0.74

    word_contribs = []
    sentence_score = 0.0
    punct_factor = 1.0
    exclaims = sentence.count('!')
    questions = sentence.count('?')
    punct_factor += min(3, exclaims) * 0.08
    punct_factor += min(2, questions) * 0.03

    for i, w in enumerate(words):
        lw = lower_words[i]
        base = 0.0
        notes = []
        if lw in lex:
            base = lex[lw]
            notes.append("lexicon")
        else:
            stripped = re.sub(r"^[^\w]+|[^\w]+$", "", lw)
            if stripped in lex:
                base = lex[stripped]
                notes.append("lexicon(stripped)")
        adjusted = base
        if i-1 >= 0:
            prev = lower_words[i-1]
            if prev in BOOSTERS:
                adjusted *= BOOSTERS[prev]
                notes.append(f"booster({prev})")
        neg_found = any(lower_words[j] in NEGATIONS for j in range(max(0, i-negation_window), i))
        if neg_found and base != 0:
            adjusted *= NEGATION_SCALAR
            notes.append("negation")
        if base != 0:
            adjusted *= punct_factor
            if punct_factor != 1.0:
                notes.append(f"punct({punct_factor:.2f})")
        sentence_score += adjusted
        word_contribs.append({"word": w, "base": base, "adjusted": adjusted, "notes": notes})

    vader_scores = analyzer.polarity_scores(sentence)
    return {"words": word_contribs, "structure_score": sentence_score, "vader_scores": vader_scores}