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
