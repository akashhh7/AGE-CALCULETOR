import ast
import math
import operator
import os
import re
import statistics

HISTORY_FILE = "calculator_history.txt"
history = []
memory = 0
last_answer = 0
angle_mode = "DEG"


class CalcError(Exception):
    """An error msg"""

def ask_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("  Please enter a valid number.")


def ask_int(prompt, minimum=None):
    while True:
        try:
            value = int(input(prompt))
        except ValueError:
            print("  Please enter a whole number.")
            continue
        if minimum is not None and value < minimum:
            print(f"  The number must be at least {minimum}.")
            continue
        return value


def format_number(x):
    if isinstance(x, float):
        if math.isnan(x) or math.isinf(x):
            return str(x)
        if x.is_integer() and abs(x) < 1e15:
            return str(int(x))
        return f"{x:.12g}"
    return str(x)


def number(value):
    try:
        x = float(value)
    except (TypeError, ValueError):
        raise CalcError("Please enter a valid number.")
    if not math.isfinite(x):
        raise CalcError("Please enter a valid number.")
    return x



def clean(x):
    return round(x, 12) + 0.0


def trig_functions(mode):
    deg = mode == "DEG"
    to_rad = math.radians if deg else (lambda x: x)
    from_rad = math.degrees if deg else (lambda x: x)

    def tan(x):
        if deg and x % 180 == 90:
            raise ValueError("tan is undefined here")
        return clean(math.tan(to_rad(x)))

    return {
        "sin": lambda x: clean(math.sin(to_rad(x))),
        "cos": lambda x: clean(math.cos(to_rad(x))),
        "tan": tan,
        "asin": lambda x: clean(from_rad(math.asin(x))),
        "acos": lambda x: clean(from_rad(math.acos(x))),
        "atan": lambda x: clean(from_rad(math.atan(x))),
    }


def factorial(x):
    if x < 0 or x != int(x) or x > 1000:
        raise ValueError("factorial needs a whole number from 0 to 1000")
    return math.factorial(int(x))


def cbrt(x):
    return math.copysign(abs(x) ** (1 / 3), x)


def safe_power(a, b):
    if abs(b) > 1000:
        raise OverflowError("exponent too large")
    return a ** b


FUNCTIONS = {
    "sqrt": math.sqrt, "cbrt": cbrt, "pow": safe_power,
    "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
    "log": math.log10, "log2": math.log2, "ln": math.log, "exp": math.exp,
    "abs": abs, "round": round, "floor": math.floor, "ceil": math.ceil,
    "fact": factorial, "gcd": math.gcd, "lcm": math.lcm,
    "ncr": lambda n, r: math.comb(int(n), int(r)),
    "npr": lambda n, r: math.perm(int(n), int(r)),
}

OPERATORS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod,
    ast.Pow: safe_power,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}


# exp eval

def evaluate(node, names, funcs):
    if isinstance(node, ast.Expression):
        return evaluate(node.body, names, funcs)

    if isinstance(node, ast.Constant):
        if type(node.value) in (int, float):
            return node.value
        raise CalcError("Invalid expression")

    if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
        left = evaluate(node.left, names, funcs)
        right = evaluate(node.right, names, funcs)
        return OPERATORS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in OPERATORS:
        return OPERATORS[type(node.op)](evaluate(node.operand, names, funcs))

    if isinstance(node, ast.Name):
        if node.id in names:
            return names[node.id]
        raise CalcError(f"Unknown name: {node.id}")

    if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id in funcs and not node.keywords):
        args = [evaluate(arg, names, funcs) for arg in node.args]
        return funcs[node.func.id](*args)

    raise CalcError("Invalid expression")


def prepare(expression):
    expression = expression.lower()
    expression = expression.replace("^", "**").replace("×", "*").replace("÷", "/")
    # implicit multiplication: 2pi, 3(4), (2)(3)
    expression = re.sub(r"(\d|\))\s*(?=[a-df-z(])", r"\1*", expression)
    expression = re.sub(r"(\))\s*(?=\d)", r"\1*", expression)
    return expression


def calculate(expression, mode="DEG", ans=0, mem=0):
    names = {"pi": math.pi, "e": math.e, "ans": ans, "m": mem}
    funcs = {**FUNCTIONS, **trig_functions(mode)}

    try:
        tree = ast.parse(prepare(expression), mode="eval")
        result = evaluate(tree, names, funcs)
    except ZeroDivisionError:
        raise CalcError("Cannot divide by zero")
    except OverflowError:
        raise CalcError("Number is too big")
    except (ValueError, TypeError):
        raise CalcError("Math error (check the numbers you used)")
    except SyntaxError:
        raise CalcError("Invalid expression")
    except RecursionError:
        raise CalcError("Expression is too long")

    if isinstance(result, complex):
        raise CalcError("Math error (result is not a real number)")
    return result


