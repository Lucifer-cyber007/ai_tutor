"""
All system prompts for the AI Tutor live here, separate from the code,
so they are easy to read and improve.
"""

TOPICS = {
    "expressions": "Variables and algebraic expressions",
    "equations": "Linear equations in one variable",
    "word_problems": "Word problems that lead to linear equations",
}

LEVELS = {
    "Beginner": {
        "teach": "Use very simple words and small whole numbers. Explain every step. Give hints generously.",
        "questions": "One or two steps only. Small positive whole numbers. Whole-number answers.",
    },
    "Intermediate": {
        "teach": "Normal Class 8 textbook level. Explain the key steps. Give a hint when the learner is stuck.",
        "questions": "Two or three steps. May use brackets, negative numbers or the variable on both sides. Whole-number answers.",
    },
    "Advanced": {
        "teach": "Use harder examples (brackets, variables on both sides, fractions). Give fewer hints and ask the learner to explain their method.",
        "questions": "Multi-step: brackets, variables on both sides, fractions. Answers are whole numbers or simple fractions with 2, 3 or 4 on the bottom (like 7/2).",
    },
}

QUESTION_TOPIC_GUIDE = {
    "expressions": 'Terms, like terms, adding/subtracting expressions, simplifying, and finding the value of an expression by substituting numbers. Mostly "expression" kind.',
    "equations": 'Solving linear equations in one variable. Use the "equation" kind.',
    "word_problems": 'Short real-life word problems (ages, money, perimeter, consecutive numbers) that lead to ONE linear equation and ask for ONE unknown number. Use the "equation" kind.',
}
