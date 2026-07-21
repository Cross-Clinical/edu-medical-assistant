"""Edu Medical Assistant — citation-grounded study modes only."""

from __future__ import annotations

import json
import re
from pathlib import Path

import gradio as gr

from input_guard import DISCLAIMER, guard_input, looks_like_clinical_request

ROOT = Path(__file__).parent
CORPUS = ROOT / "corpus"

PATHWAYS = json.loads((CORPUS / "pathways.json").read_text())
GLOSSARY = json.loads((CORPUS / "glossary.json").read_text())
CASES = json.loads((CORPUS / "cases.json").read_text())
ORIENT = (CORPUS / "orientation_excerpts.md").read_text()

MODES = ["explain_concept", "quiz_me", "compare_pathways"]


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", (text or "").lower()) if len(t) > 2}


def retrieve(query: str, k: int = 4) -> list[tuple[str, str, str]]:
    """Return list of (source_id, title, snippet)."""
    q = _tokens(query)
    scored: list[tuple[float, str, str, str]] = []

    for p in PATHWAYS:
        blob = " ".join([p["title"], p["summary"], p["education"], p["typical_shadowing"]])
        overlap = len(q & _tokens(blob))
        if overlap:
            scored.append((overlap, f"pathway:{p['id']}", p["title"], p["summary"][:400]))

    for g in GLOSSARY:
        blob = f"{g['term']} {g['plain_english']} {g['note']}"
        overlap = len(q & _tokens(blob))
        if overlap:
            scored.append(
                (
                    overlap + (3 if g["term"].lower() in query.lower() else 0),
                    f"glossary:{g['discipline']}",
                    g["term"],
                    f"{g['plain_english']} — {g['note']}",
                )
            )

    for c in CASES:
        blob = f"{c['title']} {c['stem']} {c['question']} {c['explanation']}"
        overlap = len(q & _tokens(blob))
        if overlap:
            scored.append((overlap, f"case:{c['id']}", c["title"], c["explanation"][:300]))

    for block in ORIENT.split("\n\n---\n\n"):
        overlap = len(q & _tokens(block))
        if overlap:
            title = block.splitlines()[0].lstrip("# ").strip() if block else "orientation"
            scored.append((overlap, "orientation-kit", title, block[:400]))

    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    seen = set()
    for _, sid, title, snip in scored:
        if sid in seen:
            continue
        seen.add(sid)
        out.append((sid, title, snip))
        if len(out) >= k:
            break
    return out


def explain_concept(query: str) -> str:
    hits = retrieve(query)
    if not hits:
        return (
            "I don't have enough allowlisted educational material to answer that. "
            "Try a glossary term, career pathway, or orientation topic. "
            f"\n\n**{DISCLAIMER}**"
        )
    cites = "\n".join(f"- `{sid}` — **{title}**: {snip}" for sid, title, snip in hits)
    top = hits[0]
    return (
        f"### Study explanation (grounded)\n\n"
        f"Based on allowlisted Cross Clinical educational corpus, **{top[1]}** is most relevant:\n\n"
        f"{top[2]}\n\n"
        f"### Citations\n{cites}\n\n"
        f"Verify with your textbooks and instructors.\n\n**{DISCLAIMER}**"
    )


def quiz_me(topic: str) -> str:
    hits = [c for c in CASES if topic.lower() in json.dumps(c).lower()]
    case = hits[0] if hits else CASES[0]
    choices = "\n".join(f"{i+1}. {ch}" for i, ch in enumerate(case["choices"]))
    return (
        f"### Quiz mode (synthetic case `{case['id']}`)\n\n"
        f"{case['stem']}\n\n**{case['question']}**\n\n{choices}\n\n"
        f"_Reveal: answer index {case['answer_index'] + 1} — {case['explanation']}_\n\n"
        f"Citation: `case:{case['id']}`\n\n**{DISCLAIMER}**"
    )


def compare_pathways(query: str) -> str:
    # naive: pick two highest scoring pathways
    q = _tokens(query)
    ranked = []
    for p in PATHWAYS:
        blob = " ".join([p["title"], p["discipline"], p["summary"]])
        ranked.append((len(q & _tokens(blob)), p))
    ranked.sort(key=lambda x: x[0], reverse=True)
    picks = [p for score, p in ranked if score > 0][:2]
    if len(picks) < 2:
        picks = PATHWAYS[:2]
    a, b = picks[0], picks[1]
    return (
        f"### Compare pathways\n\n"
        f"**{a['title']}** vs **{b['title']}**\n\n"
        f"- {a['title']}: {a['summary']}\n"
        f"- {b['title']}: {b['summary']}\n\n"
        f"Shadowing focus differs: _{a['typical_shadowing']}_ vs _{b['typical_shadowing']}_\n\n"
        f"Citations: `pathway:{a['id']}`, `pathway:{b['id']}`\n\n"
        f"**{DISCLAIMER}**"
    )


def respond(mode: str, message: str) -> str:
    blocked = guard_input(message)
    if blocked:
        return blocked
    if looks_like_clinical_request(message):
        return (
            "Mode blocked: this assistant has no `diagnose` or `treatment_plan` modes. "
            "Use explain_concept / quiz_me / compare_pathways for studying only.\n\n"
            f"**{DISCLAIMER}**"
        )
    if mode == "explain_concept":
        return explain_concept(message)
    if mode == "quiz_me":
        return quiz_me(message)
    if mode == "compare_pathways":
        return compare_pathways(message)
    return "Choose a valid mode."


with gr.Blocks(title="Edu Medical Assistant") as demo:
    gr.Markdown(
        f"# Edu Medical Assistant\n\n**{DISCLAIMER}**\n\n"
        "Modes: `explain_concept` · `quiz_me` · `compare_pathways` — "
        "**no diagnosis / treatment**.\n\n"
        "Also try: "
        "[Pathway Explorer](https://github.com/Cross-Clinical/health-pathway-explorer) · "
        "[Jargon](https://github.com/Cross-Clinical/clinical-jargon-explainer) · "
        "[Quizzes](https://github.com/Cross-Clinical/synthetic-case-quizzes) · "
        "[Lit Helper](https://github.com/Cross-Clinical/student-lit-helper)\n\n"
        "[Cross Clinical OSS](https://github.com/Cross-Clinical/suite-index) · "
        "[ProMedNet](https://crossclinical.com)"
    )
    mode = gr.Radio(MODES, value="explain_concept", label="Mode")
    msg = gr.Textbox(label="Ask a study question")
    out = gr.Markdown()
    gr.Button("Respond").click(respond, [mode, msg], out)
    msg.submit(respond, [mode, msg], out)

if __name__ == "__main__":
    demo.launch()