# percentage

PERCENT_MODES = [
    "X% of Y",
    "X is what % of Y",
    "Increase X by Y%",
    "Decrease X by Y%",
    "Percentage change from X to Y",
]


def percentage(kind, x, y):
    if kind == 1:
        return format_number(x * y / 100)
    if kind == 2:
        if y == 0:
            raise CalcError("Y cannot be zero.")
        return format_number(x / y * 100) + "%"
    if kind == 3:
        return format_number(x + x * y / 100)
    if kind == 4:
        return format_number(x - x * y / 100)
    if kind == 5:
        if x == 0:
            raise CalcError("X cannot be zero.")
        return format_number((y - x) / x * 100) + "%"
    raise CalcError("Invalid choice")


def percentage_menu():
    print()
    for i, label in enumerate(PERCENT_MODES, 1):
        print(f"{i}. {label}")
    choice = input("Enter your choice (1-5): ").strip()
    if choice not in ("1", "2", "3", "4", "5"):
        print("Invalid choice")
        return

    x = ask_float("Enter X: ")
    y = ask_float("Enter Y: ")
    try:
        print(f"Result = {percentage(int(choice), x, y)}")
    except CalcError as error:
        print(error)


# stats

def stats_summary(nums):
    if not nums:
        raise CalcError("Enter at least one number.")
    rows = [
        ("Sum", sum(nums)),
        ("Average", sum(nums) / len(nums)),
        ("Median", statistics.median(nums)),
        ("Maximum", max(nums)),
        ("Minimum", min(nums)),
        ("Range", max(nums) - min(nums)),
        ("Std dev (population)", statistics.pstdev(nums)),
    ]
    if len(nums) > 1:
        rows.append(("Std dev (sample)", statistics.stdev(nums)))
    return [(label, format_number(value)) for label, value in rows]


def stats_menu():
    n = ask_int("How many numbers? ", minimum=1)
    nums = [ask_float(f"Enter number {i + 1}: ") for i in range(n)]
    for label, value in stats_summary(nums):
        print(f"{label:<22} = {value}")


# unit converter

def factor(f):
    return (lambda x: x * f), (lambda x: x / f)


CONVERSIONS = [
    ("Length",      "Km", "Miles", *factor(0.621371)),
    ("Weight",      "Kg", "lbs", *factor(2.20462)),
    ("Temperature", "°C", "°F",
        lambda c: c * 9 / 5 + 32, lambda f: (f - 32) * 5 / 9),
    ("Length",      "Meters", "Feet", *factor(3.28084)),
    ("Length",      "Centimeters", "Inches", *factor(0.393701)),
    ("Length",      "Meters", "Yards", *factor(1.09361)),
    ("Weight",      "Kg", "Grams", *factor(1000)),
    ("Weight",      "Grams", "Ounces", *factor(0.035274)),
    ("Temperature", "°C", "Kelvin",
        lambda c: c + 273.15, lambda k: k - 273.15),
    ("Temperature", "°F", "Kelvin",
        lambda f: (f - 32) * 5 / 9 + 273.15,
        lambda k: (k - 273.15) * 9 / 5 + 32),
    ("Speed",       "Km/h", "mph", *factor(0.621371)),
    ("Speed",       "m/s", "Km/h", *factor(3.6)),
    ("Time",        "Seconds", "Minutes", *factor(1 / 60)),
    ("Time",        "Minutes", "Hours", *factor(1 / 60)),
    ("Time",        "Hours", "Days", *factor(1 / 24)),
    ("Area",        "m²", "ft²", *factor(10.7639)),
    ("Area",        "Acres", "Hectares", *factor(0.404686)),
    ("Volume",      "Liters", "Gallons", *factor(0.264172)),
    ("Volume",      "Liters", "Milliliters", *factor(1000)),
    ("Pressure",    "Bar", "PSI", *factor(14.5038)),
    ("Pressure",    "Pascal", "Bar", *factor(1e-5)),
    ("Energy",      "Joules", "Calories", *factor(1 / 4.184)),
    ("Energy",      "kWh", "Joules", *factor(3600000)),
    ("Power",       "Watts", "Kilowatts", *factor(1e-3)),
    ("Power",       "Watts", "Horsepower", *factor(1 / 745.7)),
    ("Data",        "Bytes", "KB", *factor(1 / 1024)),
    ("Data",        "MB", "GB", *factor(1 / 1024)),
    ("Data",        "GB", "TB", *factor(1 / 1024)),
    ("Angle",       "Degrees", "Radians", *factor(math.pi / 180)),
    ("Frequency",   "Hz", "kHz", *factor(1e-3)),
    ("Frequency",   "MHz", "GHz", *factor(1e-3)),
    ("Force",       "Newton", "Kilonewton", *factor(1e-3)),
    ("Force",       "Newton", "Pound-force", *factor(0.224809)),
    ("Torque",      "N·m", "lb·ft", *factor(0.737562)),
    ("Resistance",  "Ω", "kΩ", *factor(1e-3)),
    ("Voltage",     "V", "mV", *factor(1000)),
    ("Current",     "A", "mA", *factor(1000)),
]


