from flask import Flask, render_template, request
import requests
import time

app = Flask(__name__)

from dotenv import load_dotenv
import os

load_dotenv()   # Load .env file
API_KEY = os.getenv("API_KEY")

#API_KEY = open("api.txt").read().strip()
UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"

headers = {"authorization": API_KEY}

# ---------- UPLOAD TO ASSEMBLYAI ----------
def upload_to_assemblyai(file_path):
    CHUNK_SIZE = 5_242_880
    headers = {"authorization": API_KEY}

    def read_file(path):
        with open(path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                yield chunk

    response = requests.post(UPLOAD_URL, headers=headers, data=read_file(file_path))

    try:
        return response.json().get("upload_url")
    except:
        return None


# ---------- START TRANSCRIPTION ----------
def start_transcription(audio_url):
    data = {"audio_url": audio_url}
    response = requests.post(TRANSCRIPT_URL, json=data, headers=headers)
    return response.json().get("id")


# ---------- POLL FOR TRANSCRIPTION ----------
def get_transcription(transcript_id):
    url = f"{TRANSCRIPT_URL}/{transcript_id}"

    while True:
        result = requests.get(url, headers=headers).json()
        status = result.get("status")

        if status == "completed":
            return result.get("text")
        elif status == "error":
            return "Transcription Failed"

        time.sleep(3)


# ---------- ROUTES ----------
@app.route("/")
def index():
    return render_template("index.html")




@app.route("/transcribe", methods=["POST"])
def transcribe():
    if "audio_file" not in request.files:
        return render_template("index.html", upload_error=True)

    file = request.files["audio_file"]
    file_path = "uploaded_audio.mp4"
    file.save(file_path)

    # Show upload success message
    upload_success = True

    audio_url = upload_to_assemblyai(file_path)

    if not audio_url:
        return render_template("index.html", upload_error=True)

    transcript_id = start_transcription(audio_url)
    text = get_transcription(transcript_id)

    return render_template(
        "index.html",
        upload_success=True,
        transcription_ready=True,
        transcript=text
    )



#  RUN 
if __name__ == "__main__":
    app.run(debug=True)
