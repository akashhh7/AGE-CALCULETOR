from flask import Flask, jsonify, render_template, request
from scripts.age import calculate_age
from scripts import calc

app = Flask(
    __name__,
    template_folder="website/templates",
    static_folder="website/static",
    static_url_path="/website/static",
)

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