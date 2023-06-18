import sqlite3
import googleapiclient.discovery
import datetime
import json

# Connect to the SQLite database
def create_connection():
    return sqlite3.connect('videos.db')

# Create the videos table if it doesn't exist
def create_videos_table(connection):
    cursor = connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            video_id TEXT,
            channel_id TEXT,
            channel_title TEXT,
            time TEXT,
            thumbnail_url TEXT,
            description TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY,
            name TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS video_tags (
        video_id INTEGER,
        tag_id INTEGER,
        FOREIGN KEY (video_id) REFERENCES videos (id),
        FOREIGN KEY (tag_id) REFERENCES tags (id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            progress_value INTEGER,
            total_channels INTEGER,
            progress_count INTEGER
        )
    """)
    
    connection.commit()

# Function to scrape videos and save to the database
def scrape_video(connection, api_key, channel_id):
    # Create a YouTube API client
    youtube = googleapiclient.discovery.build('youtube', 'v3', developerKey=api_key)
    
    # Calculate the date of one week ago
    one_week_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')


    # # Get the last uploaded videos for the channel
    # videos_response = youtube.search().list(
    #     channelId=channel_id,
    #     part='snippet',
    #     order='date',
    #     maxResults=5,
    #     publishedAfter=one_week_ago
    # ).execute()
    
    # Get the last uploaded videos for the channel
    playlist_response = youtube.channels().list(
        part='contentDetails',
        id=channel_id
    ).execute()

    # Extract relevant information from the API response
    # videos_response = []
    try:
        playlist_id = playlist_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

        videos_response  = youtube.playlistItems().list(
                part='snippet',
                playlistId=playlist_id,
                maxResults=50  # Fetch up to 50 videos per request
            ).execute()

        # videos_response.append(playlist_items_response['items'])
        videos = []
        for video in videos_response['items']:
        # for item in playlist_items_response['items']:
            # item = item[0]
            # print(item)
            # print(item)
            # print(item['id'])
            # try:
            video = {
                'title': item['snippet']['title'],
                'video_id': item['snippet']['resourceId']['videoId'],
                'channel_id': channel_id,
                'channel_title': item['snippet']['channelTitle'],
                'description': item['snippet']['description'],
                'time': item['snippet']['publishedAt'],
                'thumbnail_url': item['snippet']['thumbnails']['default']['url']
            }
            videos.append(video)
            # print(f"video: {video}")
            # except KeyError as e:
            #     pass
        
        print(f"\n videos count is {len(videos)}")
    
    
        # Save the videos to the database, checking for duplicates
        cursor = connection.cursor()
        for video in videos:
            cursor.execute("""
                SELECT COUNT(*) FROM videos WHERE video_id = ?
            """, (video['video_id'],))
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.execute("""
                    INSERT INTO videos (title, video_id, channel_id, channel_title, time, thumbnail_url, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (video['title'], video['video_id'], video['channel_id'], video['channel_title'], 
                    video['time'],video['thumbnail_url'], video['description']))

        connection.commit()
    except Exception as e:
        print(f"channel: {channel_id}=")
        

def save_progress(connection, progress):
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM progress")
    count = cursor.fetchone()[0]
    if count == 0:
        cursor.execute("""
            INSERT INTO progress (progress_value, total_channels, progress_count)
            VALUES (?, ?, ?)
        """, (progress['progress_value'], progress['total_channels'], progress['progress_count']))
    else:
        cursor.execute("""
            UPDATE progress SET progress_value = ?, total_channels = ?, progress_count = ?
        """, (progress['progress_value'], progress['total_channels'], progress['progress_count']))
    
    connection.commit()

# Get progress
def get_progress(connection):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM progress")
    row = cursor.fetchone()

    if row is not None:
        return {
            'progress_value': row[1],
            'total_channels': row[2],
            'progress_count': row[3]
        }
    else:
        return None
