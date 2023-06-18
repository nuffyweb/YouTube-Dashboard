from flask import Flask, render_template, request, redirect, url_for, jsonify, session, Response
from database import create_connection, create_videos_table, scrape_video, get_progress, save_progress
from tqdm import tqdm
import time

# Read API Key from a separate file
with open("api_key.key", "r") as f:
    API_KEY = f.read().strip()

# Create Flask application
app = Flask(__name__, static_url_path="/videos", static_folder='static')

@app.route('/videos')
def display_videos():
    search_query = request.args.get('search', '')
    # Get the requested page number from the URL parameters
    page = int(request.args.get('page', 1))
    videos_per_page = 50  # Number of videos to display per page
    # Fetch a portion of videos based on the page number and videos per page
    offset = (page - 1) * videos_per_page
    
    # Connect to the SQLite database
    connection = create_connection()
    # Fetch the videos from the database
    cursor = connection.cursor()
    # Modify the SQL query to include the search condition
    query = """
        SELECT videos.*, GROUP_CONCAT(tags.name) AS tag_names
        FROM videos
        LEFT JOIN video_tags ON videos.id = video_tags.video_id
        LEFT JOIN tags ON video_tags.tag_id = tags.id
        WHERE title LIKE '%' || ? || '%'
        GROUP BY videos.id
        ORDER BY time DESC
        LIMIT ? OFFSET ?
    """
    cursor.execute(query, (search_query, videos_per_page, offset))
    video_rows = cursor.fetchall()
    column_names = [description[0] for description in cursor.description]  # Get column names
    
    # Get the total number of videos in the database
    total_videos_query = "SELECT COUNT(*) FROM videos WHERE title LIKE '%' || ? || '%'"
    cursor.execute(total_videos_query, (search_query,))
    total_videos = cursor.fetchone()[0]

    # Calculate the total number of pages
    total_pages = (total_videos // videos_per_page) + (total_videos % videos_per_page > 0)

    # Close the database connection
    connection.close()
    
    # Convert rows to dictionaries for easier data manipulation in the template
    videos = []
    for row in video_rows:
        video = dict(zip(column_names, row))
        video['tags'] = video['tag_names'].split(',') if video['tag_names'] else []
        videos.append(video)

    return render_template('videos.html', videos=videos, search_query=search_query, page=page, total_pages=total_pages)

@app.route('/videos/<int:video_id>/add_tags', methods=['POST'])
def add_tags(video_id):
    # Retrieve the submitted tags from the form data
    tags = request.form.get('tags')
    tags = [tag.strip() for tag in tags.split(',')]

    # Connect to the SQLite database
    connection = create_connection()
    # Fetch the videos from the database
    cursor = connection.cursor()

    # Get the video ID and tag IDs
    video_id = video_id
    tag_ids = []

    # Check if the tags already exist in the database, otherwise insert them
    for tag in tags:
        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag,))
        tag_row = cursor.fetchone()
        if tag_row is None:
            cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag,))
            tag_ids.append(cursor.lastrowid)
        else:
            tag_ids.append(tag_row[0])

    # Associate the tags with the video
    for tag_id in tag_ids:
        cursor.execute("INSERT INTO video_tags (video_id, tag_id) VALUES (?, ?)", (video_id, tag_id))

    # Commit the changes and close the database connection
    connection.commit()
    connection.close()

    # Redirect back to the video listing page
    return redirect('/videos')

@app.route('/tags')
def get_tags():
    # Connect to the SQLite database
    connection = create_connection()
    cursor = connection.cursor()

    # Get the query parameter for filtering tags
    query = request.args.get('query', '')

    # Fetch existing tags from the database based on the query
    cursor.execute("""
        SELECT name FROM tags
        WHERE name LIKE ? || '%'
    """, (query,))
    tag_rows = cursor.fetchall()

    # Close the database connection
    connection.close()

    # Extract the tags from the rows
    tags = [row[0] for row in tag_rows]

    # Return the list of tags as JSON
    return jsonify(tags)

@app.route('/add_channel', methods=['POST'])
def add_channel():
    # Get the form data
    channel = request.form.get('channel')
    # tags = request.form.get('tags')
    
    # Connect to the SQLite database
    connection = create_connection()
    # Fetch the videos from the database
    cursor = connection.cursor()
    
    # Insert video details into the 'videos' table
    cursor.execute("""
        INSERT INTO videos (channel)
        VALUES (?, ?)
    """, (channel))
    
    # Get the ID of the newly inserted video
    # video_id = cursor.lastrowid
    
    # Close the database connection
    connection.close()

# Initialize the database and scrape videos from channels
def initialize_database():
    # Connect to the SQLite database
    connection = create_connection()
    # Fetch the videos from the database
    cursor = connection.cursor()

    # Create the videos table if it doesn't exist
    create_videos_table(connection)

    # scrape_videos(connection)
    
    # Close the database connection
    connection.close()

def scrape_videos(connection):
    # Read the channels from channels.txt and scrape videos for each channel
    with open("channels.txt", "r") as f:
        channels = f.readlines()

    # UNCOMMENT TO SCRAPE
    for channel in tqdm(channels):
        channel_id = channel.strip()
        scrape_video(connection, API_KEY, channel_id)

@app.route('/settings', methods=['GET'])
def settings():
    connection = create_connection()
    reset_progress(connection)
    
    return render_template('settings.html')

def get_channels():
    channels = []
    with open("channels.txt", "r") as f:
        channels = f.readlines()
    return channels

@app.route('/scrape', methods=['GET'])
def scrape():
    connection = create_connection()
    progress_data = get_progress(connection)
    if progress_data['progress_value'] is None:
        return jsonify({
        'progress': 0,
        })
    elif progress_data['progress_value'] is not None and progress_data['progress_value'] < 100:
        return jsonify({
        'progress': progress_data['progress_value'],
        })
    else:
        reset_progress(connection)
        return jsonify({
            'finished': 100
        })
        

@app.route('/progress', methods=['GET'])
def progress():
    connection = create_connection()
    progress = get_progress(connection)
    channels = get_channels()
    pr = 0
    # Initialize progress variables
    total_channels = len(channels)
    if progress['progress_value'] is None:
        initialize_progress(connection, total_channels)
        progress = get_progress(connection)
        # Loop through each channel and perform scraping
        for i in tqdm(channels):
            pr += 1
            time.sleep(0.1)
            progress_value = int((pr / total_channels) * 100)
            update_progress(connection, progress_value, pr + 1)

    return jsonify({
        'progress': progress['progress_value'],
        'total_channels': progress['total_channels'],
        'progress_count': progress['progress_count']
    })

def initialize_progress(connection, total_channels):
    progress = {
        'progress_value': 0,
        'total_channels': total_channels,
        'progress_count': 0
    }
    save_progress(connection, progress)

# Update progress
def update_progress(connection, progress_value, progress_count):
    progress = {
        'progress_value': progress_value,
        'total_channels': None,
        'progress_count': progress_count
    }
    save_progress(connection, progress)

# Reset progress
def reset_progress(connection):
    progress = {
        'progress_value': None,
        'total_channels': 0,
        'progress_count': 0
    }
    save_progress(connection, progress)

@app.route('/')
def index():
    return redirect(url_for('display_videos'))

# set the secret key.  keep this really secret:
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

# Run the Flask application
if __name__ == '__main__':
    initialize_database()
    app.run(host='0.0.0.0', port=80)
    # app.register_blueprint(sse, url_prefix='/stream')
