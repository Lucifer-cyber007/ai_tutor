"""
Checks the maths with a computer algebra library (sympy), so we never rely only on the AI.

- verify_question(): re-solves an AI-generated question; wrong ones are thrown away.
- compare_numeric(): decides if a learner's numeric answer (e.g. "x = 5") is right.

The text we parse comes from the AI or the learner, so it is strictly filtered first:
only digits, single-letter variables, + - * / ^ ( ) . and small powers are allowed.
"""
import re

from sympy import Eq, Poly, Symbol, simplify, solve
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication,
    parse_expr,
    standard_transformations,
)

MAX_MATH_CHARS = 120
MAX_DENOMINATOR = 4   # answers like 7/2 or 5/4 are fine; 26/11 is too messy for Class 8
_ALLOWED_CHARS = re.compile(r"[0-9a-z+\-*/().^\s]+")
_TRANSFORMS = standard_transformations + (implicit_multiplication, convert_xor)
_NUMBER = r"-?\d+(?:\.\d+)?(?:\s*/\s*\d+)?"   # 5, -3, 2.5, 7/2


def _clean(text: str) -> str:
    text = text.strip().lower()
    for fancy, plain in (("×", "*"), ("÷", "/"), ("−", "-"), ("–", "-"), ("**", "^")):
        text = text.replace(fancy, plain)
    return text


def _parse(text: str):
    """Parse one expression (no '=') safely. Raises ValueError if it is not simple algebra."""
    text = _clean(text)
    if not text or len(text) > MAX_MATH_CHARS or not _ALLOWED_CHARS.fullmatch(text):
        raise ValueError(f"unsupported math text: {text!r}")
    # Powers must be one small digit (x^2 is fine, 9^9^9 is not) - protects the server.
    if text.count("^") > 3 or len(re.findall(r"\^\s*\d(?![\d.(^])", text)) != text.count("^"):
        raise ValueError(f"unsupported power in: {text!r}")
    # "3ab" means 3*a*b: split letters so every variable is one letter.
    text = re.sub(r"(?<=[a-z])(?=[a-z])", "*", text)
    symbols = {letter: Symbol(letter) for letter in set(re.findall(r"[a-z]", text))}
    try:
        return parse_expr(text, local_dict=symbols, transformations=_TRANSFORMS)
    except Exception as exc:  # sympy raises many error types for bad input
        raise ValueError(f"could not parse {text!r}: {exc}") from exc
