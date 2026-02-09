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

# new: expanded contextual detector for fighting, theft, rule-breaking, emergencies, bullying, weapons, etc.
def detect_contextual_issue(text):
    """
    Heuristic detector returning None or a dict:
      {'override':'negative', 'reason': str, 'tags': [...], 'severity': 'low|medium|high'}
    """
    t = text.lower()
    sents = split_sentences(t)

    # keyword groups
    teacher_kw = {"teacher","professor","instructor","lecturer","class","lecture","teaching","speaking","presenting"}
    disruptive_kw = {"play","playing","shout","shouting","talk","talking","laugh","laughing","whisper","phone","text","texting","distract","distracting","noisy","noise","messing","mess"}
    fight_kw = {"fight","fighting","fights","punch","punching","hit","hits","assault","brawl","scuffle","attack","beat","beating","stab","stabbing","kick","kicked"}
    theft_kw = {"steal","stole","stealing","theft","rob","robbed","robbery","thief"}
    rulebreak_kw = {"cheat","cheating","vandal","vandalize","vandalism","break the rule","break rules","skip class","skip school","trespass","graffiti"}
    emergency_kw = {"fire","help","help!","injur","bleed","bleeding","collapsed","unconscious","choking","ambulance","hurt","medical","scream","screaming"}
    bully_kw = {"bully","bullying","harass","harassment","insult","abuse","abusive","taunt","taunting"}
    weapon_kw = {"gun","knife","weapon","firearm","bomb","shoot","shooting","knife","blade"}

    tags = set()
    reason = None
    severity = "medium"

    # quick urgent/emergency detection
    for kw in emergency_kw:
        if kw in t:
            tags.add("emergency")
            reason = f"Emergency-related keyword detected: '{kw}'"
            severity = "high"
            return {"override":"negative","reason":reason,"tags":sorted(tags),"severity":severity}

    # weapon presence -> high severity
    for kw in weapon_kw:
        if kw in t:
            tags.add("weapon")
            reason = f"Weapon-related keyword detected: '{kw}'"
            severity = "high"
            return {"override":"negative","reason":reason,"tags":sorted(tags),"severity":severity}

    # cross-sentence patterns: teacher + disruptive (classroom complaint)
    for i, s in enumerate(sents):
        if any(k in s for k in teacher_kw):
            for j, s2 in enumerate(sents):
                if i == j: continue
                if any(d in s2 for d in disruptive_kw):
                    tags.update(["teacher_context","disruption"])
                    reason = f"Teacher context (sentence {i+1}) and disruptive behavior (sentence {j+1}): \"{s2.strip()}\""
                    severity = "medium"
                    return {"override":"negative","reason":reason,"tags":sorted(tags),"severity":severity}

    # cross-sentence detection for fighting, theft, bullying, rule-breaking
    for i, s in enumerate(sents):
        if any(f in s for f in fight_kw):
            tags.add("fighting")
            reason = f"Fighting/physical altercation mentioned in sentence {i+1}: \"{s.strip()}\""
            severity = "high"
            return {"override":"negative","reason":reason,"tags":sorted(tags),"severity":severity}
        if any(th in s for th in theft_kw):
            tags.add("theft")
            reason = f"Theft-related activity mentioned in sentence {i+1}: \"{s.strip()}\""
            severity = "high"
            return {"override":"negative","reason":reason,"tags":sorted(tags),"severity":severity}
        if any(b in s for b in bully_kw):
            tags.add("bullying")
            reason = f"Bullying/harassment mentioned in sentence {i+1}: \"{s.strip()}\""
            severity = "medium"
            return {"override":"negative","reason":reason,"tags":sorted(tags),"severity":severity}
        if any(r in s for r in rulebreak_kw):
            tags.add("rule_breaking")
            reason = f"Rule-breaking related phrase in sentence {i+1}: \"{s.strip()}\""
            severity = "medium"
            return {"override":"negative","reason":reason,"tags":sorted(tags),"severity":severity}

    # within-sentence contrast: "while/when/as" patterns e.g. "while the teacher is speaking ... boys ... playing"
    for s in sents:
        if any(conj in s for conj in (" while ", " when ", " as ", " whilst ")):
            for conj in (" while ", " when ", " as ", " whilst "):
                if conj in s:
                    a, b = s.split(conj, 1)
                    a = a.strip(); b = b.strip()
                    # teacher + disruption
                    if (any(k in a for k in teacher_kw) and any(d in b for d in disruptive_kw)) or (any(k in b for k in teacher_kw) and any(d in a for d in disruptive_kw)):
                        tags.update(["teacher_context","disruption"])
                        reason = f"Contrast clause detected: \"{s.strip()}\""
                        severity = "medium"
                        return {"override":"negative","reason":reason,"tags":sorted(tags),"severity":severity}
                    # fighting contrast or theft within clause
                    if (any(f in a for f in fight_kw) or any(f in b for f in fight_kw)):
                        tags.add("fighting")
                        reason = f"Fighting mentioned in contrast clause: \"{s.strip()}\""
                        severity = "high"
                        return {"override":"negative","reason":reason,"tags":sorted(tags),"severity":severity}

    # positional + disruptive -> likely complaint / negative context
    if re.search(r"\b(back|rear|front|middle|behind|near)\b", t) and any(d in t for d in disruptive_kw) and any(k in t for k in teacher_kw):
        tags.update(["positional","disruption","teacher_context"])
        reason = "Positional mention with disruptive action detected (e.g., 'back' + 'playing')"
        severity = "medium"
        return {"override":"negative","reason":reason,"tags":sorted(tags),"severity":severity}

    # fallback: if general violent verbs present anywhere
    if any(f in t for f in fight_kw):
        tags.add("fighting")
        reason = "Violent/physical action words detected."
        severity = "high"
        return {"override":"negative","reason":reason,"tags":sorted(tags),"severity":severity}

    # no contextual override
    return None

