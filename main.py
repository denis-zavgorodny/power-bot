from datetime import datetime, timedelta
import tzlocal
import pytz
from functools import wraps
from typing import Sequence

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

def get_parameter_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.args
        api_key = data.get("key")
        configured_key = config.get("HTTP_KEY")

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
@get_parameter_key_required
def stat():
    select_from = request.args.get('from')
    select_to = request.args.get('to')

    table = db.Table('signal')
    res: Sequence[Row[Signal]] = db.engine.connect().execute(table.select().filter(
        # Signal.timestamp >= select_from
        Signal.timestamp.between(select_from, select_to)
    )).fetchall()

    difference_in_hours = get_time_difference_in_hours()
    difference_in_hours_db = get_db_time_difference_in_hours()

    signals = [{"timestamp": row[1] - timedelta(hours=difference_in_hours_db), "at": row[2] - timedelta(hours=difference_in_hours_db)} for row in res]

    if len(signals) < 1:
        return "<div>NO DATA. PLease use: <pre>/stat?from=2024-07-10&to=2024-07-30</pre></div>", 404

    if datetime.now() < datetime.fromisoformat(select_to):
        future_date = datetime.now() - timedelta(hours=difference_in_hours)
    else:
        future_date = datetime.fromisoformat(select_to) - timedelta(hours=difference_in_hours)

    img = plot(signals, datetime.fromisoformat(select_from), future_date)
    return """
        <div>
            <img src='data:image/png;base64,{0}'>
        </div>
    """.format(img), 200

@app.route("/status")
def status():
    current_time = datetime.utcnow() - timedelta(minutes=2)

    table = db.Table('signal')
    res: Sequence[Row[Signal]] = db.engine.connect().execute(table.select().filter(
        Signal.timestamp > current_time
    )).fetchall()

    if len(res) < 1:
        return "<div>NO POWER</div>", 404

    return "<div>POWER</div>", 200


def get_time_difference_in_hours():
    ###
    ### For some reason it does not calculate the diff between Kyiv
    ### and UTM timezones. @todo: It needs to be figured out
    ###

    # local_timezone = tzlocal.get_localzone()
    # home_timezone = pytz.timezone('Europe/Kyiv')
    # time1 = datetime.now(local_timezone)
    # time2 = datetime.now(home_timezone)
    # time_difference = time2 - time1
    # difference_in_hours = time_difference.total_seconds() / 3600

    # return round(difference_in_hours)


    return int(config.get("TIME_ZONE_DIFF"))


def get_db_time_difference_in_hours():
    return int(config.get("DB_TIME_ZONE_DIFF"))

if __name__ == '__main__':
    app.run(debug=True)
