from datetime import datetime
from functools import wraps
from typing import Any, Sequence

from dotenv import dotenv_values
from flask import request, jsonify, send_file
from sqlalchemy import Row

from chart.main import plot
from init import db, app
from models.signal import Signal

config = dotenv_values(".env")

# Initialize the database
@app.before_request
def create_tables():
    db.create_all()

def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("API-KEY")
        configured_key = config.get("API_KEY")

        if api_key != configured_key:
            return jsonify({"error": "Authentication is required"}), 403

        return f(*args, **kwargs)
    return decorated_function

@app.route("/ping", methods=["POST"])
@api_key_required
def ping():
    data = request.get_json()

    timestamp_str = data.get('timestamp')
    if timestamp_str:
        try:
            timestamp = datetime.fromtimestamp(int(timestamp_str))
            new_timestamp = Signal(timestamp=timestamp)
            db.session.add(new_timestamp)
            db.session.commit()
            return jsonify({"message": "Timestamp received"}), 200
        except ValueError:
            return jsonify({"error": "Invalid timestamp format"}), 400
    else:
        return jsonify({"error": "No timestamp provided"}), 400


@app.route("/stat")
def stat():
    select_from = request.args.get('from')
    select_to = request.args.get('to')

    table = db.Table('signal')
    res: Sequence[Row[Signal]] = db.engine.connect().execute(table.select().filter(
        # Signal.timestamp >= select_from
        Signal.timestamp.between(select_from, select_to)
    )).fetchall()
    signals = [{"timestamp": row[1], "at": row[2]} for row in res]

    if len(signals) < 1:
        return "<div>NO DATA. PLease use: <pre>/stat?from=2024-07-10&to=2024-07-30</pre></div>", 404

    img = plot(signals)
    return "<div><img src='data:image/png;base64,{0}'></div>".format(img), 200



if __name__ == '__main__':
    app.run(debug=True)