# integrate detector into CLI/utility flow
def analyze_with_context(text, analyzer):
    res = analyzer.analyze(text)
    ctx = detect_contextual_issue(text)
    if ctx:
        res.setdefault("context", {})
        res["context"]["override"] = ctx
        # mark the overall as overridden and compute an adjusted compound/label
        orig_compound = res.get("overall", {}).get("compound", res.get("compound", 0.0))
        adj = _severity_to_adjusted_compound(ctx.get("severity", "medium"))
        res.setdefault("overall", {})
        res["overall"]["overridden"] = True
        res["overall"]["adjusted_compound"] = adj
        res["overall"]["adjusted_label"] = sentiment_label(adj)
        # keep original for reference
        res["overall"]["original_compound"] = orig_compound
        res["overall"]["original_label"] = sentiment_label(orig_compound)
    else:
        # ensure keys exist for consistent printing
        res.setdefault("overall", {})
        res["overall"]["overridden"] = False
        res["overall"]["adjusted_compound"] = res["overall"].get("compound", 0.0)
        res["overall"]["adjusted_label"] = sentiment_label(res["overall"].get("compound", 0.0))
        res["overall"]["original_compound"] = res["overall"].get("compound", 0.0)
        res["overall"]["original_label"] = sentiment_label(res["overall"].get("compound", 0.0))
    return res

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
    ov = res.get("context", {}).get("override")
    if ov:
        tags = ", ".join(ov.get("tags", []))
        print(f"CONTEXT OVERRIDE: {ov.get('severity','').upper()} {ov.get('override','').upper()}  Tags: {tags}")
        print(f"  Reason: {ov.get('reason')}")
        print("")
        # show both original and adjusted overall clearly
        o = res['overall']
        print("=== OVERALL (original -> adjusted due to context) ===")
        print(f"  original: {o.get('original_compound'):.3f} -> {o.get('original_label')}")
        print(f"  adjusted: {o.get('adjusted_compound'):.3f} -> {o.get('adjusted_label')}")
    else:
        o = res['overall']
        print("\n--- OVERALL ---")
        print(f"compound: {o.get('compound', o.get('original_compound',0.0)):.3f} -> {o.get('adjusted_label')}")

    print("\n=== SUMMARY ===")
    print(res.get('summary',''))

    print("\n--- SEGMENTS ---")
    for i, seg in enumerate(res['segments'], start=1):
        print(f"\n[{i}] {seg['text']}")
        v = seg['vader']
        print(f"  vader: compound={v['compound']:.3f}, pos={v['pos']:.3f}, neu={v['neu']:.3f}, neg={v['neg']:.3f}")
        # show structure only if it has anything meaningful (non-zero base or notes)
        if seg.get('structure'):
            s = seg['structure']
            # determine if any word row has non-zero base or notes
            meaningful = False
            for w in s['words']:
                try:
                    base = w[1] if not isinstance(w, dict) else w.get('base', 0)
                    notes = w[3] if not isinstance(w, dict) else w.get('notes') or w.get('notes', [])
                except Exception:
                    base = 0
                    notes = []
                if base != 0 or (notes and len(notes) > 0):
                    meaningful = True
                    break
            if meaningful:
                print(f"  structure_score={s['structure_score']:.3f}")
                for w in s['words'][:8]:
                    if isinstance(w, dict):
                        if w.get('base', 0) == 0 and not (w.get('notes') or w.get('adjusted', 0)):
                            continue
                        print(f"    {w.get('word',''):12} base={w.get('base',0):6.3f} adj={w.get('adjusted',0):7.3f} {','.join(w.get('notes',[]))}")
                    else:
                        try:
                            word, base, adjusted, notes = w
                            if base == 0 and not notes:
                                continue
                            notes_str = ",".join(notes) if isinstance(notes, (list,tuple)) else str(notes)
                            print(f"    {word:12} base={base:6.3f} adj={adjusted:7.3f} {notes_str}")
                        except Exception:
                            print(f"    {w}")
            else:
                # concise note when nothing interesting found
                print("  (no significant per-word contributions)")

def _severity_to_adjusted_compound(sev):
    """
    Map heuristic severity to a conservative negative compound score used
    when a contextual override is applied.
    """
    return {"low": -0.30, "medium": -0.60, "high": -0.90}.get(sev, -0.60)

def main():
    analyzer = SentimentAnalyzer()
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
        res = analyze_with_context(text, analyzer)
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
        res = analyze_with_context(text, analyzer)
        print_cli_result(res)

if __name__ == "__main__":
    main()