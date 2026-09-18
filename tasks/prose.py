"""LLM prose tells in anything we write: notes, drafts and annotation reasons.

    python3 tasks/prose.py <path…>        # scan .md / .txt files (a directory is walked)
    python3 tasks/prose.py tasks/<id>     # that task's notes, drafts and Studio reasons

Ported 2026-09-15 from ../snk-geranium (`tools/gcheck/authorship/prose.py`, rule A10,
and `docs/reference/llm-prose-tells.md`), whose classes come from reviewers rejecting
submissions for reading like a model wrote them, plus the platform style guide's prose
table ("Recognizing LLM-Generated Files"). docs/12-llm-prose-tells.md has the classes
and the fixes.

ERROR is a shape a reviewer has rejected on sight. WARN is worth re-reading aloud.
This is a pattern net, not a substitute for reading the text: a clean run does not
mean the prose is good, and a hit on a quoted phrase from a trajectory is expected —
quote it and move on.
"""

import re
import sys
from pathlib import Path

# (id, severity, regex, what it is, the fix)
CATALOG = [
    # ---- restatement and slogans: the highest-confidence tells ----------------------
    ("tautology", "ERROR", re.compile(r"\b(\w{4,})\s+(?:is|are)\s+(?:still\s+|just\s+|always\s+)?\1\b", re.I),
     "tautology (X is X)", "state the rule and its consequence instead"),
    ("tautology", "ERROR", re.compile(r"\b(?:is|are)\s+the\s+whole\s+story\b", re.I),
     "tautology", "name what the evidence shows"),
    # The head noun restated as the predicate: "Committed work is committed",
    # "policy 6.3 is still policy". The gap stays on one line, or it matches across a
    # paragraph break into an unrelated list item.
    ("tautology", "ERROR", re.compile(r"\b(\w{5,})\b(?:[\w.\-]|[^\S\n]){0,20}?[^\S\n]+(?:is|are)\s+"
                                      r"(?:still\s+|just\s+|always\s+)?\1\b", re.I),
     "tautology (head noun restated)", "state the rule and its consequence instead"),
    ("slogan", "WARN", re.compile(r"\b(?:at the end of the day|the name of the game|moves? the needle"
                                  r"|low.hanging fruit|speaks? for itself|tells? the (?:whole )?story"
                                  r"|is where the (?:money|pain|trouble) (?:is|hurts?|lands?))\b", re.I),
     "slogan standing in for the fact", "state the mechanism or the quantity"),
    ("antithesis", "WARN", re.compile(r"\b(?:it|this|that)(?:'s| is| was)\s+not\s+(?:just|only|merely)\b"
                                      r"|\bnot\s+(?:just|only|merely)\s+\w+[^.;\n]{0,50}\bbut\b", re.I),
     "not-just-X-but-Y antithesis", "drop the setup and state Y"),
    ("triad", "WARN", re.compile(r"\b(\w+), (\w+),? and (\w+)[.,]\s+(?:That|This|These)\b"),
     "three-beat list closed by a summary sentence", "cut the summary or the list"),

    # ---- hedging and meta-commentary ------------------------------------------------
    ("hedging", "ERROR", re.compile(r"\bit (?:is|'s) (?:worth (?:noting|mentioning)|important to (?:note|consider|remember))\b"
                                    r"|\bit should be noted\b|\bone could argue\b|\bit may be worth\b", re.I),
     "hedged filler", "state the finding directly"),
    ("meta", "WARN", re.compile(r"\bhaving (?:reviewed|established|examined|covered)\b"
                                r"|\bwith (?:this|that) (?:context|in mind)\b"
                                r"|\bas (?:outlined|discussed|noted) (?:above|earlier|previously)\b"
                                r"|\bthe (?:sections?|paragraphs?) (?:that follow|below)\b"
                                r"|\bthe following sections?\b", re.I),
     "transitional meta-sentence", "delete it; the next sentence carries itself"),
    ("self-describing", "ERROR", re.compile(r"\bthis (?:document|report|memo|note|annotation|analysis|summary) "
                                            r"(?:provides|presents|summari[sz]es|outlines|contains|walks through|is organi[sz]ed)\b"
                                            r"|\bas requested,? (?:this|the)\b", re.I),
     "text describing itself", "delete the sentence, or give the thing its real title"),
    ("pre-counted", "WARN", re.compile(r"\bthere are (?:two|three|four|five|six|\d+) (?:key |main |primary |major )?"
                                       r"(?:considerations|factors|drivers|reasons|issues|points|takeaways|findings|steps)\b"
                                       r"|\b(?:two|three|four|five|six|\d+) key (?:considerations|factors|drivers|reasons"
                                       r"|issues|points|takeaways|findings)\b", re.I),
     "pre-counted list", "just list them; don't announce the count"),

    # ---- register ------------------------------------------------------------------
    ("buzzword", "WARN", re.compile(r"\b(?:leverag(?:e|ing|es)|synerg\w+|holistic|best practices"
                                    r"|stakeholder alignment|facilitates?|utili[sz]es?)\b", re.I),
     "corporate buzzword", "use the specific verb: use, run, call, write"),
    ("filler-adjectives", "WARN", re.compile(r",\s+not\s+\w+\s+(?:or|nor)\s+\w+\b", re.I),
     "praise pair closed by a negation", "say what it does, not what it avoids"),
    ("passive-hedge", "WARN", re.compile(r"\b(?:opportunities|challenges|risks|issues|concerns|gaps) "
                                         r"(?:have been|were|was) (?:identified|noted|observed|found)\b", re.I),
     "agentless passive", "name who did what"),
    ("emphatic", "WARN", re.compile(r"\b(?:crucial|pivotal|vital|paramount|delve into|underscore[sd]?"
                                    r"|showcas(?:e|es|ing)|robustly|seamless(?:ly)?)\b", re.I),
     "inflated word", "plain word, or cut it"),
]

