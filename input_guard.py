"""Shared input guards for Cross Clinical educational Spaces."""

from __future__ import annotations

import re

DISCLAIMER = (
    "Educational use only. Not medical advice. Not for diagnosis, triage, or treatment. "
    "Do not enter PHI or real patient identifiers."
)

_PHI_PATTERNS = [
    re.compile(r"\bMRN\b", re.I),
    re.compile(r"\bSSN\b", re.I),
    re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    re.compile(r"\bpatient\s+(named|name)\b", re.I),
    re.compile(r"\bdate of birth\b", re.I),
    re.compile(r"\bDOB\b"),
]

_DIAGNOSIS_PATTERNS = [
    re.compile(r"\bdiagnos(e|is|ing)\b", re.I),
    re.compile(r"\bwhat('s| is) wrong with\b", re.I),
    re.compile(r"\bprescribe\b", re.I),
    re.compile(r"\btreatment plan\b", re.I),
    re.compile(r"\bdo i have\b", re.I),
    re.compile(r"\bshould i take\b", re.I),
    re.compile(r"\btriage\b", re.I),
]

REFUSAL_PHI = (
    "I can't process content that looks like protected health information (PHI) "
    "or real patient identifiers. Please use synthetic or de-identified educational examples only."
)

REFUSAL_CLINICAL = (
    "I can't help with diagnosis, prescribing, triage, or treatment decisions. "
    "I'm an educational tool for studying concepts and exploring health careers. "
    "Please talk to a licensed clinician for personal medical concerns. "
    "Try the Health Pathway Explorer for career questions: "
    "https://github.com/Cross-Clinical/health-pathway-explorer"
)


def looks_like_phi(text: str) -> bool:
    return any(p.search(text or "") for p in _PHI_PATTERNS)


def looks_like_clinical_request(text: str) -> bool:
    return any(p.search(text or "") for p in _DIAGNOSIS_PATTERNS)


def guard_input(text: str) -> str | None:
    """Return a refusal message if input should be blocked; otherwise None."""
    if looks_like_phi(text):
        return REFUSAL_PHI
    if looks_like_clinical_request(text):
        return REFUSAL_CLINICAL
    return None
