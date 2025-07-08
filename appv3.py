import os
import re
import time
import urllib.request
from flask import Flask, render_template, request, send_file, after_this_request
from pytubefix import YouTube
import pytubefix.request
from pytubefix.exceptions import VideoUnavailable
from urllib.error import HTTPError

# Patch pytubefix request.urlopen to set custom User-Agent header
def custom_urlopen(url, *args, **kwargs):
    if isinstance(url, str):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/114.0.0.0 Safari/537.36"
                )
            }
        )
    else:
        req = url  # already a Request object
    return urllib.request.urlopen(req, *args, **kwargs)

pytubefix.request.urlopen = custom_urlopen

app = Flask(__name__)

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

def fetch_yt_with_retries(link):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            yt = YouTube(link, use_po_token=True)
            yt.check_availability()
            return yt
        except HTTPError as e:
            if e.code == 429:
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                    continue
                else:
                    raise
            else:
                raise
        except VideoUnavailable:
            raise
        except Exception:
            raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    link = request.form['youtube_link']
    choice = request.form['download_choice']

    try:
        yt = fetch_yt_with_retries(link)
        audio_stream = yt.streams.filter(only_audio=True).first()
        video_stream = yt.streams.get_highest_resolution()
    except VideoUnavailable:
        return "The requested video is unavailable or private."
    except HTTPError as e:
        return f"An error occurred while accessing the video: {e}"
    except Exception as e:
        return f"Failed to initialize YouTube: {e}"

    downloads_folder = "/tmp/YTDownloader"
    os.makedirs(downloads_folder, exist_ok=True)

    if choice == "mp4":
        filename = sanitize_filename(f"{yt.title}.mp4")
        filepath = os.path.join(downloads_folder, filename)
        try:
            video_stream.download(output_path=downloads_folder, filename=filename)

            @after_this_request
            def cleanup(response):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Cleanup failed: {e}")
                return response

            return send_file(filepath, as_attachment=True, download_name=filename)
        except Exception as e:
            return f"An error occurred while downloading the video: {e}"

    elif choice == "mp3":
        filename = sanitize_filename(f"{yt.title}.mp3")
        filepath = os.path.join(downloads_folder, filename)
        try:
            audio_stream.download(output_path=downloads_folder, filename=filename)

            @after_this_request
            def cleanup(response):
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Cleanup failed: {e}")
                return response

            return send_file(filepath, as_attachment=True, download_name=filename)
        except Exception as e:
            return f"An error occurred while downloading the audio: {e}"

    else:
        return "Invalid choice. Please enter 'mp4' or 'mp3'."

if __name__ == '__main__':
    app.run(debug=True)
