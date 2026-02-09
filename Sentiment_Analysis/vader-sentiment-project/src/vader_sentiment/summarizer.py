import re
from . import structure
try:
    import nltk
    NLTK_AVAILABLE = True
except Exception:
    nltk = None
    NLTK_AVAILABLE = False

def sentiment_label(compound):
    if compound >= 0.05:
        return "positive"
    if compound <= -0.05:
        return "negative"
    return "neutral"

def _ensure_nltk_resource(name):
    if not NLTK_AVAILABLE:
        return False
    try:
        nltk.data.find(name)
        return True
    except LookupError:
        try:
            nltk.download(name.split('/')[-1], quiet=True)
            return True
        except Exception:
            return False

def _get_nearest_noun(tokens, target_index):
    if NLTK_AVAILABLE and _ensure_nltk_resource('taggers/averaged_perceptron_tagger'):
        try:
            tags = nltk.pos_tag(tokens)
            for dist in range(0, max(len(tokens), 5)):
                for idx in (target_index - dist, target_index + dist):
                    if 0 <= idx < len(tags) and tags[idx][1].startswith('NN'):
                        return tags[idx][0]
        except Exception:
            pass
    for idx in range(target_index, -1, -1):
        if re.match(r"\w", tokens[idx]):
            return tokens[idx]
    for idx in range(target_index+1, len(tokens)):
        if re.match(r"\w", tokens[idx]):
            return tokens[idx]
    return None

def generate_summary(text, analyzer, mode="structured", sentences_limit=5):
    overall_scores = analyzer.polarity_scores(text)
    overall_label = sentiment_label(overall_scores['compound'])
    lines = [f"Overall sentiment: {overall_label} (compound={overall_scores['compound']:.3f})"]
    sents = structure.split_sentences(text) or [text]
    for si, s in enumerate(sents[:sentences_limit], start=1):
        res = structure.analyze_with_structure(s, analyzer)
        words_info = res["words"]
        if not words_info:
            lines.append(f"Sentence {si}: no strong sentiment words detected.")
            continue
        sorted_words = sorted(enumerate(words_info), key=lambda iv: abs(iv[1]['adjusted']), reverse=True)
        top = sorted_words[:2]
        parts = []
        tokens = structure.split_words(s)
        for idx, info in top:
            w = info['word']
            adj = info['adjusted']
            polarity = "positive" if adj > 0 else ("negative" if adj < 0 else "neutral")
            target = _get_nearest_noun(tokens, idx)
            if target:
                parts.append(f"'{w}' ({polarity}) -> {target}")
            else:
                parts.append(f"'{w}' ({polarity})")
        sent_label = sentiment_label(res["vader_scores"]["compound"])
        lines.append(f"Sentence {si}: mostly {sent_label}. Key: " + "; ".join(parts))
    if len(sents) > sentences_limit:
        lines.append(f"...and {len(sents)-sentences_limit} more sentences omitted.")
    return "\n".join(lines)

def detect_tone_context(text, analyzer, top_k=3):
    """
    Return a small context/tone summary:
      - tone_label: low/neutral/positive/negative with intensity
      - main_emotion: mapped from emotion-lexicon hits (joy/anger/sadness/fear/surprise/disgust) or None
      - emotion_scores: counts/weights per emotion
      - main_targets: nouns likely targeted by sentiment words
      - strong_words: top_k words contributing most to sentiment (adjusted)
    """
    from . import structure as _structure

    # overall VADER
    vs = analyzer.polarity_scores(text)
    compound = vs['compound']
    # intensity buckets
    if abs(compound) >= 0.6:
        intensity = "very"
    elif abs(compound) >= 0.25:
        intensity = "moderately"
    else:
        intensity = "mildly"

    tone_label = "neutral"
    if compound >= 0.05:
        tone_label = f"{intensity} positive"
    elif compound <= -0.05:
        tone_label = f"{intensity} negative"

    # simple emotion lexicon (expand as needed)
    EMO = {
        "joy": {"happy","joy","love","delighted","pleased","glad","excited","enjoy"},
        "anger": {"angry","enraged","furious","hate","annoyed","irritat","rage"},
        "sadness": {"sad","unhappy","depressed","mourn","sorrow","sorry","gloom"},
        "fear": {"afraid","scared","fear","terrified","panic","worried","anxious"},
        "surprise": {"surprise","shocked","astonish","amazed","wow"},
        "disgust": {"disgust","gross","nasty","sick","revolting","repuls"}
    }

    # analyze by sentence and words
    sents = _structure.split_sentences(text) or [text]
    emotion_scores = {k: 0.0 for k in EMO}
    word_hits = []

    for si, s in enumerate(sents):
        struct = _structure.analyze_with_structure(s, analyzer)
        for i, info in enumerate(struct["words"]):
            w = info["word"]
            adj = info["adjusted"]
            lw = w.lower()
            # accumulate by emotion lexicon substring match
            for emo, lex in EMO.items():
                for token in lex:
                    if token in lw:
                        emotion_scores[emo] += abs(adj)
            if abs(adj) > 0.01:
                word_hits.append((abs(adj), w, i, s))

    # pick strongest words
    word_hits.sort(reverse=True)
    strong_words = [{"word": w, "weight": wt} for wt, w, idx, s in word_hits[:top_k]]

    # find likely targets (nearest nouns to top words)
    tokens = _structure.split_words(text)
    targets = []
    if word_hits:
        for wt, w, idx_in_sent, sent in word_hits[:top_k]:
            # find token index of w in sentence tokens
            sent_tokens = _structure.split_words(sent)
            # find first match index
            try:
                t_idx = next(i for i,tok in enumerate(sent_tokens) if tok.lower().startswith(w.lower().strip(".,!?'\"")))
            except StopIteration:
                t_idx = 0
            noun = None
            # try POS-based noun via summarizer helper if available
            try:
                noun = _get_nearest_noun(sent_tokens, t_idx)
            except Exception:
                noun = None
            if noun and noun not in targets:
                targets.append(noun)

    # determine main emotion
    main_emotion = None
    if emotion_scores:
        sorted_em = sorted(emotion_scores.items(), key=lambda kv: kv[1], reverse=True)
        if sorted_em[0][1] > 0:
            main_emotion = sorted_em[0][0]

    return {
        "tone_label": tone_label,
        "compound": compound,
        "intensity": intensity,
        "main_emotion": main_emotion,
        "emotion_scores": emotion_scores,
        "main_targets": targets,
        "strong_words": strong_words
    }