EM_DASH = "—"
# A reason cites something checkable: a record, a file, a line, a test, a quote.
EVIDENCE = re.compile(r"record \d+|\[\d+\]|\bstep \d+|\bline \d+|:\d+\b|\b\w+\.(?:py|ts|tsx|js|jsx|c|h|sh|json|toml|md|yml|yaml)\b"
                      r"|\btest_\w+|\b\w+\(\)|`[^`]+`|\"[^\"]{8,}\"", re.I)


# Ordinary English the restatement patterns catch by accident.
TAUTOLOGY_OK = re.compile(r"\bwhich(?: \w+)? is which\b|\bwhat(?: \w+)? is what\b|\bwho(?: \w+)? is who\b", re.I)
# A restatement is one clause. Once the span crosses a sentence or clause boundary the
# repeat is ordinary English ("graded by pass rate. It is graded by ...").
TAUTOLOGY_SPAN = re.compile(r"[.;:!?]")


def scan(text, *, studio_text=False):
    """Findings as (severity, id, label, fix, line_number, matched text)."""
    out = []
    for cid, sev, rx, label, fix in CATALOG:
        for m in rx.finditer(text):
            if cid == "tautology" and (TAUTOLOGY_OK.search(m.group(0))
                                      or TAUTOLOGY_SPAN.search(m.group(0))):
                continue
            line = text.count("\n", 0, m.start()) + 1
            out.append((sev, cid, label, fix, line, m.group(0).strip()[:70]))
    dashes = text.count(EM_DASH)
    if dashes:
        words = max(len(text.split()), 1)
        per_k = 1000 * dashes / words
        # Studio-entered text: the house rule from ../snk-geranium is zero. Elsewhere it
        # is density that reads as LLM-styled, not the occasional dash.
        if studio_text or (dashes >= 3 and per_k >= 8):
            sev = "ERROR" if studio_text else "WARN"
            out.append((sev, "em-dash", f"{dashes} em dash(es) ({per_k:.0f}/1000 words)",
                        "use commas, periods, semicolons or parentheses", 0, EM_DASH))
    return sorted(out, key=lambda f: (f[4], f[1]))


def check_reason(text):
    """Findings for one annotation reason, plus the evidence rule."""
    out = scan(text, studio_text=True)
    if text.strip() and not EVIDENCE.search(text):
        out.append(("WARN", "no-evidence", "cites no record, file, line, test or quote",
                    "point at the trajectory record or the code", 0, text.strip()[:70]))
    return out


# Files that quote Studio, a reviewer or an agent verbatim. Their prose is evidence,
# not ours, so scanning them only produces noise. docs/01-07 are Mercor's own pages.
GENERATED = re.compile(r"^> ?\*\*Generated by|^Generated by `tasks/studio\.py"
                       r"|^<!-- prose-check: catalog", re.M)


def is_ours(path):
    if any(part in ("studio", "trajectories", "harbor", "archived") for part in path.parts):
        return False
    if re.match(r"0[1-7]-", path.name):  # the project docs, written by Mercor
        return False
    return not GENERATED.search(path.read_text(encoding="utf-8", errors="ignore")[:2000])


def scan_path(path):
    if path.is_dir():
        return [p for p in sorted(path.rglob("*")) if p.suffix in (".md", ".txt") and is_ours(p)]
    return [path] if path.suffix in (".md", ".txt") else []


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    errors = warns = 0
    for arg in sys.argv[1:]:
        for f in scan_path(Path(arg)):
            findings = scan(f.read_text(encoding="utf-8", errors="ignore"))
            if not findings:
                continue
            print(f"\n{f}")
            for sev, cid, label, fix, line, hit in findings:
                errors += sev == "ERROR"
                warns += sev == "WARN"
                where = f":{line}" if line else ""
                print(f"  {sev:5} {cid}{where}: {label} — {hit!r}\n        fix: {fix}")
    print(f"\n{errors} error(s), {warns} warning(s) — docs/12-llm-prose-tells.md")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
