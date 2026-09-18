<!-- prose-check: catalog -- this page quotes the bad shapes on purpose -->

# LLM Prose Tells

> **Maintained by Claude.** Ported 2026-09-15 from the sibling repo `../snk-geranium`
> (`tools/gcheck/authorship/prose.py` rule A10, `docs/reference/llm-prose-tells.md`,
> and the platform style guide "Recognizing LLM-Generated Files"). Those classes come
> from reviewers rejecting real submissions for reading like a model wrote them.
> Enforced here by [tasks/prose.py](../tasks/prose.py).

## Why this matters for Anton

Anton annotations are prose a human reviewer reads: eight dimension reasons per side,
a rubric reason per side, and a comparative rationale. Reviewers on the sibling
project rejected work with headings like *"Remove unclear LLM slang"* and *"LLM
sounding language needs to be eliminated"*. The same reader is auditing these
annotations.

The mechanism a Geranium reviewer described is a rhythm, not a word list:

> messy workplace detail → artificial shorthand/idiom → analytical requirement

The idiom in the middle is the tell: it carries no information and exists to sound
lived-in. Their second observation applies here too: real workplace writing is
**flatter and more repetitive** than fiction about workplace writing. It repeats the
noun instead of finding a fresh image for it.

For an annotation reason, the standard is simpler still: **every sentence should
carry a fact a reviewer can check** — a record number, a `file:line`, a test name, a
quoted command output. A sentence that carries no checkable fact is usually the
sentence that reads like a model wrote it.

## The classes

Each is checked by `tasks/prose.py` unless marked "read, not checked".

| Class | Example | Fix |
|---|---|---|
| **Tautology** (ERROR) | "Committed work is committed", "policy 6.3 is still policy", "paragraph 8 is the whole story" | State the rule and its consequence |
| **Slogan / aphorism** | "at the end of the day", "the diff speaks for itself", "September is use it or lose it" | State the mechanism or the quantity |
| **Idiom in place of the fact** | "what we leave on the counter" | Name the quantity |
| **not-just-X-but-Y** | "It's not just a refactor, but a rewrite" | Drop the setup, state Y |
| **Hedged filler** (ERROR) | "It is worth noting that…", "It should be noted", "One could argue" | State the finding |
| **Transitional meta-sentence** | "Having reviewed the above, we now turn to…" | Delete it |
| **Text describing itself** (ERROR) | "This analysis summarizes…", "As requested, this document…" | Delete, or use the real title |
| **Pre-counted list** | "There are three key considerations" | List them without the count |
| **Corporate buzzword** | leverage, synergies, holistic, facilitate, utilize | Use the specific verb |
| **Praise pair plus negation** | "a clear, well-structured patch, not vague or incomplete" | Say what it does |
| **Agentless passive** | "Several risks were identified" | Name who did what |
| **Inflated words** | crucial, pivotal, delve into, showcases, seamless | Plain word, or cut |
| **Em dashes** | "B fixed the bug — then ran the tests — twice" | Commas, periods, semicolons, parentheses. **Zero in text typed into Studio** |
| **Three-beat rhythm** (read, not checked) | detail → idiom → demand, paragraph after paragraph | Cut the middle beat |
| **Uniform register** (read, not checked) | every reason the same length and shape | Vary with what the evidence supports |

## How it runs

```bash
python3 tasks/prose.py tasks/<task-id>/notes.md    # one file
python3 tasks/prose.py tasks/ docs/ *.md           # a sweep; directories are walked
python3 tasks/studio.py check tasks/<task-id>      # every annotation reason, plus the evidence rule
```

`studio.py check` scans all 16 dimension reasons, every rubric reason and the
comparative rationale. It applies two extra rules there:

- **zero em dashes** in text typed into Studio, the house rule in the sibling repo
  since a reviewer failed a submission for them;
- **evidence**: a reason that cites no record, file, line, test or quote gets a
  warning. On its first real run it caught four reasons.

What the scanner skips: `studio/`, `trajectories/`, `harbor/`, generated docs
(`docs/10`, `docs/11`) and Mercor's own pages (`docs/01`–`07`). Those quote Studio,
a reviewer or an agent, so their prose is evidence rather than ours.

## Standing rule

Run the prose check on any notes, draft annotation or write-up before handing it
over, and fix the ERROR lines. A clean run is not proof the prose is good: read the
reasons aloud, and cut any sentence that carries no checkable fact.

A hit inside a quotation from a trajectory or a reviewer is expected. Keep the quote,
and say where it came from.
