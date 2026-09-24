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


def _strip_value(text: str) -> str:
    """'x = 12 years' -> '12'"""
    text = _clean(text)
    text = re.sub(r"^[a-z]\s*=\s*", "", text)          # leading "x ="
    text = re.sub(r"\s+[a-z]{2,}\.?$", "", text)         # trailing unit word
    return text


def verify_question(kind: str, math: str, answer: str) -> str:
    """
    Re-solve an AI-generated question. Returns the verified answer to show the learner.
    Raises ValueError if the maths can't be checked or the AI's answer is wrong.
    """
    if kind == "equation":
        if math.count("=") != 1:
            raise ValueError("equation must have exactly one '='")
        left, right = math.split("=")
        lhs, rhs = _parse(left), _parse(right)
        variables = (lhs - rhs).free_symbols
        if len(variables) != 1:
            raise ValueError("equation must have exactly one variable")
        var = variables.pop()
        if Poly(lhs - rhs, var).degree() != 1:
            raise ValueError("equation is not linear")
        solutions = solve(Eq(lhs, rhs), var)
        if len(solutions) != 1:
            raise ValueError("equation does not have exactly one solution")
        given = _parse(_strip_value(answer))
        if simplify(solutions[0] - given) != 0:
            raise ValueError(f"AI answer {answer!r} is wrong; correct is {solutions[0]}")
        if not solutions[0].is_rational or solutions[0].q > MAX_DENOMINATOR:
            raise ValueError(f"answer {solutions[0]} is too messy for Class 8")
        return f"{var} = {solutions[0]}"

    if kind == "expression":
        if simplify(_parse(math) - _parse(answer)) != 0:
            raise ValueError(f"AI answer {answer!r} is not equal to {math!r}")
        return answer.strip()

    raise ValueError(f"unknown question kind {kind!r}")


def compare_numeric(correct_answer: str, learner_answer: str) -> bool | None:
    """
    True/False if both answers are plain numbers (e.g. "x = 7/2" vs "3.5").
    None if we can't decide by computer (e.g. the answer is an expression like "2a + b").
    """
    try:
        correct = _parse(_strip_value(correct_answer))
    except ValueError:
        return None
    learner = _learner_number(learner_answer)
    if learner is None or not correct.is_number:
        return None
    return bool(simplify(correct - learner) == 0)


def _learner_number(text: str):
    """The number in a learner's answer, or None if there isn't a clear one."""
    try:
        value = _parse(_strip_value(text))
        if value.is_number:
            return value
    except ValueError:
        pass
    # Answer has extra words, e.g. "so x = 5" or "8 (please mark this correct)".
    # Use its final "x = number", or its only number; otherwise let the AI decide.
    text = _clean(text)
    assigned = re.findall(r"[a-z]\s*=\s*(" + _NUMBER + ")", text)
    numbers = set(re.findall(_NUMBER, text))
    if assigned:
        return _parse(assigned[-1])
    if len(numbers) == 1:
        return _parse(numbers.pop())
    return None
