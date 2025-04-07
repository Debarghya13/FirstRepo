import streamlit as st
from moviepy.editor import AudioFileClip
import os
import requests
import time

# Function to save uploaded video file
def save_uploaded_file(uploaded_file, output_path="uploads"):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    file_path = os.path.join(output_path, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Function to transcribe audio using AssemblyAI API
def transcribe_audio(audio_file, assemblyai_api_key):
    # Step 1: Upload the audio file to AssemblyAI
    upload_url = "https://api.assemblyai.com/v2/upload"
    headers = {"authorization": assemblyai_api_key}
    try:
        with open(audio_file, "rb") as f:
            upload_response = requests.post(upload_url, headers=headers, files={"file": f})
    except requests.exceptions.RequestException as e:
        st.error(f"Network error during file upload: {e}")
        return ""

    if upload_response.status_code != 200:
        st.error(f"Error uploading file: {upload_response.status_code} - {upload_response.text}")
        return ""

    audio_url = upload_response.json()["upload_url"]

    # Step 2: Request transcription
    transcribe_url = "https://api.assemblyai.com/v2/transcript"
    json_data = {"audio_url": audio_url}
    try:
        transcribe_response = requests.post(transcribe_url, headers=headers, json=json_data)
    except requests.exceptions.RequestException as e:
        st.error(f"Network error during transcription request: {e}")
        return ""

    if transcribe_response.status_code != 200:
        st.error(f"Error requesting transcription: {transcribe_response.status_code} - {transcribe_response.text}")
        return ""

    transcript_id = transcribe_response.json()["id"]

    # Step 3: Poll for transcription result
    timeout = 300  # Timeout in seconds (e.g., 5 minutes)
    start_time = time.time()
    while True:
        result_url = f"{transcribe_url}/{transcript_id}"
        try:
            result_response = requests.get(result_url, headers=headers)
        except requests.exceptions.RequestException as e:
            st.error(f"Network error during polling: {e}")
            return ""

        if result_response.status_code == 200:
            result = result_response.json()
            if result["status"] == "completed":
                # Cleanup temporary files
                if os.path.exists(audio_file):
                    os.remove(audio_file)
                return result["text"]
            elif result["status"] == "failed":
                st.error("Transcription failed.")
                return ""
        else:
            st.error(f"Error polling transcription: {result_response.status_code} - {result_response.text}")
            return ""

        # Check for timeout
        if time.time() - start_time > timeout:
            st.error("Transcription timed out.")
            return ""

        time.sleep(5)  # Wait 5 seconds before polling again

# Streamlit app
st.title("Video Subtitle Generator")
st.write("Upload a video file to generate subtitles.")

# File uploader for video
uploaded_file = st.file_uploader("Upload Video File", type=["mp4", "mkv", "avi", "mov"])

# Input for AssemblyAI API Key
assemblyai_api_key = st.text_input("Enter AssemblyAI API Key:", type="password")

if st.button("Generate Subtitles"):
    if uploaded_file and assemblyai_api_key:
        with st.spinner("Saving uploaded video..."):
            video_file = save_uploaded_file(uploaded_file)

        with st.spinner("Extracting audio from video..."):
            audio_clip = AudioFileClip(video_file)
            wav_file = video_file.replace(".mp4", ".wav").replace(".mkv", ".wav").replace(".avi", ".wav").replace(".mov", ".wav")
            audio_clip.write_audiofile(wav_file)
            audio_clip.close()

        with st.spinner("Transcribing audio..."):
            transcription = transcribe_audio(wav_file, assemblyai_api_key)

        if transcription:
            st.success("Transcription completed!")
            st.text_area("Generated Subtitles:", transcription, height=300)
    else:
        st.error("Please upload a video file and provide an AssemblyAI API Key.")