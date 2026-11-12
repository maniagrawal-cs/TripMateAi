"""LLM, RAG retrieval, quiz/mission generation and photo verification. Every function has a fallback."""
import os, re, json, base64, logging, httpx
from .kb import TAJ, QUIZ_BANK, MISSIONS
log = logging.getLogger("TripMateAi.ai")

def llm(prompt, system=None, image=None, mime=None, json_mode=False):
    key = os.getenv("GEMINI_API_KEY")
    if not key: return None
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    parts = [{"text": prompt}]
    if image: parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(image).decode()}})
    body = {"contents": [{"role": "user", "parts": parts}]}
    if system: body["system_instruction"] = {"parts": [{"text": system}]}
    if json_mode: body["generationConfig"] = {"responseMimeType": "application/json"}
    try:
        r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                       params={"key": key}, json=body, timeout=60)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        log.warning("AI call failed: %s", e); return None

def parse_json(text):
    if not text: return None
    try: return json.loads(re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip())
    except Exception: return None

# ---- RAG: simple keyword retrieval (replace with embeddings + FAISS for bigger knowledge bases) ----
def retrieve(query, k=3):
    q = set(re.findall(r"[a-z]{3,}", query.lower()))
    scored = []
    for name, text in TAJ["sections"].items():
        words = set(re.findall(r"[a-z]{3,}", (name + " " + text).lower()))
        scored.append((len(q & words), name, text))
    scored.sort(reverse=True)
    return [(n, t) for s, n, t in scored[:k] if s > 0]

def chat(message, history, user, trip):
    hits = retrieve(message)
    ctx = "\n".join(f"[{n}] {t}" for n, t in hits)
    system = (f"You are TripMateAi, a friendly learning companion on a school trip to {TAJ['name']}. "
              f"Student age {user.age}, class {user.class_name}. Explain simply for that age. "
              "Use ONLY the CONTEXT for destination facts. If it lacks the answer, say you are not sure and suggest asking the teacher. "
              "End with 'Related topics:' (2-3 school subjects) and 'Challenge:' (one observation task). Cite section names in brackets. "
              "Reply in the language the student writes in.")
    convo = "\n".join(f"{m.role}: {m.content}" for m in history[-8:])
    out = llm(f"CONTEXT:\n{ctx or 'none'}\n\nCONVERSATION:\n{convo}\n\nStudent: {message}", system=system)
    if out: return out, [n for n, _ in hits]
    if hits:
        return (f"(AI is offline, showing stored notes.) {hits[0][1]}\n\nRelated topics: History, Art, Mathematics.\nChallenge: Spot something symmetrical.", [hits[0][0]])
    return "I'm not sure about that, and I don't want to guess. Try asking your teacher or rephrasing.", []

def generate_quiz(subject, difficulty, n):
    ctx = "\n".join(TAJ["sections"].values())
    out = parse_json(llm(
        f"From CONTEXT only, write {n} quiz questions about the Taj Mahal for subject '{subject}', difficulty '{difficulty}'. "
        "Mix types mcq (4 options), tf (options ['True','False']), short (options []). Return JSON list of objects with keys "
        "qtype,text,options,answer,explanation,topic. For mcq the answer must exactly equal one option.\nCONTEXT:\n" + ctx, json_mode=True))
    ok = isinstance(out, list) and len(out) >= n and all(isinstance(q, dict) and {"qtype","text","answer"} <= q.keys() for q in out)
    if ok:
        good = [q for q in out if q["qtype"] in ("mcq","tf","short") and (q["qtype"] != "mcq" or q["answer"] in q.get("options", []))]
        if len(good) >= n: return good[:n]
    bank = QUIZ_BANK * (n // len(QUIZ_BANK) + 1)
    return bank[:n]   # fallback keeps the 10-question minimum (repeats only if n > bank size)

def generate_missions(n=3):
    ctx = "\n".join(TAJ["sections"].values())
    out = parse_json(llm(f"Create {n} photo treasure-hunt missions for the Taj Mahal from CONTEXT. JSON list with keys title,task,criteria,hint,points,difficulty.\n{ctx}", json_mode=True))
    if isinstance(out, list) and out and all(isinstance(m, dict) and {"title","task","criteria"} <= m.keys() for m in out):
        return out[:n]
    return MISSIONS[:n]

def verify_photo(mission, img, mime):
    """Returns dict with status in verified|try_again|needs_review. Confidence comes from the model, never invented."""
    out = parse_json(llm(
        f"Mission: {mission.title}. Task: {mission.task}. Criteria: {mission.criteria}\n"
        "Look at the photo strictly against the criteria. Return JSON: is_correct (bool), confidence (0-1), detected_features (list), "
        "explanation (student friendly), learning_fact, hint (what to change if not correct).", image=img, mime=mime, json_mode=True))
    if not out or "is_correct" not in out:
        return dict(status="needs_review", confidence=None, detected_features=[], explanation="AI check unavailable, so your teacher will review this photo.", learning_fact="", hint=mission.hint)
    try: conf = float(out.get("confidence"))
    except (TypeError, ValueError): conf = None
    if conf is not None and conf >= 0.75: status = "verified" if out["is_correct"] else "try_again"
    else: status = "needs_review"
    out.update(status=status, confidence=conf); out.setdefault("hint", mission.hint)
    return out
