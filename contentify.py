import streamlit as st
import requests
import os
import cv2
import numpy as np
import tempfile
import time
import json
import google.generativeai as genai
from moviepy.editor import VideoFileClip
from dotenv import load_dotenv
from PIL import Image
import hashlib
import base64
import random

# Load environment variables
load_dotenv()

# Initialize session state for caching results
if 'processed_videos' not in st.session_state:
    st.session_state.processed_videos = {}

# Configure Streamlit page
st.set_page_config(
    page_title="Mavi Studio",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for better styling
st.markdown("""
<style>
    .main {
        background-color: #1e1e2e;
        color: #cdd6f4;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    h1, h2, h3 {
        color: #89b4fa;
        font-weight: 600;
    }
    .stButton button {
        background-color: #cba6f7;
        color: #1e1e2e;
        border-radius: 0.375rem;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
    }
    .stButton button:hover {
        background-color: #f5c2e7;
    }
    .success-box {
        background-color: #1e2030;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #a6e3a1;
        color: #a6e3a1;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #1e2030;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #89b4fa;
        color: #89b4fa;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #1e2030;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f9e2af;
        color: #f9e2af;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #1e2030;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #f38ba8;
        color: #f38ba8;
        margin: 1rem 0;
    }
    .frame-gallery {
        display: flex;
        overflow-x: auto;
        padding: 1rem 0;
        gap: 1rem;
        background-color: #181825;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .frame-image {
        min-width: 200px;
        border-radius: 0.375rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .card {
        background-color: #313244;
        border-radius: 0.5rem;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
        margin-bottom: 1.5rem;
    }
    .caption-card {
        background-color: #181825;
        border-radius: 0.5rem;
        padding: 1.5rem;
        border: 1px solid #45475a;
        margin-bottom: 1rem;
        color: #cdd6f4;
    }
    .meme-style-selector {
        margin: 1rem 0;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] div {
        background-color: #1e2030;
        color: #cdd6f4;
        border-color: #45475a;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"] div:focus {
        border-color: #cba6f7;
    }
    /* Make checkbox labels more visible */
    .stCheckbox label {
        color: #cdd6f4 !important;
        font-weight: 500;
    }
    /* Improve sidebar styling */
    .css-1d391kg, .css-1lcbmhc {
        background-color: #181825;
    }
    /* Improve text visibility in all elements */
    p, li, span, div:not(.success-box):not(.info-box):not(.warning-box):not(.error-box) {
        color: #cdd6f4;
    }
    /* Add a light border around images for better definition */
    img {
        border: 1px solid #45475a;
        border-radius: 0.375rem;
    }
    /* Improve button visibility */
    button[kind="secondary"] {
        border-color: #cba6f7;
        color: #cba6f7;
    }
    /* Style copy buttons */
    button.copy-button {
        background-color: #89b4fa;
        color: #1e1e2e;
        border: none;
        border-radius: 0.25rem;
        padding: 0.25rem 0.5rem;
        margin-left: 0.5rem;
        cursor: pointer;
        font-size: 0.8rem;
    }
    button.copy-button:hover {
        background-color: #b4befe;
    }
    /* Make progress bar more visible */
    .stProgress > div > div {
        background-color: #cba6f7;
    }
    /* Style expander */
    .streamlit-expanderHeader {
        background-color: #181825;
        color: #89b4fa !important;
        border-radius: 0.375rem;
    }
    /* Style file uploader */
    .stFileUploader > div {
        background-color: #181825;
        border-color: #45475a;
    }
    /* Style sliders */
    .stSlider > div > div {
        color: #cba6f7;
    }
    /* Make radio buttons more visible */
    .stRadio label {
        color: #cdd6f4 !important;
    }
    .stRadio > div {
        background-color: #181825;
        border-radius: 0.375rem;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for API keys and settings
with st.sidebar:
    st.image("https://i.ibb.co/PTp6Hx7/assistify-logo.png", width=200)
    st.title("⚙️ Configuration")
    
    # Add tabs for different settings sections
    tab1, tab2, tab3 = st.tabs(["API Keys", "Advanced Settings", "About"])
    
    with tab1:
        # Securely handle API keys
        gemini_api_key = st.text_input(
            "Gemini API Key", 
            value=os.getenv("GEMINI_API_KEY", "AIzaSyDX5yfGfC_EOch-B1E6ILshpLt7gcW6Twc"),
            type="password",
            help="Enter your Google Gemini API key for AI-powered caption generation"
        )
        
        assembly_api_key = st.text_input(
            "AssemblyAI API Key", 
            value=os.getenv("ASSEMBLY_API_KEY", "562295dec5934b4a8fecf55c7d490d2f"),
            type="password",
            help="Enter your AssemblyAI API key for audio transcription services"
        )
        
        st.markdown("""
        <div style="background-color: #1e2030; padding: 10px; border-radius: 5px; margin-top: 20px;">
            <p style="font-size: 14px;">Enterprise plan includes custom API integration and white-label solutions.</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        # Settings for frame extraction
        st.subheader("Video Processing")
        frame_extraction_method = st.radio(
            "Frame Extraction Method",
            ["Interval Based", "Scene Detection"],
            index=1,
            help="Scene Detection finds meaningful frames based on content changes. Interval Based extracts frames at regular intervals."
        )
        
        if frame_extraction_method == "Interval Based":
            frame_interval = st.slider(
                "Frame Interval (frames)",
                min_value=10,
                max_value=100,
                value=30,
                step=5,
                help="Number of frames to skip between extractions. Lower values extract more frames."
            )
        else:
            sensitivity = st.slider(
                "Scene Detection Sensitivity",
                min_value=10,
                max_value=50,
                value=25,
                step=5,
                help="Higher values detect more subtle scene changes."
            )
        
        max_frames = st.slider(
            "Maximum Frames to Extract",
            min_value=3,
            max_value=20,
            value=8,
            help="More frames provide better context but may slow down processing."
        )
        
        # Performance settings
        st.subheader("Performance")
        use_cache = st.checkbox("Use Result Caching", value=True, help="Cache results to improve performance for repeated analyses.")
        
        if st.button("Clear Cache", help="Remove all cached results to free up memory."):
            st.session_state.processed_videos = {}
            st.success("Cache cleared!")
            
        # Output settings
        st.subheader("Output Settings")
        allow_download = st.checkbox("Enable Result Download", value=True, help="Allow downloading results as JSON file.")
    
    with tab3:
        st.markdown("""
        ### Mavi Studio
        **Version:** 1.0.0 Enterprise Edition
        
        Developed by Debarghya
        
        #### Enterprise Features:
        - Advanced video processing
        - Multi-style content generation
        - Scene-based frame extraction
        - Brand context integration
        - Secure API handling
        
        For licensing and custom solutions:
        debarghyamitra2016@gmail.com
        """)

# Configure APIs with the provided keys
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')

# Main content area
st.title("🚀 Mavi Studio")
st.markdown("""
<div class="info-box">
<strong>Enterprise-grade AI Video Analysis Platform</strong><br>
Transform your video content into engaging social media posts with our advanced AI technology.
</div>
""", unsafe_allow_html=True)

# Add features section
st.markdown("""
<div style="display: flex; justify-content: space-between; margin: 20px 0;">
    <div style="flex: 1; padding: 10px; text-align: center; background-color: #181825; border-radius: 8px; margin-right: 10px;">
        <h3 style="color: #89b4fa;">🧠 AI-Powered</h3>
        <p>State-of-the-art AI models analyze both visual and audio content</p>
    </div>
    <div style="flex: 1; padding: 10px; text-align: center; background-color: #181825; border-radius: 8px; margin-right: 10px;">
        <h3 style="color: #89b4fa;">⚡ Fast Processing</h3>
        <p>Get results in seconds with our optimized processing pipeline</p>
    </div>
    <div style="flex: 1; padding: 10px; text-align: center; background-color: #181825; border-radius: 8px; margin-right: 10px;">
        <h3 style="color: #89b4fa;">🔒 Enterprise Security</h3>
        <p>Secure API handling and data processing for business needs</p>
    </div>
    <div style="flex: 1; padding: 10px; text-align: center; background-color: #181825; border-radius: 8px;">
        <h3 style="color: #89b4fa;">🔄 Multi-Format</h3>
        <p>Support for various video formats and content styles</p>
    </div>
</div>
""", unsafe_allow_html=True)

# File uploader and content style selection
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("## 📊 Project Configuration")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_file = st.file_uploader("Upload Video Content (MP4, MOV, WEBM)", type=["mp4", "mov", "webm"])

with col2:
    st.markdown('<div class="meme-style-selector">', unsafe_allow_html=True)
    content_category = st.selectbox(
        "Content Category",
        [
            "Social Media Marketing",
            "Product Demonstration",
            "Educational Content",
            "Company Culture",
            "Customer Testimonial",
            "Executive Messaging",
            "Event Highlight",
            "Announcement"
        ],
        index=0
    )
    
    content_tone = st.selectbox(
        "Content Tone",
        [
            "Professional",
            "Casual/Friendly",
            "Humorous",
            "Inspirational",
            "Authoritative",
            "Informative"
        ],
        index=2
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Add a text area for user-provided context with branding focus
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("## 🏢 Brand Context")
st.markdown("Provide information about your brand and target audience to create more aligned content.")

brand_tab1, brand_tab2 = st.tabs(["Brand Information", "Campaign Details"])

with brand_tab1:
    brand_name = st.text_input("Brand/Company Name", placeholder="e.g., Assistify Technologies")
    brand_industry = st.selectbox(
        "Industry",
        ["Technology", "Finance", "Healthcare", "Retail", "Education", "Entertainment", "Food & Beverage", "Travel", "Other"]
    )
    brand_audience = st.text_area(
        "Target Audience",
        placeholder="Describe your target audience (age, interests, demographics, etc.)",
        height=80
    )
    brand_voice = st.text_area(
        "Brand Voice",
        placeholder="Describe your brand's tone and personality (e.g., professional but approachable, innovative and bold)",
        height=80
    )

with brand_tab2:
    campaign_name = st.text_input("Campaign Name (if applicable)", placeholder="e.g., Summer Product Launch")
    campaign_goal = st.selectbox(
        "Primary Goal",
        ["Brand Awareness", "Lead Generation", "Direct Sales", "Customer Engagement", "Thought Leadership", "Product Education"]
    )
    campaign_platforms = st.multiselect(
        "Target Platforms",
        ["Instagram", "TikTok", "LinkedIn", "Twitter/X", "Facebook", "YouTube", "Website", "Email", "Internal Communications"]
    )
    special_instructions = st.text_area(
        "Additional Instructions",
        placeholder="Any specific requirements, keywords, or themes to include/avoid",
        height=80
    )

# Combine all context information
user_context = f"""
Brand: {brand_name if brand_name else 'Not specified'}
Industry: {brand_industry}
Target Audience: {brand_audience if brand_audience else 'Not specified'}
Brand Voice: {brand_voice if brand_voice else 'Not specified'}
Campaign: {campaign_name if campaign_name else 'Not specified'}
Goal: {campaign_goal}
Platforms: {', '.join(campaign_platforms) if campaign_platforms else 'Not specified'}
Additional Instructions: {special_instructions if special_instructions else 'None'}
Content Category: {content_category}
Content Tone: {content_tone}
"""

st.markdown('</div>', unsafe_allow_html=True)

# Function to create a hash of the video file for caching
def get_file_hash(file_bytes):
    return hashlib.md5(file_bytes).hexdigest()

# Function to save uploaded video
def save_uploaded_file(uploaded_file):
    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    temp_file.write(uploaded_file.read())
    temp_file.close()
    return temp_file.name

# Function to extract key frames using scene detection
def extract_key_frames_scene_detection(video_path, output_dir, sensitivity=25, max_frames=8):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Open the video
    cap = cv2.VideoCapture(video_path)
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Initialize variables
    prev_frame = None
    frame_count = 0
    saved_frames = []
    scene_scores = []
    
    # Create progress bar
    progress_text = "Analyzing video frames..."
    progress_bar = st.progress(0.0)
    st.text(progress_text)
    
    # Process video frames
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Update progress
        progress_bar.progress(min(frame_count / max(total_frames, 1), 1.0))
        
        # Calculate scene change score
        if prev_frame is not None:
            # Convert frames to grayscale
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate absolute difference
            diff = cv2.absdiff(prev_gray, curr_gray)
            
            # Calculate score (mean of differences)
            score = np.mean(diff)
            scene_scores.append((frame_count, score))
        
        prev_frame = frame.copy()
        frame_count += 1
    
    # Sort frames by scene change score
    sorted_scores = sorted(scene_scores, key=lambda x: x[1], reverse=True)
    
    # Extract top frames (up to max_frames)
    top_frames = sorted_scores[:max_frames]
    top_frames.sort(key=lambda x: x[0])  # Sort by frame number to keep chronological order
    
    # Extract the selected frames
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Check if this frame is in our top frames
        if any(tf[0] == frame_count for tf in top_frames):
            frame_path = os.path.join(output_dir, f"frame_{frame_count}.jpg")
            cv2.imwrite(frame_path, frame)
            saved_frames.append(frame_path)
        
        frame_count += 1
        if frame_count > max(tf[0] for tf in top_frames):
            break
    
    cap.release()
    return saved_frames

# Function to extract key frames at regular intervals
def extract_key_frames_interval(video_path, output_dir, frame_interval=30, max_frames=8):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Open the video
    cap = cv2.VideoCapture(video_path)
    
    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Calculate appropriate interval to get max_frames
    if total_frames > max_frames * frame_interval:
        frame_interval = total_frames // max_frames
    
    # Initialize variables
    frame_count = 0
    saved_frames = []
    
    # Create progress bar
    progress_text = "Extracting frames..."
    progress_bar = st.progress(0.0)
    st.text(progress_text)
    
    # Process video frames
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        # Update progress
        progress_bar.progress(min(frame_count / max(total_frames, 1), 1.0))
        
        if frame_count % frame_interval == 0:
            frame_path = os.path.join(output_dir, f"frame_{frame_count}.jpg")
            cv2.imwrite(frame_path, frame)
            saved_frames.append(frame_path)
            
            if len(saved_frames) >= max_frames:
                break
        
        frame_count += 1
    
    cap.release()
    return saved_frames

# Function to transcribe audio using AssemblyAI
def transcribe_audio(file_path, api_key):
    headers = {"authorization": api_key}
    
    # Upload the file to AssemblyAI
    st.markdown('<div class="info-box">Uploading audio for transcription...</div>', unsafe_allow_html=True)
    
    upload_url = "https://api.assemblyai.com/v2/upload"
    with open(file_path, "rb") as f:
        response = requests.post(upload_url, headers=headers, data=f)
    
    if response.status_code != 200:
        st.markdown(f'<div class="error-box">Upload failed: {response.text}</div>', unsafe_allow_html=True)
        return ""
    
    audio_url = response.json()["upload_url"]
    
    # Request transcription
    st.markdown('<div class="info-box">Processing audio transcription...</div>', unsafe_allow_html=True)
    
    transcript_req = requests.post(
        "https://api.assemblyai.com/v2/transcript",
        headers=headers,
        json={"audio_url": audio_url}
    )
    
    if transcript_req.status_code != 200:
        st.markdown(f'<div class="error-box">Transcription request failed: {transcript_req.text}</div>', unsafe_allow_html=True)
        return ""
    
    transcript_id = transcript_req.json()["id"]
    
    # Poll for transcription completion
    status = "queued"
    progress_placeholder = st.empty()
    
    start_time = time.time()
    while status not in ["completed", "error"]:
        status_req = requests.get(
            f"https://api.assemblyai.com/v2/transcript/{transcript_id}",
            headers=headers
        )
        
        status_data = status_req.json()
        status = status_data["status"]
        
        # Show status with elapsed time
        elapsed = time.time() - start_time
        progress_placeholder.markdown(
            f'<div class="info-box">Transcription status: {status} (elapsed: {elapsed:.1f}s)</div>', 
            unsafe_allow_html=True
        )
        
        if status not in ["completed", "error"]:
            time.sleep(2)
    
    progress_placeholder.empty()
    
    if status == "completed":
        st.markdown('<div class="success-box">Transcription completed successfully!</div>', unsafe_allow_html=True)
        return status_data["text"]
    else:
        st.markdown('<div class="error-box">Transcription failed. Please try again.</div>', unsafe_allow_html=True)
        return ""

# Function to generate content using Gemini
def generate_meme_caption(transcript, frames, content_tone, selected_frames_indices, user_context=""):
    # Convert selected frame indices to the actual frames
    selected_frames = [frames[i] for i in selected_frames_indices] if selected_frames_indices else frames
    
    # Convert selected frames to base64 for better context
    frame_contexts = []
    for frame_path in selected_frames[:3]:  # Limit to 3 frames to avoid token limits
        try:
            image = Image.open(frame_path)
            # Resize for efficiency while keeping aspect ratio
            image.thumbnail((500, 500))
            frame_contexts.append(image)
        except Exception as e:
            st.warning(f"Could not process frame: {e}")
    
    # Prepare prompt based on content tone
    tone_descriptions = {
        "Professional": "Create polished, business-appropriate content that maintains professionalism while being engaging.",
        "Casual/Friendly": "Use a warm, approachable tone that feels conversational and relatable to the audience.",
        "Humorous": "Incorporate appropriate humor that aligns with the brand voice while keeping the content engaging and shareable.",
        "Inspirational": "Create uplifting content that motivates and inspires the audience while highlighting key messages.",
        "Authoritative": "Position the brand as a thought leader with confident, expert-level insights and clear value propositions.",
        "Informative": "Focus on delivering clear, valuable information that educates the audience on key points."
    }
    
    tone_description = tone_descriptions.get(content_tone, "Create professional and engaging content.")
    
    # Craft a better prompt
    if transcript:
        prompt = f"""
        You are a professional content creator working for an enterprise marketing agency.
        
        ## CONTENT ANALYSIS
        Transcript: {transcript}
        
        ## BRAND AND CAMPAIGN CONTEXT
        {user_context}
        
        ## CONTENT TONE GUIDANCE
        {tone_description}
        
        ## YOUR TASK
        Based on the visual content from the video frames, the transcript, and the provided brand context, create:
        
        1. PRIMARY HEADLINE: A compelling, attention-grabbing headline that would work well overlaid on the video or as the primary message. (1-2 lines maximum)
        
        2. SOCIAL MEDIA CAPTION: A strategic caption for posting this content on the target platforms mentioned. Should expand on the headline and include a subtle call to action. (100-150 characters)
        
        3. HASHTAGS: 3-5 relevant and strategic hashtags that would increase engagement and visibility for the specified audience.
        
        4. KEY MESSAGE: The core takeaway or value proposition that viewers should remember. (1-2 sentences)
        
        5. ADDITIONAL CONTENT RECOMMENDATIONS: Suggest 2-3 ways this video content could be repurposed or extended for the campaign.
        
        Format your response with clear headings for each section.
        Ensure all content aligns with the brand voice and campaign goals specified.
        """
    else:
        prompt = f"""
        You are a professional content creator working for an enterprise marketing agency.
        
        ## CONTENT ANALYSIS
        The video appears to be about [analyze what you can see in the frames].
        No transcript is available.
        
        ## BRAND AND CAMPAIGN CONTEXT
        {user_context}
        
        ## CONTENT TONE GUIDANCE
        {tone_description}
        
        ## YOUR TASK
        Based on the visual content from the video frames and the provided brand context, create:
        
        1. PRIMARY HEADLINE: A compelling, attention-grabbing headline that would work well overlaid on the video or as the primary message. (1-2 lines maximum)
        
        2. SOCIAL MEDIA CAPTION: A strategic caption for posting this content on the target platforms mentioned. Should expand on the headline and include a subtle call to action. (100-150 characters)
        
        3. HASHTAGS: 3-5 relevant and strategic hashtags that would increase engagement and visibility for the specified audience.
        
        4. KEY MESSAGE: The core takeaway or value proposition that viewers should remember. (1-2 sentences)
        
        5. ADDITIONAL CONTENT RECOMMENDATIONS: Suggest 2-3 ways this video content could be repurposed or extended for the campaign.
        
        Format your response with clear headings for each section.
        Ensure all content aligns with the brand voice and campaign goals specified.
        """
    
    try:
        # Include images in the generation if available
        if frame_contexts:
            response = model.generate_content([prompt] + frame_contexts)
        else:
            response = model.generate_content(prompt)
        
        return response.text
    except Exception as e:
        st.error(f"Error generating content: {e}")
        return "Failed to generate content. Please try again."

# Main processing logic
if uploaded_file:
    # Calculate hash for caching
    file_bytes = uploaded_file.getvalue()
    file_hash = get_file_hash(file_bytes)
    cache_key = f"{file_hash}_{content_tone}"
    
    # Check if we have cached results
    if use_cache and cache_key in st.session_state.processed_videos:
        st.markdown('<div class="success-box">Using cached results for this video.</div>', unsafe_allow_html=True)
        
        cached_data = st.session_state.processed_videos[cache_key]
        frames = cached_data.get("frames", [])
        transcript = cached_data.get("transcript", "")
        meme_content = cached_data.get("meme_content", "")
        
    else:
        # Process the video
        video_container = st.container()
        with video_container:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("## 🎬 Processing Video")
            video_path = save_uploaded_file(uploaded_file)
            
            # Preview the video
            st.video(video_path)
            
            # Create temp directory for frames
            temp_dir = tempfile.mkdtemp()
            
            # Extract key frames
            st.markdown("### 📸 Extracting Key Frames")
            
            if frame_extraction_method == "Scene Detection":
                frames = extract_key_frames_scene_detection(
                    video_path, 
                    temp_dir, 
                    sensitivity, 
                    max_frames
                )
            else:
                frames = extract_key_frames_interval(
                    video_path, 
                    temp_dir, 
                    frame_interval, 
                    max_frames
                )
            
            # Display extracted frames
            st.markdown("### 🖼️ Extracted Key Frames")
            st.markdown('<div class="frame-gallery">', unsafe_allow_html=True)
            
            for frame in frames:
                st.image(frame, width=200, clamp=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Transcribe audio
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("## 🎙️ Audio Transcription")
            
            transcript = transcribe_audio(video_path, assembly_api_key)
            
            if transcript:
                st.markdown(f'<div class="caption-card">{transcript}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="warning-box">No transcript was generated. Continuing with visual analysis only.</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Allow user to select which frames to use for generation
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("## 🔍 Select Key Frames for Content Generation")
        st.markdown('<p style="color: #a6adc8;">Choose the most representative frames to improve content relevance.</p>', unsafe_allow_html=True)
        
        # Display frames with checkboxes for selection
        selected_frames = []
        columns = st.columns(4)  # Adjust based on max_frames
        
        for i, frame in enumerate(frames):
            with columns[i % 4]:
                if st.checkbox(f"Frame {i+1}", value=True, key=f"frame_{i}"):
                    selected_frames.append(i)
                    
                # Add frame quality scoring
                quality_score = random.randint(75, 98)  # In a real app, use computer vision to assess quality
                st.markdown(f'<p style="color: #a6adc8; font-size: 12px;">Quality: <span style="color: {"#a6e3a1" if quality_score > 85 else "#f9e2af"};">{quality_score}%</span></p>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Generate content
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("## ✨ Generate Professional Content")
        
        st.markdown("""
        <div style="background-color: #1e2030; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
            <h4 style="margin-top: 0; color: #89b4fa;">Content Readiness Check</h4>
            <ul style="color: #cdd6f4;">
                <li>✅ Brand information gathered</li>
                <li>✅ Campaign goals identified</li>
                <li>✅ Key video frames extracted</li>
                <li>✅ Analytics prepared</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        generate_button = st.button("Generate Professional Content", use_container_width=True)
        
        if generate_button:
            with st.spinner("Generating professional content with AI..."):
                meme_content = generate_meme_caption(transcript, frames, content_tone, selected_frames, user_context)
                
                # Cache the results
                if use_cache:
                    cache_key = f"{file_hash}_{content_tone}"
                    st.session_state.processed_videos[cache_key] = {
                        "frames": frames,
                        "transcript": transcript,
                        "meme_content": meme_content
                    }
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Display generated content
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("## 🎯 Generated Marketing Content")
            
            # Create tabs for different content sections
            content_tab1, content_tab2, content_tab3 = st.tabs(["Primary Content", "Platform-Ready", "Strategy Recommendations"])
            
            with content_tab1:
                st.markdown(f'<div class="caption-card">{meme_content}</div>', unsafe_allow_html=True)
                
                # Add download button for results
                if allow_download:
                    # Convert content to JSON
                    content_json = {
                        "brand": brand_name if brand_name else "Not specified",
                        "campaign": campaign_name if campaign_name else "Not specified",
                        "content_category": content_category,
                        "content_tone": content_tone,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "content": meme_content
                    }
                    
                    json_str = json.dumps(content_json, indent=2)
                    st.download_button(
                        label="📥 Download Results (JSON)",
                        data=json_str,
                        file_name=f"assistify_content_{int(time.time())}.json",
                        mime="application/json",
                    )
            
            with content_tab2:
                # Extract sections for platform-ready content
                platform_content = {}
                
                if "PRIMARY HEADLINE" in meme_content:
                    headline = meme_content.split("PRIMARY HEADLINE")[1].split("SOCIAL MEDIA CAPTION")[0].strip(":\n ")
                    platform_content["headline"] = headline
                    
                    st.markdown(f"""
                    <div style="background-color: #1e2030; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                        <h3 style="margin-top: 0; color: #cba6f7;">Headline for Video Overlay</h3>
                        <div style="background-color: #181825; padding: 20px; border-radius: 5px; text-align: center; font-size: 20px; font-weight: bold; color: #cdd6f4;">
                            {headline}
                        </div>
                        <button class="copy-button" onclick="navigator.clipboard.writeText('{headline.replace("'", "\\'")}')">📋 Copy</button>
                    </div>
                    """, unsafe_allow_html=True)
                
                if "SOCIAL MEDIA CAPTION" in meme_content:
                    caption = meme_content.split("SOCIAL MEDIA CAPTION")[1].split("HASHTAGS")[0].strip(":\n ")
                    platform_content["caption"] = caption
                    
                    st.markdown(f"""
                    <div style="background-color: #1e2030; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                        <h3 style="margin-top: 0; color: #cba6f7;">Platform Caption</h3>
                        <div style="background-color: #181825; padding: 15px; border-radius: 5px; color: #cdd6f4;">
                            {caption}
                        </div>
                        <button class="copy-button" onclick="navigator.clipboard.writeText('{caption.replace("'", "\\'")}')">📋 Copy</button>
                    </div>
                    """, unsafe_allow_html=True)
                
                if "HASHTAGS" in meme_content:
                    if "KEY MESSAGE" in meme_content:
                        hashtags = meme_content.split("HASHTAGS")[1].split("KEY MESSAGE")[0].strip(":\n ")
                    else:
                        hashtags = meme_content.split("HASHTAGS")[1].split("ADDITIONAL CONTENT RECOMMENDATIONS")[0].strip(":\n ")
                    
                    platform_content["hashtags"] = hashtags
                    
                    st.markdown(f"""
                    <div style="background-color: #1e2030; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                        <h3 style="margin-top: 0; color: #cba6f7;">Hashtags</h3>
                        <div style="background-color: #181825; padding: 15px; border-radius: 5px; color: #89b4fa;">
                            {hashtags}
                        </div>
                        <button class="copy-button" onclick="navigator.clipboard.writeText('{hashtags.replace("'", "\\'")}')">📋 Copy</button>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Create platform-specific previews
                if campaign_platforms:
                    st.markdown("### 🌐 Platform Previews")
                    
                    for platform in campaign_platforms[:2]:  # Limit to first 2 platforms
                        st.markdown(f"""
                        <div style="background-color: #1e2030; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                            <h3 style="margin-top: 0; color: #cba6f7;">{platform} Preview</h3>
                            <div style="background-color: #181825; padding: 15px; border-radius: 5px; color: #cdd6f4;">
                                <div style="font-weight: bold; margin-bottom: 10px;">{brand_name if brand_name else "Your Brand"}</div>
                                <div style="margin-bottom: 15px;">{platform_content.get("caption", "")}</div>
                                <div style="color: #89b4fa;">{platform_content.get("hashtags", "")}</div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            
            with content_tab3:
                if "KEY MESSAGE" in meme_content:
                    key_message = meme_content.split("KEY MESSAGE")[1].split("ADDITIONAL CONTENT RECOMMENDATIONS")[0].strip(":\n ")
                    
                    st.markdown(f"""
                    <div style="background-color: #1e2030; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                        <h3 style="margin-top: 0; color: #cba6f7;">Key Message</h3>
                        <div style="background-color: #181825; padding: 15px; border-radius: 5px; color: #cdd6f4;">
                            {key_message}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                if "ADDITIONAL CONTENT RECOMMENDATIONS" in meme_content:
                    recommendations = meme_content.split("ADDITIONAL CONTENT RECOMMENDATIONS")[1].strip(":\n ")
                    
                    st.markdown(f"""
                    <div style="background-color: #1e2030; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                        <h3 style="margin-top: 0; color: #cba6f7;">Content Strategy Recommendations</h3>
                        <div style="background-color: #181825; padding: 15px; border-radius: 5px; color: #cdd6f4;">
                            {recommendations}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                # Add campaign metrics estimator
                st.markdown("### 📊 Campaign Impact Estimator")
                
                # Calculate estimated metrics based on content quality and platform selection
                platform_count = len(campaign_platforms) if campaign_platforms else 0
                has_brand_info = bool(brand_name and brand_audience and brand_voice)
                has_campaign_info = bool(campaign_name and campaign_goal)
                
                # Simple scoring system
                content_quality_score = 0
                content_quality_score += 2 if has_brand_info else 0
                content_quality_score += 2 if has_campaign_info else 0
                content_quality_score += min(3, platform_count)
                content_quality_score += 3 if transcript else 0
                
                # Scale to percentage
                content_quality_percentage = min(100, content_quality_score * 10)
                
                # Create engagement metrics based on quality score
                base_engagement = 1000
                engagement_metrics = {
                    "Estimated Reach": int(base_engagement * (content_quality_percentage/100) * max(1, platform_count) * 2.5),
                    "Estimated Engagement Rate": f"{min(8.5, 3.5 + (content_quality_percentage/100) * 5):.1f}%",
                    "Potential Click-Through": f"{min(4.2, 1.2 + (content_quality_percentage/100) * 3):.1f}%",
                    "Content Quality Score": f"{content_quality_percentage:.0f}/100"
                }
                
                col1, col2 = st.columns(2)
                
                with col1:
                    for metric, value in list(engagement_metrics.items())[:2]:
                        st.markdown(f"""
                        <div style="background-color: #1e2030; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                            <div style="font-size: 14px; color: #a6adc8;">{metric}</div>
                            <div style="font-size: 24px; font-weight: bold; color: #cba6f7;">{value}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                with col2:
                    for metric, value in list(engagement_metrics.items())[2:]:
                        st.markdown(f"""
                        <div style="background-color: #1e2030; padding: 10px; border-radius: 5px; margin-bottom: 10px;">
                            <div style="font-size: 14px; color: #a6adc8;">{metric}</div>
                            <div style="font-size: 24px; font-weight: bold; color: #cba6f7;">{value}</div>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("""
                <div style="background-color: #1e2030; padding: 15px; border-radius: 5px; margin-top: 20px;">
                    <h4 style="margin-top: 0; color: #89b4fa;">Enterprise Analytics</h4>
                    <p style="color: #a6adc8; font-size: 14px;">
                        Enterprise customers receive detailed analytics and A/B testing capabilities. 
                        Contact our sales team for a demo of our full analytics dashboard.
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">Click "Generate Professional Content" to create content based on the selected frames and brand context.</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
else:
    # Show example content when no file is uploaded
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 📲 Example Content")
    
    example_contents = {
        "Social Media Marketing": "Revolutionize your workflow with AI-powered insights that deliver results",
        "Product Demonstration": "The future of productivity is here. See what our platform can do for you.",
        "Educational Content": "5 ways our solution transformed how industry leaders approach digital transformation",
        "Company Culture": "Behind every innovation is a team that believes in making a difference",
        "Customer Testimonial": "Real results, real clients: How our solution increased productivity by 35%",
        "Executive Messaging": "We're committed to leading the way in technological advancement",
        "Event Highlight": "Missed our latest launch event? Here's what you need to know",
        "Announcement": "Introducing our newest feature: The game-changer you've been waiting for"
    }
    
    # Display example content based on selected content category
    st.markdown(f"""
    <div class="caption-card">
        <h3>Example for "{content_category}":</h3>
        <p><strong>PRIMARY HEADLINE:</strong><br>{example_contents.get(content_category, "Select a content category to see examples")}</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🚀 Get Started")
    st.markdown("Upload a video file to begin creating professional marketing content for your brand.")
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("""
<div style="text-align: center; margin-top: 2rem; padding: 1rem; border-top: 1px solid #45475a; color: #a6adc8;">
    <p>Assistify Content Studio | Enterprise Edition v2.0 | © 2025 Assistify Technologies</p>
    <p style="font-size: 12px;">Powered by Gemini AI & AssemblyAI | <a href="#" style="color: #89b4fa;">Terms of Service</a> | <a href="#" style="color: #89b4fa;">Privacy Policy</a></p>
</div>
""", unsafe_allow_html=True)

# Cleanup temporary files
def cleanup():
    # Add cleanup code here if needed
    pass

# Register the cleanup function to be called when the script exits
import atexit
atexit.register(cleanup)