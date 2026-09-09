from datetime import date

from flask import Flask, jsonify, render_template, request

from model import get_today_view, predict_for_date, valid_date_range
from stocks import STOCKS

app = Flask(__name__)


@app.route("/")
def index():
    min_date, max_date = valid_date_range()
    return render_template(
        "index.html",
        min_date=min_date.isoformat(),
        max_date=max_date.isoformat(),
    )


@app.route("/predict")
def predict():
    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"error": "Mangler dato"}), 400

    try:
        requested_date = date.fromisoformat(date_str)
    except ValueError:
        return jsonify({"error": "Ugyldig dato"}), 400

    min_date, max_date = valid_date_range()
    if not (min_date <= requested_date <= max_date):
        return jsonify({"error": f"Dato skal være mellem {min_date} og {max_date}"}), 400

    results = [predict_for_date(ticker, requested_date) for ticker in STOCKS]
    return jsonify(results)


@app.route("/today")
def today_page():
    return render_template("today.html")


@app.route("/live")
def live():
    results = []
    for ticker in STOCKS:
        try:
            results.append(get_today_view(ticker))
        except Exception:
            results.append({
                "ticker": ticker,
                "name": STOCKS[ticker],
                "live_price": None,
                "predicted": None,
                "predicted_direction": None,
            })
    return jsonify(results)


if __name__ == "__main__":
    app.run(debug=True)
