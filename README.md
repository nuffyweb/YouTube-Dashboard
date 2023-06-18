# YouTube Video Scraper

This is a Python web application that scrapes the last uploaded videos from YouTube channels using the YouTube Data API, saves them to a SQLite database, and displays them on a web page using Flask.

## Features

- Scrapes the last uploaded videos from YouTube channels using API Key
- Saves the video information (title, description, channel, thumbnail URL, etc.) to a SQLite database
- Displays the videos on a web page with pagination
- Allows sorting of video entries by title and upload date
- Supports searching for videos by title
- Allows adding tags to videos
- Provides a settings page to configure the YouTube API key and list of channels to scrape
- Supports progress tracking during the scraping process

## Prerequisites

- Python 3.x
- Flask
- SQLite3

## Installation

1. Clone the repository:
```bash
   git clone https://github.com/your-username/youtube-video-scraper.git
   cd youtube-video-scraper
```
2. Install the required Python dependencies:
```bash
pip install -r requirements.txt
```
3. Set up the YouTube API key:
4. Obtain a YouTube Data API key from the Google Developers Console.
Open the config.ini file and replace the value of API_KEY with your API key.
Set up the list of channels:
5. Open the channels.txt file and add the YouTube channel URLs, each on a new line.
Initialize the SQLite database:
```bash
python create_database.py
```

## Usage
1. Start the Flask server:
```bash
python app.py
Open a web browser and navigate to http://localhost:5000 to access the web application.
```
2. The main page will display the scraped videos, and you can use the pagination and sorting options to navigate and sort the video entries.
3. You can search for videos by title using the search bar.
4. To add tags to a video, click on the "Add Tags" button and enter the tags in the input field. Press Enter or click the "Add" button to save the tags.
6. The settings page (http://localhost:5000/settings) allows you to configure the YouTube API key and the list of channels to scrape.
7. On the settings page, click the "Scrape" button to start scraping the videos. The progress bar will show the progress, and a completion message will be displayed when scraping is finished.

## License
This project is licensed under the MIT License. See the LICENSE file for more information.