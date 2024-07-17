import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO
import matplotlib

matplotlib.use('agg')
from datetime import datetime, timedelta

def plot(data):
    # Example input data
    # data = [
    #     {"timestamp": "2024-07-13T12:00:00", "at": "2024-07-13T12:01:00"},
    #     {"timestamp": "2024-07-13T12:05:00", "at": "2024-07-13T12:06:00"},
    #     # Add more records as needed
    # ]

    # Convert input data to DataFrame
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['at'] = pd.to_datetime(df['at'])

    # Determine the start and end times for the time series
    start_time = df['timestamp'].min()
    end_time = df['timestamp'].max()

    # Generate a time series with 1-minute intervals
    time_range = pd.date_range(start=start_time, end=end_time, freq='T')

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
    plt.title('Time Series Chart')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()

    tmpfile = BytesIO()

    plt.savefig(tmpfile, format='png')

    return base64.b64encode(tmpfile.getvalue()).decode('utf-8')

# plot([
#     {"timestamp": "2024-07-13T12:00:00", "at": "2024-07-13T12:01:00"},
#     {"timestamp": "2024-07-13T12:05:00", "at": "2024-07-13T12:06:00"},
#     # Add more records as needed
# ])
