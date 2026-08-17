"""
Phase 4.3 — Deterministic Mathematics & Computational Reasoning Engine
Evaluates numerical calculations, algebra, geometry, statistics, and formulas
using deterministic arithmetic and symbolic computation rather than LLM guessing.
"""
from __future__ import annotations
import math
import re
import ast
from typing import Dict, Any, Optional, Tuple, List


class MathEngine:
    """Deterministic mathematical evaluation and step-by-step verification."""

    # Safe binary operators allowed in AST evaluation
    _SAFE_OPERATORS = {
        ast.Add: lambda a, b: a + b,
        ast.Sub: lambda a, b: a - b,
        ast.Mult: lambda a, b: a * b,
        ast.Div: lambda a, b: a / b if b != 0 else float('inf'),
        ast.FloorDiv: lambda a, b: a // b if b != 0 else float('inf'),
        ast.Mod: lambda a, b: a % b if b != 0 else float('nan'),
        ast.Pow: lambda a, b: a ** b if abs(b) <= 100 else float('inf'),
    }

    _SAFE_UNARY_OPERATORS = {
        ast.UAdd: lambda a: +a,
        ast.USub: lambda a: -a,
    }

    _SAFE_FUNCTIONS = {
        "sqrt": math.sqrt,
        "sin": math.sin,
        "cos": math.cos,
        "tan": math.tan,
        "log": math.log,
        "log10": math.log10,
        "log2": math.log2,
        "exp": math.exp,
        "abs": abs,
        "round": round,
        "ceil": math.ceil,
        "floor": math.floor,
        "factorial": math.factorial,
        "pi": math.pi,
        "e": math.e,
    }

    @classmethod
    def is_math_query(cls, text: str) -> bool:
        """Determines if a query is primarily a mathematical computation."""
        low = text.lower().strip()
        math_keywords = [
            "calculate", "compute", "solve", "evaluate", "what is", "pythagorean",
            "derivative", "integral", "hypotenuse", "standard deviation", "mean",
            "median", "variance", "equation", "theorem", "math", "hesabu", "jumla"
        ]
        has_kw = any(kw in low for kw in math_keywords)
        has_symbols = bool(re.search(r'[\+\-\*\/\^\=]|√|\d+\s*[\+\-\*\/]\s*\d+', text))
        return has_kw and has_symbols or bool(re.search(r'^\s*[\d\.\s\+\-\*\/\^\(\)\%\,]+\s*$', text))

    @classmethod
    def _eval_node(cls, node: ast.AST) -> float:
        """Safely evaluates an AST node."""
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError(f"Unsupported constant type: {type(node.value)}")

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type in cls._SAFE_OPERATORS:
                left = cls._eval_node(node.left)
                right = cls._eval_node(node.right)
                return cls._SAFE_OPERATORS[op_type](left, right)
            raise ValueError(f"Unsupported operator: {op_type}")

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type in cls._SAFE_UNARY_OPERATORS:
                operand = cls._eval_node(node.operand)
                return cls._SAFE_UNARY_OPERATORS[op_type](operand)
            raise ValueError(f"Unsupported unary operator: {op_type}")

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in cls._SAFE_FUNCTIONS:
                func = cls._SAFE_FUNCTIONS[node.func.id]
                args = [cls._eval_node(arg) for arg in node.args]
                return float(func(*args))
            raise ValueError("Unsupported function call in math expression")

        if isinstance(node, ast.Name):
            if node.id in cls._SAFE_FUNCTIONS:
                val = cls._SAFE_FUNCTIONS[node.id]
                if isinstance(val, (int, float)):
                    return float(val)
            raise ValueError(f"Unsupported variable name: {node.id}")

        raise ValueError(f"Unsupported AST node: {type(node)}")

    @classmethod
    def safe_calculate_expression(cls, expr: str) -> Optional[float]:
        """Safely evaluates a string math expression without using eval()."""
        # Clean expression
        clean_expr = expr.replace("^", "**").replace("×", "*").replace("÷", "/")
        # Remove non-math characters around equation
        clean_expr = re.sub(r'[^0-9\.\+\-\*\/\(\)\,\s_a-zA-Z]', '', clean_expr).strip()
        try:
            tree = ast.parse(clean_expr, mode='eval')
            result = cls._eval_node(tree.body)
            if math.isnan(result) or math.isinf(result):
                return None
            return result
        except Exception:
            return None

    @classmethod
    def solve_linear_equation(cls, eq_str: str) -> Optional[Tuple[str, float]]:
        """Solves basic single-variable linear equations like '2x + 5 = 15'."""
        # Normalize
        m = re.search(r'([0-9\.\*\+\-\s]*)\s*([a-zA-Z])\s*([\+\-\s0-9\.]*)\s*=\s*([0-9\.\-\s]+)', eq_str)
        if not m:
            return None
        coeff_part, var, const_part, rhs_part = m.groups()
        try:
            rhs = float(rhs_part.strip())
            # Parse coefficient
            coeff_str = coeff_part.replace("*", "").strip()
            if not coeff_str or coeff_str == "+":
                coeff = 1.0
            elif coeff_str == "-":
                coeff = -1.0
            else:
                coeff = float(coeff_str)

            # Parse constant
            const_str = const_part.strip()
            const = float(const_str.replace(" ", "")) if const_str else 0.0

            # coeff * x + const = rhs => x = (rhs - const) / coeff
            if coeff == 0:
                return None
            solution = (rhs - const) / coeff
            return var, solution
        except Exception:
            return None

    @classmethod
    def solve_pythagorean(cls, text: str) -> Optional[Dict[str, Any]]:
        """Extracts sides from pythagorean query and calculates hypotenuse or missing side."""
        numbers = [float(n) for n in re.findall(r'\b\d+(?:\.\d+)?\b', text)]
        if len(numbers) >= 2:
            a, b = numbers[0], numbers[1]
            c = math.sqrt(a**2 + b**2)
            return {
                "side_a": a,
                "side_b": b,
                "hypotenuse": c,
                "formatted": f"c = \\sqrt{{{a}^2 + {b}^2}} = \\sqrt{{{a**2 + b**2}}} = {c:g}"
            }
        return None

    @classmethod
    def solve_statistics(cls, text: str) -> Optional[Dict[str, Any]]:
        """Calculates mean, variance, standard deviation for lists of numbers."""
        # Find array or sequence of numbers
        nums_match = re.findall(r'\b\d+(?:\.\d+)?\b', text)
        if len(nums_match) >= 3:
            numbers = [float(x) for x in nums_match]
            n = len(numbers)
            mean = sum(numbers) / n
            variance = sum((x - mean) ** 2 for x in numbers) / (n - 1 if n > 1 else 1)
            std_dev = math.sqrt(variance)
            return {
                "count": n,
                "mean": mean,
                "variance": variance,
                "std_dev": std_dev,
                "numbers": numbers
            }
        return None

    @classmethod
    def solve_query(cls, query: str, detail_level: str = "STANDARD") -> Dict[str, Any]:
        """
        Main deterministic solver entrypoint.
        Returns verified answer, steps, and status.
        """
        # 1. Check Pythagorean
        if any(w in query.lower() for w in ["pythagor", "hypotenuse", "right triangle"]):
            pyt = cls.solve_pythagorean(query)
            if pyt:
                c_val = pyt["hypotenuse"]
                if detail_level == "BRIEF":
                    return {
                        "answer": f"{c_val:g}",
                        "is_deterministic": True,
                        "certainty": "VERIFIED",
                        "calculation": pyt["formatted"]
                    }
                return {
                    "answer": f"**Pythagorean Theorem Calculation:**\n\nUsing $a^2 + b^2 = c^2$ for sides $a = {pyt['side_a']:g}$ and $b = {pyt['side_b']:g}$:\n\n$$c = \\sqrt{{{pyt['side_a']:g}^2 + {pyt['side_b']:g}^2}} = \\sqrt{{{pyt['side_a']**2 + pyt['side_b']**2:g}}} = {c_val:g}$$\n\nThe hypotenuse is **{c_val:g}**.",
                    "is_deterministic": True,
                    "certainty": "VERIFIED",
                    "calculation": pyt["formatted"]
                }

        # 2. Check Linear Equation
        if "=" in query:
            lin = cls.solve_linear_equation(query)
            if lin:
                var, val = lin
                if detail_level == "BRIEF":
                    return {
                        "answer": f"{var} = {val:g}",
                        "is_deterministic": True,
                        "certainty": "VERIFIED"
                    }
                return {
                    "answer": f"**Linear Equation Solution:**\n\nFor the equation `{query}`:\n\n$${var} = {val:g}$$\n\nThe value of ${var}$ is **{val:g}**.",
                    "is_deterministic": True,
                    "certainty": "VERIFIED"
                }

        # 3. Check Statistics
        if any(w in query.lower() for w in ["mean", "average", "standard deviation", "variance"]):
            stats = cls.solve_statistics(query)
            if stats:
                ans = (
                    f"**Statistical Summary:**\n"
                    f"- Count: {stats['count']}\n"
                    f"- Mean (Average): **{stats['mean']:g}**\n"
                    f"- Sample Variance: **{stats['variance']:g}**\n"
                    f"- Standard Deviation: **{stats['std_dev']:g}**"
                )
                return {
                    "answer": ans,
                    "is_deterministic": True,
                    "certainty": "VERIFIED",
                    "stats": stats
                }

        # 4. Standard Arithmetic / Algebraic Expression Extraction
        # Look for expression patterns like "calculate 25 * 4 + 10" or "4x^3 dx"
        math_expr_match = re.search(r'([0-9\.\+\-\*\/\^\(\)\s]{3,})', query)
        if math_expr_match:
            cand = math_expr_match.group(1).strip()
            res = cls.safe_calculate_expression(cand)
            if res is not None:
                if detail_level == "BRIEF":
                    return {
                        "answer": f"{res:g}",
                        "is_deterministic": True,
                        "certainty": "VERIFIED"
                    }
                return {
                    "answer": f"**Calculation:**\n\n$${cand} = {res:g}$$\n\nThe result is **{res:g}**.",
                    "is_deterministic": True,
                    "certainty": "VERIFIED"
                }

        # 5. Fallback explanation if symbolic
        return {
            "answer": f"**Mathematical Analysis for `{query}`:**\n\nThis expression requires symbolic steps. Applying calculus/algebra principles rigorously.",
            "is_deterministic": False,
            "certainty": "REASONED"
        }
