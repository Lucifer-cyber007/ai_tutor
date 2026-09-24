"""
The only file that talks to the Groq API.
Any Groq problem is turned into a TutorAIError with a message that is safe
to show to a student. The real error is written to the server log.
"""
import json
import logging
import os
import re
from typing import Callable, TypeVar

from groq import AuthenticationError, BadRequestError, Groq, GroqError, RateLimitError

log = logging.getLogger("ai_tutor")

DEFAULT_MODEL = "openai/gpt-oss-120b"
T = TypeVar("T")


class TutorAIError(Exception):
    """The AI could not give an answer. The message is safe to show to learners."""


class _BadJSON(Exception):
    """Groq's JSON mode rejected the model output (we retry once)."""


_client = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        api_key = os.getenv("GROQ_API_KEY", "").strip()
        if not api_key:
            log.error("GROQ_API_KEY is not set")
            raise TutorAIError("The tutor is not set up yet. Please try again later.")
        _client = Groq(api_key=api_key, timeout=30.0, max_retries=1)
    return _client


def _call(
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    json_mode: bool = False,
    reasoning: str = "low",
) -> str:
    """One request to Groq. Returns the reply text."""
    model = os.getenv("GROQ_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    options = {"response_format": {"type": "json_object"}} if json_mode else {}
    if "gpt-oss" in model:
        # Reasoning models think before answering; "low"/"medium" keeps it fast. Other models reject this option.
        options["reasoning_effort"] = reasoning
    try:
        response = _get_client().chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **options,
        )
    except RateLimitError:
        log.warning("Groq rate limit reached")
        raise TutorAIError("The tutor is very busy right now. Please wait a minute and try again.")
    except AuthenticationError:
        log.error("Groq rejected the API key - check GROQ_API_KEY")
        raise TutorAIError("The tutor is not set up correctly. Please try again later.")
    except BadRequestError as exc:
        if json_mode and "json_validate_failed" in str(exc):
            raise _BadJSON(str(exc)) from exc
        log.error("Groq bad request: %s", exc)
        raise TutorAIError("The tutor could not answer right now. Please try again in a moment.")
    except GroqError as exc:
        log.error("Groq request failed: %s: %s", type(exc).__name__, exc)
        raise TutorAIError("The tutor could not answer right now. Please try again in a moment.")

    text = (response.choices[0].message.content or "").strip()
    if not text:
        log.error("Groq returned an empty reply")
        raise TutorAIError("The tutor gave an empty answer. Please try asking again.")
    return text
