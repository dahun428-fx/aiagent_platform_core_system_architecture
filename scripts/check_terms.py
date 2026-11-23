"""Find where the guide uses discouraged words from terms.json, for a person to review in context.

    python scripts/check_terms.py               # list every discouraged word by file and line
    python scripts/check_terms.py --compare main  # also compare numbers and MUST words with a git ref

Nothing here is forbidden: a discouraged word can be right where a concept is first explained.
The script always exits 0 unless terms.json is broken.
"""
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERMS = json.loads((ROOT / "terms.json").read_text(encoding="utf-8"))["terms"]
FILES = sorted((ROOT / "docs/onboarding").glob("*.md")) + [ROOT / "docs/onboarding/scenario.json", ROOT / "portal/interactive.js"] + sorted((ROOT / "examples/build").rglob("*.py"))
NORMS = re.compile(r"MUST NOT|SHOULD NOT|MUST|SHOULD|MAY")


def report():
    total = Counter()
    for term in TERMS:
        hits = []
        for path in FILES:
            for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for word in term["discouraged"]:
                    if word in line:
                        i = line.index(word)
                        hits.append(f"  {path.relative_to(ROOT)}:{n}  …{line[max(0, i - 25):i + 35].strip()}…")
        total[term["canonical"]] = len(hits)
        if hits:
            print(f"{term['canonical']}  (검토할 말: {', '.join(term['discouraged'])})")
            print("\n".join(hits))
    print("\n합계: " + ", ".join(f"{k} {v}" for k, v in total.items() if v) if sum(total.values()) else "검토할 말이 없습니다.")


def facts(text):
    """Numbers and normative words: what a wording change must not move."""
    return Counter(re.findall(r"\d[\d,.]*", text)) + Counter(NORMS.findall(text))


def compare(ref):
    changed = False
    for path in FILES:
        rel = path.relative_to(ROOT).as_posix()
        old = subprocess.run(["git", "show", f"{ref}:{rel}"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        if old.returncode:
            continue
        before, after = facts(old.stdout), facts(path.read_text(encoding="utf-8"))
        if before != after:
            changed = True
            print(f"{rel}: 사라짐 {dict(before - after)} · 생김 {dict(after - before)}")
    print("숫자와 규범어(MUST 등)가 모두 그대로입니다." if not changed else "위 차이가 의도한 것인지 확인하세요.")


if __name__ == "__main__":
    report()
    if "--compare" in sys.argv:
        print()
        compare(sys.argv[sys.argv.index("--compare") + 1])
