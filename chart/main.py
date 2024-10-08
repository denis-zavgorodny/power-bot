import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import matplotlib

from models.signal import Signal

matplotlib.use('agg')
from datetime import timedelta



def plot(data, min, max):
    for row in data:
        row["timestamp"] = round_to_nearest_minute(row["timestamp"])

    # Convert input data to DataFrame
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['at'] = pd.to_datetime(df['at'])

    # Generate a time series with 1-minute intervals
    time_range = pd.date_range(start=min, end=max, freq='T')

    # Create a DataFrame to hold the time series data
    time_series_df = pd.DataFrame(time_range, columns=['time'])
    time_series_df['value'] = 0

    # Mark 1 if there is a record at the specific time
    for index, row in df.iterrows():
        time_series_df.loc[time_series_df['time'] == row['timestamp'], 'value'] = 1

    # Plot the chart
    plt.figure(figsize=(10, 3))
    plt.plot(time_series_df['time'], time_series_df['value'], marker='o', linestyle='-', color='b')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.title('Power supply over time')
    plt.grid(visible=True, axis='x')
    plt.xticks(rotation=90)
    plt.tight_layout()

    tmpfile = BytesIO()

    plt.savefig(tmpfile, format='png')

    return base64.b64encode(tmpfile.getvalue()).decode('utf-8')

def round_to_nearest_minute(dt: Signal.timestamp):
    # Calculate the seconds since the last minute
    seconds = dt.second + dt.microsecond / 1_000_000

    # Round to the nearest minute
    if seconds >= 30:
        dt += timedelta(minutes=1)

    # Truncate to remove seconds and microseconds
    dt = dt.replace(second=0, microsecond=0)
    return dt
