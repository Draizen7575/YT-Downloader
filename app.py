import os
from flask import Flask, render_template, request, send_file
from pytubefix import YouTube
from urllib.error import HTTPError
import re

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '', filename)

@app.route('/download', methods=['POST'])
def download():
    link = request.form['youtube_link']
    try:
        yt = YouTube(link)
        audio_stream = yt.streams.filter(only_audio=True).first()
        video_stream = yt.streams.get_highest_resolution()
    except HTTPError as e:
        return f"An error occurred while accessing the video: {e}"
 
    choice = request.form['download_choice']
    downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads", "YTDownloader")
    
    # Create the downloads folder if it doesn't exist
    os.makedirs(downloads_folder, exist_ok=True)
    
    if choice == "mp4":
        try:
            filename = sanitize_filename(f"{yt.title}.mp4")
            filepath = os.path.join(downloads_folder, filename)
            video_stream.download(output_path=downloads_folder, filename=filename)
            return send_file(filepath, as_attachment=True, download_name=filename)
        except Exception as e:
            return f"An error occurred while downloading the video: {e}"
    elif choice == "mp3":
        try:
            filename = sanitize_filename(f"{yt.title}.mp3")
            filepath = os.path.join(downloads_folder, filename)
            audio_stream.download(output_path=downloads_folder, filename=filename)
            return send_file(filepath, as_attachment=True, download_name=filename)
        except Exception as e:
            return f"An error occurred while downloading the audio: {e}"
    else:
        return "Invalid choice. Please enter 'mp4' or 'mp3'."

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