def convert_units(index, direction, value):
    if not 0 <= index < len(CONVERSIONS):
        raise CalcError("Unknown conversion.")
    _, a, b, a_to_b, b_to_a = CONVERSIONS[index]
    if direction == 1:
        return f"{format_number(value)} {a} = {format_number(a_to_b(value))} {b}"
    if direction == 2:
        return f"{format_number(value)} {b} = {format_number(b_to_a(value))} {a}"
    raise CalcError("Invalid direction.")


def unit_groups():
    groups = {}
    for i, (category, a, b, _, _) in enumerate(CONVERSIONS):
        groups.setdefault(category, []).extend(
            [(f"{i}:1", f"{a} → {b}"), (f"{i}:2", f"{b} → {a}")]
        )
    return groups


def unit_converter():
    print()
    for n, (category, a, b, _, _) in enumerate(CONVERSIONS, 1):
        print(f"{n:>2}. {category} ({a} ↔ {b})")

    choice = ask_int(f"Enter your choice (1-{len(CONVERSIONS)}): ", minimum=1)
    if choice > len(CONVERSIONS):
        print(f"Invalid choice! Please enter a number from 1 to {len(CONVERSIONS)}.")
        return

    _, a, b, _, _ = CONVERSIONS[choice - 1]
    print(f"1. {a} → {b}")
    print(f"2. {b} → {a}")
    direction = input("Direction (1 or 2): ").strip()
    if direction not in ("1", "2"):
        print("Invalid direction.")
        return

    source = a if direction == "1" else b
    value = ask_float(f"Enter value in {source}: ")
    print(convert_units(choice - 1, int(direction), value))


# bases

BASE_MODES = [
    "Decimal → Binary / Octal / Hex",
    "Binary → Decimal",
    "Octal → Decimal",
    "Hex → Decimal",
]


def convert_base(kind, text):
    try:
        if kind == 1:
            n = int(text)
            sign = "-" if n < 0 else ""
            n = abs(n)
            return [("Binary", sign + bin(n)[2:]),
                    ("Octal", sign + oct(n)[2:]),
                    ("Hex", sign + hex(n)[2:].upper())]
        base = {2: 2, 3: 8, 4: 16}[kind]
        return [("Decimal", str(int(text.strip(), base)))]
    except (ValueError, KeyError):
        raise CalcError("That is not a valid number for this base.")


def base_menu():
    print()
    for i, label in enumerate(BASE_MODES, 1):
        print(f"{i}. {label}")
    choice = input("Enter your choice (1-4): ").strip()
    if choice not in ("1", "2", "3", "4"):
        print("Invalid choice")
        return

    if choice == "1":
        text = str(ask_int("Enter a whole number: "))
    else:
        text = input("Enter the number: ").strip()
    try:
        for label, value in convert_base(int(choice), text):
            print(f"{label:<7} = {value}")
    except CalcError as error:
        print(error)


# memory (m)

def memory_add(value):
    global memory
    memory += value
    print(f"Memory = {format_number(memory)}")


def memory_menu():
    global memory
    print(f"\nCurrent memory value: {format_number(memory)}")
    print("1. M+ (Add to memory)")
    print("2. M- (Subtract from memory)")
    print("3. MC (Memory clear)")
    print("4. MR (Memory recall)")
    choice = input("Choose (1-4): ").strip()

    if choice == "1":
        memory_add(ask_float("Enter value to add: "))
    elif choice == "2":
        memory_add(-ask_float("Enter value to subtract: "))
    elif choice == "3":
        memory = 0
        print("Memory cleared.")
    elif choice == "4":
        print(f"Memory value: {format_number(memory)}")
    else:
        print("Invalid choice! Please enter a number from 1 to 4.")


# history for terminal

def show_history():
    if not history:
        print("No history available.")
        return
    print("\n--- History ---")
    for i, item in enumerate(history, 1):
        print(f"{i}. {item}")
    print("---------------")


