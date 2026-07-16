"""
Heuristic prompt-injection detection. Catches the obvious patterns;
does NOT catch sophisticated or novel attacks. Use as a defense layer,
not a defense.

Pattern types:
- Override directives ("ignore previous instructions", "disregard above")
- Role-override attempts ("you are now", "pretend you are")
- System-prompt impersonation (output that looks like a system message)
- Output exfiltration attempts ("repeat your system prompt", "dump")
- Encoded payloads (base64/hex inside otherwise plain text)
- Delimiter confusion (closing tags / quotes for the wrapping prompt)
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, field
from enum import Enum


class InjectionPattern(str, Enum):
    OVERRIDE_DIRECTIVE = "override_directive"
    ROLE_OVERRIDE = "role_override"
    SYSTEM_IMPERSONATION = "system_impersonation"
    EXFILTRATION = "exfiltration"
    ENCODED_PAYLOAD = "encoded_payload"
    DELIMITER_CONFUSION = "delimiter_confusion"


@dataclass
class InjectionSignal:
    pattern: InjectionPattern
    excerpt: str
    confidence: float  # 0.0 to 1.0; heuristic, not calibrated


_OVERRIDE_PHRASES = [
    r"ignore\s+(?:the\s+)?(?:previous|above|prior|earlier)\s+(?:instructions?|prompts?|messages?|rules?)",
    r"disregard\s+(?:the\s+)?(?:previous|above|prior|earlier)",
    r"forget\s+(?:everything|the\s+rules|all\s+previous)",
    r"override\s+(?:your|all|the)\s+(?:instructions?|rules?|guidelines?)",
    r"new\s+instructions?\s*[:.]",
]

_ROLE_OVERRIDE_PHRASES = [
    r"you\s+are\s+now\s+(?:a\s+)?(?:dan|jailbroken|unrestricted|free|evil)",
    r"pretend\s+(?:you\s+are|to\s+be)\s+",
    r"act\s+as\s+(?:if\s+)?(?:dan|an?\s+ai\s+without|jailbroken)",
    r"role[-\s]?play\s+as\s+",
    r"from\s+now\s+on\s+you\s+(?:will|are|must)",
]

_SYSTEM_IMPERSONATION = [
    r"<\|im_start\|>\s*system",
    r"<system>",
    r"\bSystem:\s+(?:you\s+are|new\s+instruction)",
    r"\[\s*system\s*\]",
    r"###\s*system",
]

_EXFILTRATION_PHRASES = [
    r"repeat\s+(?:your|the)\s+system\s+prompt",
    r"(?:show|reveal|print|output|dump)\s+(?:your|the)\s+(?:system\s+)?(?:prompt|instructions?)",
    r"what\s+(?:were|are)\s+your\s+(?:original\s+)?instructions?",
    r"echo\s+(?:back\s+)?everything\s+above",
    r"reproduce\s+(?:your|the)\s+(?:initial\s+)?prompt",
]

_DELIMITER_CONFUSION = [
    r"\"\"\"\s*\n",  # Closing triple-quote on its own line, mid-message
    r"```\s*\n.*\n\s*system",
    r"</\s*(?:user|assistant|system|context|input)\s*>",
    r"\[/(?:user|assistant|system|inst)\]",
]

_OVERRIDE_RE = [re.compile(p, re.IGNORECASE) for p in _OVERRIDE_PHRASES]
_ROLE_RE = [re.compile(p, re.IGNORECASE) for p in _ROLE_OVERRIDE_PHRASES]
_SYSTEM_RE = [re.compile(p, re.IGNORECASE) for p in _SYSTEM_IMPERSONATION]
_EXFIL_RE = [re.compile(p, re.IGNORECASE) for p in _EXFILTRATION_PHRASES]
_DELIM_RE = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _DELIMITER_CONFUSION]


def _excerpt(text: str, match: re.Match[str], pad: int = 30) -> str:
    start = max(match.start() - pad, 0)
    end = min(match.end() + pad, len(text))
    snippet = text[start:end].replace("\n", " ")
    return snippet[:120]


def _check_encoded_payload(text: str) -> InjectionSignal | None:
    # Heuristic: long base64-ish run (40+ chars) embedded in otherwise prose.
    candidates = re.findall(r"[A-Za-z0-9+/=]{40,}", text)
    for candidate in candidates:
        # Try to decode; if it parses to plausible UTF-8, treat as encoded payload.
        try:
            decoded = base64.b64decode(candidate, validate=True).decode("utf-8")
        except Exception:
            continue
        if any(
            keyword in decoded.lower()
            for keyword in ("ignore", "override", "system", "instruction", "jailbreak")
        ):
            return InjectionSignal(
                pattern=InjectionPattern.ENCODED_PAYLOAD,
                excerpt=candidate[:60] + "...",
                confidence=0.7,
            )
    return None


def detect_injection(text: str) -> list[InjectionSignal]:
    """
    Run all heuristic checks. Returns a list of signals (empty if clean).
    Confidence values are heuristic, not calibrated; treat as "what to
    inspect," not "what to block."
    """
    signals: list[InjectionSignal] = []

    for regex in _OVERRIDE_RE:
        match = regex.search(text)
        if match:
            signals.append(
                InjectionSignal(
                    pattern=InjectionPattern.OVERRIDE_DIRECTIVE,
                    excerpt=_excerpt(text, match),
                    confidence=0.85,
                )
            )

    for regex in _ROLE_RE:
        match = regex.search(text)
        if match:
            signals.append(
                InjectionSignal(
                    pattern=InjectionPattern.ROLE_OVERRIDE,
                    excerpt=_excerpt(text, match),
                    confidence=0.75,
                )
            )

    for regex in _SYSTEM_RE:
        match = regex.search(text)
        if match:
            signals.append(
                InjectionSignal(
                    pattern=InjectionPattern.SYSTEM_IMPERSONATION,
                    excerpt=_excerpt(text, match),
                    confidence=0.8,
                )
            )

    for regex in _EXFIL_RE:
        match = regex.search(text)
        if match:
            signals.append(
                InjectionSignal(
                    pattern=InjectionPattern.EXFILTRATION,
                    excerpt=_excerpt(text, match),
                    confidence=0.85,
                )
            )

    for regex in _DELIM_RE:
        match = regex.search(text)
        if match:
            signals.append(
                InjectionSignal(
                    pattern=InjectionPattern.DELIMITER_CONFUSION,
                    excerpt=_excerpt(text, match),
                    confidence=0.6,
                )
            )

    encoded = _check_encoded_payload(text)
    if encoded:
        signals.append(encoded)

    return signals
