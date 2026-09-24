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
