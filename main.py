import json
import os
import re
import time
import urllib.request
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from scripts.age import calculate_age
from scripts import calc

app = Flask(
    __name__,
    template_folder="website/templates",
    static_folder="website/static",
    static_url_path="/website/static",
)

REPO = "shuvamm939-glitch/Py-Calculator"
BASE_DIR = Path(__file__).parent

LANG_COLORS = {
    "Python": "#3572A5", "HTML": "#e34c26", "CSS": "#563d7c",
    "JavaScript": "#f1e05a", "Jinja": "#a52a22", "Shell": "#89e051",
}
_lang_cache = {"expires": 0, "data": None}


def repo_languages():
    if time.time() < _lang_cache["expires"]:
        return _lang_cache["data"]

    headers = {"User-Agent": "py-calc-site", "Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]

    data = None
    try:
        request_ = urllib.request.Request(
            f"https://api.github.com/repos/{REPO}/languages", headers=headers
        )
        with urllib.request.urlopen(request_, timeout=2) as response:
            raw = json.load(response)
        total = sum(raw.values())
        if total:
            data = [
                {
                    "name": name,
                    "pct": size / total * 100,
                    "label": f"{round(size / total * 100)}%" if size / total >= 0.01 else "<1%",
                    "color": LANG_COLORS.get(name, "#8b9096"),
                }
                for name, size in sorted(raw.items(), key=lambda item: -item[1])
            ]
    except Exception:
        data = None

    _lang_cache["data"] = data
    _lang_cache["expires"] = time.time() + (3600 if data else 300)
    return data


def read_requirements():
    try:
        lines = (BASE_DIR / "requirements.txt").read_text(encoding="utf-8").splitlines()
    except OSError:
        return []
    packages = []
    for line in lines:
        line = line.split("#")[0].strip()
        if not line or line.startswith("-"):
            continue
        name = re.split(r"[<>=!~\[;\s]", line, maxsplit=1)[0]
        pinned = re.search(r"==\s*([\w.]+)", line)
        packages.append({"name": name, "version": pinned.group(1) if pinned else ""})
    return packages


@app.context_processor
def footer_data():
    return {"repo": REPO, "languages": repo_languages(), "deps": read_requirements()}

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/age-calculator", methods=["GET", "POST"])
def age_calculator():
    result = None
    error = None

    if request.method == "POST":
        try:
            birth_date = request.form["birth_date"]
            present_date = request.form["present_date"]

            b_year, b_month, b_day = map(int, birth_date.split("-"))
            p_year, p_month, p_day = map(int, present_date.split("-"))

            years, months, days = calculate_age(
                b_year, b_month, b_day, p_year, p_month, p_day
            )
            result = {"years": years, "months": months, "days": days}
        except (ValueError, KeyError):
            error = "please select valid dates."

    return render_template("age_calculator.html", result=result, error=error)

@app.route("/calculator")
def calculator():
    return render_template(
        "calc.html",
        units=calc.unit_groups(),
        percent_modes=calc.PERCENT_MODES,
        base_modes=calc.BASE_MODES,
        )

@app.route("/changelog")
def changelog():
    return render_template("changelog.html")

@app.route("/api/calc", methods=["POST"])
def api_calc():
    return jsonify(calc.handle(request.get_json(silent=True)or{}))

if __name__ == "__main__":
    app.run(debug=True)