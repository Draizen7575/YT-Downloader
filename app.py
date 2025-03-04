from flask import Flask, render_template, request, send_file
from pytubefix import YouTube, exceptions
import os
from urllib.error import HTTPError

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    link = request.form['youtube_link']
    try:
        yt = YouTube(link, use_oauth=True, allow_oauth_cache=True)
        audio_stream = yt.streams.filter(only_audio=True).first()
        video_stream = yt.streams.get_highest_resolution()
    except HTTPError as e:
        return f"An error occurred while accessing the video: {e}"
    except exceptions.BotDetection:
        return "Bot detection triggered. Please try again later or use a different link."
    except Exception as e:
        return f"An error occurred: {e}"

    choice = request.form['download_choice']
    try:
        filename = f"{yt.title}.{choice}"
        if choice == "mp4":
            video_stream.download(filename=filename)
        elif choice == "mp3":
            audio_stream.download(filename=filename)
        else:
            return "Invalid choice. Please enter 'mp4' or 'mp3'."
        return send_file(filename, as_attachment=True)
    except Exception as e:
        return f"An error occurred while downloading the {choice}: {e}"

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
