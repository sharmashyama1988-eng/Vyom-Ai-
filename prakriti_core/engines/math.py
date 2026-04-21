"""
MATH ENGINE - Powered by SymPy
Handles Arithmetic, Algebra, Calculus, and Logic accurately.
"""
import sympy
from sympy import symbols, solve, sympify, diff, integrate

def solve_math(query):
    """
    User ki query se math extract karke solve karta hai.
    """
    try:
        # 1. Clean the Query (Keywords hatao)
        clean_query = query.lower().replace("calculate", "").replace("solve", "").replace("math", "").strip()
        
        # Replace common words with symbols
        clean_query = clean_query.replace("x", "*").replace("^", "**").replace("plus", "+").replace("minus", "-")
        
        # --- A. ALGEBRA SOLVER (e.g., "2x + 5 = 15") ---
        if "=" in clean_query:
            # Equation ke 2 hisse karo (LHS = RHS)
            parts = clean_query.split("=")
            lhs_str = parts[0].strip()
            rhs_str = parts[1].strip()
            
            # SymPy symbols define karo (x, y, z..)
            x, y, z = symbols('x y z')
            
            # Equation banao
            lhs = sympify(lhs_str)
            rhs = sympify(rhs_str)
            eq = sympy.Eq(lhs, rhs)
            
            # Solve karo
            result = solve(eq)
            return f"**Algebra Solution:**\nx = {result}"

        # --- B. CALCULUS (Derivative/Integration) ---
        if "derivative" in query or "differentiate" in query:
            # Example: "derivative of x**2"
            clean_query = clean_query.replace("derivative of", "").replace("differentiate", "").strip()
            x = symbols('x')
            expr = sympify(clean_query)
            result = diff(expr, x)
            return f"**Derivative:**\n{result}"
            
        # --- C. BASIC ARITHMETIC (BODMAS) ---
        # Direct calculation (e.g., "25 * 40 / 2")
        # sympify string ko math mein badal deta hai
        expression = sympify(clean_query)
        
        # Result nikalo (evalf se float value milti hai agar zarurat ho)
        exact_result = expression
        decimal_result = expression.evalf()
        
        if exact_result == decimal_result:
            return f"**Calculated Result:**\n# {exact_result}"
        else:
            return f"**Result:**\n{exact_result}\n*(Decimal: {decimal_result:.2f})*"

    except Exception as e:
        return f"❌ Math Error: I couldn't understand the equation. ({str(e)})"
    