import os
import datetime
import json
from googleapiclient.discovery import build
import plotly.graph_objects as go
import plotly.io as pio

API_KEY = os.environ["YOUTUBE_API_KEY"]

def fetch_latest_data() -> list:
    # Build the YouTube API service
    api_service_name = "youtube"
    api_version = "v3"
    youtube = build(api_service_name, api_version, developerKey=API_KEY)

    data=[]
    json_file_name = "channels-data.json"

    with open(json_file_name, "r") as json_file:
        data = json.load(json_file)


    for channel in data:
        # Specify the channel ID 
        channel_id = channel["id"]

        # Retrieve the channel's information
        request = youtube.channels().list(
            part="statistics",
            id=channel_id
        )

        response = request.execute()

        subscriber_count = int(response["items"][0]["statistics"]["subscriberCount"])
        viewCount = int(response["items"][0]["statistics"]["viewCount"])
        
        channel["subscribers"].append({"date": datetime.datetime.now().date().isoformat(), "count": subscriber_count})
        channel["views"].append({"date": datetime.datetime.now().date().isoformat(), "count": viewCount})

    with open(json_file_name, "w") as json_file:    
        json.dump(data,json_file,indent=4)
    
    return data

def generate_graph(channel_name:str,chart_title:str,x_axis_title:str,y_axis_title:str,x_values:list,y_values:list, chart_location:str):

    # Create a bar chart
    fig = go.Figure()

    # Add the bars
    bars = fig.add_trace(go.Bar(x=x_values, y=y_values))

    # Set chart layout
    fig.update_layout(
        title=chart_title,
        xaxis=dict(title=x_axis_title),
        yaxis=dict(title=y_axis_title)
    )

    # Add annotations for percentage changes based on the previous bar's value
    for i in range(1, len(x_values)):
        change = ((y_values[i] - y_values[i - 1]) / y_values[i - 1]) * 100
        fig.add_annotation(
            text=f'{change:.2f}%',
            x=x_values[i],
            y=y_values[i] + 1,  # Adjust the y-coordinate for annotation placement
            showarrow=False
        )

    image_path = chart_location + channel_name + '.html'
    pio.write_html(fig, image_path)


def main():
    data = fetch_latest_data()
    for channel in data:
        dates = [week["date"] for week in channel["subscribers"]]
        subscribers =  [subscribers["count"] for subscribers in channel["subscribers"]]
        views =  [views["count"] for views in channel["views"]]
        generate_graph(channel["name"], "Total Subscribers -" + channel["name"], "Time", "Subscribers", dates, subscribers,'docs/charts/subs/')
        generate_graph(channel["name"], "Total Views -" + channel["name"], "Time", "Views", dates, views, 'docs/charts/views/')
    
    
if __name__ == "__main__":
    main()