def save_history():
    with open(HISTORY_FILE, "w", encoding="utf-8") as file:
        for item in history:
            file.write(item + "\n")
    print(f"History saved to '{HISTORY_FILE}'.")


def load_history():
    global history
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            history = [line.strip() for line in file if line.strip()]
        print(f"History loaded: {len(history)} past calculations.")
    else:
        history = []
        print("No existing history found.")


def clear_history():
    global history
    history = []
    print("History cleared (not yet saved to file).")


# flask entry

def handle(data):
    # json sendig here
    op = data.get("op")
    try:
        if op == "expr":
            mode = "RAD" if data.get("mode") == "RAD" else "DEG"
            result = calculate(str(data.get("expression", "")), mode,
                               number(data.get("ans") or 0),
                               number(data.get("memory") or 0))
            try:
                value = float(result)
            except OverflowError:
                value = 0
            return {"ok": True, "text": format_number(result), "value": value}

        if op == "percent":
            text = percentage(int(data["kind"]), number(data["x"]), number(data["y"]))
            return {"ok": True, "lines": [["Result", text]]}

        if op == "stats":
            parts = re.split(r"[,\s]+", str(data.get("numbers", "")).strip())
            nums = [number(p) for p in parts if p]
            return {"ok": True, "lines": stats_summary(nums)}

        if op == "convert":
            index, direction = map(int, str(data["unit"]).split(":"))
            text = convert_units(index, direction, number(data["value"]))
            return {"ok": True, "lines": [["Result", text]]}

        if op == "base":
            lines = convert_base(int(data["kind"]), str(data["value"]))
            return {"ok": True, "lines": lines}

        return {"ok": False, "error": "Unknown request."}
    except CalcError as error:
        return {"ok": False, "error": str(error)}
    except (KeyError, ValueError, TypeError):
        return {"ok": False, "error": "Please check your input."}


# terminal only

def print_menu():
    print("\n============XD CALCULATOR============")
    print(" Type any expression, e.g.  5+3*2 - sqrt(16)   2pi   sin(30)")
    print(" Operators : + - * / ^ (power)  % (remainder)  // (whole division)")
    print(" Functions : sqrt cbrt sin cos tan asin acos atan sinh cosh tanh")
    print("             log ln log2 exp abs round floor ceil fact ncr npr gcd lcm")
    print(" Constants : pi e   ans (last answer)   m (memory)")
    print(f" Angle mode: {angle_mode}   (type 'mode' to change)")
    print(" Commands  :")
    print("   percent  -> percentage calculations")
    print("   stats    -> sum / average / median / std dev of many numbers")
    print(f"   convert  -> unit conversions ({len(CONVERSIONS)} types)")
    print("   base     -> binary / octal / hex converter")
    print("   memory   -> memory menu      m+ m- mc mr -> quick memory keys")
    print("   history  -> show history     save / load / clear")
    print("   help     -> show this menu   exit -> quit")
    print("=====================================")


def toggle_angle_mode():
    global angle_mode
    angle_mode = "RAD" if angle_mode == "DEG" else "DEG"
    print(f"Angle mode is now {angle_mode}.")


def calculator():
    global memory, last_answer
    load_history()
    print_menu()

    while True:
        try:
            user_input = input("\nEnter expression or command: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting calculator. Goodbye!")
            break

        if not user_input:
            continue

        if user_input == "exit":
            print("Exiting calculator. Goodbye!")
            break
        elif user_input == "help":
            print_menu()
        elif user_input == "percent":
            percentage_menu()
        elif user_input == "stats":
            stats_menu()
        elif user_input == "convert":
            unit_converter()
        elif user_input == "base":
            base_menu()
        elif user_input == "mode":
            toggle_angle_mode()
        elif user_input == "memory":
            memory_menu()
        elif user_input == "m+":
            memory_add(last_answer)
        elif user_input == "m-":
            memory_add(-last_answer)
        elif user_input == "mc":
            memory = 0
            print("Memory cleared.")
        elif user_input == "mr":
            print(f"Memory value: {format_number(memory)}")
        elif user_input == "history":
            show_history()
        elif user_input == "save":
            save_history()
        elif user_input == "load":
            load_history()
        elif user_input == "clear":
            clear_history()
        else:
            try:
                value = calculate(user_input, angle_mode, last_answer, memory)
            except CalcError as error:
                print(f"Error: {error}")
            else:
                last_answer = value
                result = format_number(value)
                print(f"Result: {result}")
                history.append(f"{user_input} = {result}")


if __name__ == "__main__":
    calculator()