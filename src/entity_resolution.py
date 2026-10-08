"""Building / project entity resolver for listing titles.

Conservative by design: a listing resolves only when
  - the full alias appears verbatim as adjacent tokens (confidence 'exact'), or
  - at least two alias tokens match typo-tolerantly, at least one of them distinctive
    (confidence 'fuzzy').
A single generic word ('jakarta', 'lagoon', 'residence', 'menara') never resolves a
building. If two different projects tie for the best score the listing stays
'unresolved'. The resolver never invents a name.
"""
import difflib
import json
import os
import re
import unicodedata

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY_PATH = os.path.join(BASE_DIR, "data", "property_registry.json")

_WORD = re.compile(r"[a-z0-9]+")
_MIN_TOKEN = 4        # ignore 'u', 'pi', 'lt' noise
_FUZZY_CUTOFF = 0.85  # 'recidence'~'residence' = 0.889, 'manssion'~'mansion' = 0.933

_GENERIC = {
    "apartment", "apartemen", "apartement", "residence", "residences", "condominium", "condo",
    "tower", "menara", "suites", "suite", "city", "park", "view", "garden", "gardens", "hill",
    "hills", "place", "point", "mansion", "square", "plaza", "village", "terrace", "grand", "the",
    "royale", "central", "icon", "premier", "premium", "living", "signature", "jakarta", "depok",
    "bogor", "bekasi", "tangerang", "serpong", "bsd", "cikarang", "karawaci", "kemayoran", "lagoon",
    "spring", "springs", "estate", "estates", "court", "courts", "house", "houses", "baru",
    "barat", "timur", "utara", "selatan", "tengah", "raya", "jaya", "indah", "permai", "asri",
}


def normalize(text):
    s = unicodedata.normalize("NFKD", str(text or "")).encode("ascii", "ignore").decode("ascii")
    s = s.lower().replace("'", "").replace("\u2019", "")
    s = re.sub(r"[-_/|,.()\[\]!]+", " ", s)
    return " ".join(_WORD.findall(s))


def load_registry(path=REGISTRY_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


_REG = None
_ALL_ALIASES = None
_FIRST_INDEX = None  # normalized first token -> [alias entry]


def _aliases():
    """List of (alias_tokens, project_id, project_name) for all normalized aliases."""
    global _REG, _ALL_ALIASES, _FIRST_INDEX
    if _REG is None:
        _REG = load_registry()
        _ALL_ALIASES = []
        _FIRST_INDEX = {}
        for p in _REG["projects"]:
            for alias in p["aliases"]:
                toks = normalize(alias).split()
                if toks:
                    entry = (toks, p["id"], p["name"])
                    _ALL_ALIASES.append(entry)
                    _FIRST_INDEX.setdefault(toks[0], []).append(entry)
    return _ALL_ALIASES


def _candidate_aliases(hay_tokens):
    """Only aliases whose first token plausibly appears in the title."""
    hay_set = set(hay_tokens)
    out, seen = [], set()
    for htok in hay_set:
        for key in _FIRST_INDEX:
            if key == htok or (len(key) >= _MIN_TOKEN and len(htok) >= _MIN_TOKEN and _similar(htok, key) >= _FUZZY_CUTOFF):
                for entry in _FIRST_INDEX[key]:
                    if id(entry) not in seen:
                        seen.add(id(entry))
                        out.append(entry)
    return out


def _similar(a, b):
    """Cheap similarity: exact fast path, length-ratio gate, else difflib."""
    if a == b:
        return 1.0
    la, lb = len(a), len(b)
    if max(la, lb) > 2 * min(la, lb):
        return 0.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def _match_alias(tokens, hay, hay_tokens):
    """Return (score, ratio). score 0 means no match.

    Verbatim: the whole alias appears as adjacent tokens.
    Fuzzy:    the alias appears as an adjacent run of tokens matched from the SAME
              start position (each exact or typo); at least 2 tokens, with at least
              one distinctive (non-generic) token matched. Scattered words across a
              title are NOT a match - that is what wrongly merged half the dataset
              on a long marketing alias ('golf view apartment for lease near jis').
    """
    if len(tokens) >= 2:
        if f" {' '.join(tokens)} " in hay:
            return len(tokens), 1.0

    toks2 = [t for t in tokens if len(t) >= _MIN_TOKEN or t in ("u",)]
    if not toks2:
        # alias made only of tiny tokens (e.g. 'pir 1'): verbatim or nothing
        return 0, 0.0
    first = toks2[0]
    best_run, best_ratio = [], 0.0
    for start in range(len(hay_tokens)):
        # cheap gate: the run must start with a token resembling the first alias token
        if len(first) >= _MIN_TOKEN and _similar(hay_tokens[start], first) < _FUZZY_CUTOFF:
            continue
        run = []
        hi = start
        ti = 0
        while ti < len(toks2) and hi < len(hay_tokens):
            atok = toks2[ti]
            r = 1.0 if hay_tokens[hi] == atok else _similar(hay_tokens[hi], atok)
            if len(atok) < _MIN_TOKEN and r != 1.0:
                break  # short tokens must match exactly
            if r >= _FUZZY_CUTOFF:
                run.append((atok, r))
                ti += 1
                hi += 1
            else:
                break
        if len(run) > len(best_run) or (len(run) == len(best_run) and run and sum(x[1] for x in run) / len(run) > best_ratio):
            best_run, best_ratio = run, (sum(x[1] for x in run) / len(run) if run else 0.0)

    if len(best_run) < min(2, len(toks2)):
        return 0, 0.0
    matched_distinctive = [a for a, _ in best_run if a not in _GENERIC]
    if not matched_distinctive:
        return 0, 0.0
    if len(tokens) == 1:
        t = tokens[0]
        if t in _GENERIC or len(t) < _MIN_TOKEN:
            return 0, 0.0
        return 1, best_ratio
    # stronger: prefer matches covering more of the alias
    coverage = len(best_run) / len(toks2)
    return len(best_run) + coverage, best_ratio


def _unresolved():
    return {"project_id": None, "name": None, "confidence": "unresolved", "matched_alias": None}


def resolve(*texts):
    """Return {project_id, name, confidence, matched_alias}; confidence: exact | fuzzy | unresolved."""
    hay = " " + " ".join(normalize(t) for t in texts if t) + " "
    hay_tokens = hay.split()

    best = {}  # pid -> (score, ratio, name, alias)
    _aliases()  # ensures _FIRST_INDEX is built
    for toks, pid, name in _candidate_aliases(hay_tokens):
        score, ratio = _match_alias(toks, hay, hay_tokens)
        if score <= 0:
            continue
        prev = best.get(pid)
        if prev is None or (score, ratio) > (prev[0], prev[1]):
            best[pid] = (score, ratio, name, " ".join(toks))
    if not best:
        return _unresolved()

    top_score = max(v[0] for v in best.values())
    top = [(pid, v) for pid, v in best.items() if v[0] == top_score]
    if len(top) > 1:
        top_ratio = max(v[1] for _, v in top)
        top = [(pid, v) for pid, v in top if v[1] == top_ratio]
        if len(top) != 1:
            return _unresolved()
    pid, (_, ratio, name, alias) = top[0]
    return {
        "project_id": pid,
        "name": name,
        "confidence": "exact" if ratio == 1.0 else "fuzzy",
        "matched_alias": alias,
    }
