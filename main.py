from datetime import datetime, timedelta

from functools import wraps
from typing import Sequence

import pytz
from dotenv import dotenv_values
from flask import request, jsonify, send_file
from sqlalchemy import Row

from chart.main import plot
from init import db, app
from logger import get_logger
from models.signal import Signal
from yasno.api import YasnoAPI, OFF
from yasno.power_state import Power

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
    logger = get_logger()
    try:
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
    except Exception as e:
        logger.error(f"HTTP /ping endpoint error: {e}")

@app.route("/stat")
@get_parameter_key_required
def stat():
    logger = get_logger()
    try:
        select_from = request.args.get('from')
        select_to = request.args.get('to')

        difference_in_hours = get_time_difference_in_hours()
        difference_in_hours_db = get_db_time_difference_in_hours()

        select_from_date = datetime.fromisoformat(select_from) + timedelta(hours=difference_in_hours_db)
        select_to_date = datetime.fromisoformat(select_to) + timedelta(hours=difference_in_hours_db)

        table = db.Table('signal')
        res: Sequence[Row[Signal]] = db.engine.connect().execute(table.select().filter(
            Signal.timestamp.between(
                select_from_date,
                select_to_date
            )
        )).fetchall()

        print(select_from_date, select_to_date)



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
    except Exception as e:
        logger.error(f"HTTP /stat endpoint error: {e}")

        return "Error", 502

@app.route("/status")
def status():
    logger = get_logger()
    try:
        yasno = YasnoAPI(autoload=False)
        power_status = Power(yasno)

        current_time = datetime.now() - timedelta(minutes=5)

        table = db.Table('signal')
        res: Sequence[Row[Signal]] = db.engine.connect().execute(table.select().filter(
            Signal.timestamp > current_time
        )).fetchall()

        return jsonify(power_status.predict(len(res) > 0)), 200

    except Exception as e:
        logger.error(f"HTTP /status endpoint error: {e}")
        raise e



@app.route("/calendar")
def calendar():
    yasno = YasnoAPI(autoload=False)
    currentState = yasno.get_current_event(at = datetime.now())

    if currentState is None:
        next = yasno.next_off()

        return {
            "event_state": next.get("SUMMARY"),
            "event_start": next.decoded("DTSTART").strftime("%Y-%m-%d %H:%M:%S"),
            "event_end": next.decoded("DTEND").strftime("%Y-%m-%d %H:%M:%S"),
        }, 200

    # if currentState.get("SUMMARY") == "off":
    #     next = yasno.next_off()


    event_state = currentState.get("SUMMARY")
    event_start = currentState.decoded("DTSTART")
    event_end = currentState.decoded("DTEND")

    return {
        "event_state": event_state,
        "event_start": event_start.strftime("%Y-%m-%d %H:%M:%S"),
        "event_end": event_end.strftime("%Y-%m-%d %H:%M:%S"),
    }, 200

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
    app.run(debug=True, port=config.get("PORT"))
