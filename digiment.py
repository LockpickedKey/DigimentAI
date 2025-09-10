import streamlit as st
from openai import OpenAI
import numpy as np
import cv2
from PIL import Image, ImageFilter
import io
import base64
import fitz
import pytesseract
import os

pytesseract.pytesseract.tesseract_cmd = "/usr/local/bin/tesseract"
with open("logo.svg", "r") as f:
    svg = f.read()
svg = f'<div style="width: 40px; height: 40px;">{svg}</div>'
st.set_page_config(page_title="DigiMent Hub", page_icon="🚀")
st.markdown(
    f"""
    <div style='display: flex; align-items: center; gap: 10px; 
                padding: 10px 20px; border-radius: 8px;'>
        {svg}
        <h1 style='margin: 0; color: white;'>Digiment Hub</h1>
    </div>
    """,
    unsafe_allow_html=True
)
st.caption("Warp to quiz to test yourself if you understand the uploaded image or PDF!")
page = st.selectbox("Warp to...", ["-- Select --", "Quiz", "Podcast", "Pomodoro"])
if page == "Podcast":
    st.switch_page("pages/podcastifier.py")
elif page == "Quiz":
    st.switch_page("pages/quiz.py")
elif page == "Pomodoro":
    st.switch_page("pages/pomodigi.py")
if 'raw_text' not in st.session_state:
    st.session_state.raw_text = ""
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# Image 
def remove_shadows(pil_image):
    img = np.array(pil_image.convert("L"))
    dilated = cv2.dilate(img, np.ones((7,7), np.uint8))
    bg = cv2.medianBlur(dilated, 21)
    diff = 255 - cv2.absdiff(img, bg)
    norm = cv2.normalize(diff, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    return Image.fromarray(norm)

def preprocess_image(pil_image):
    img = pil_image.convert("L")
    img = img.filter(ImageFilter.MedianFilter(size=3))
    return img

def encode_image(pil_image):
    buffered = io.BytesIO()
    pil_image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode()

# OCR 
def extract_text_from_image_gpt(image_file):
    try:
        original_image = Image.open(image_file)
        processed_image = remove_shadows(original_image)
        processed_image = preprocess_image(processed_image)
        base64_img = encode_image(processed_image)
        response = client.chat.completions.create(model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Transcribe all handwritten text EXACTLY as written. Preserve line breaks with '\\n'. Include all symbols and formatting."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                    ]
                }
            ],
            temperature=0.0,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Error extracting text (GPT): {str(e)}")
        return ""

# Tesseract
def extract_text_from_image_tesseract(image_file):
    try:
        original_image = Image.open(image_file)
        processed_image = remove_shadows(original_image)
        processed_image = preprocess_image(processed_image)
        text = pytesseract.image_to_string(processed_image)
        return text
    except Exception as e:
        st.error(f"Tesseract OCR Error: {str(e)}")
        return ""

# Summarization (GPT)
def summarize_image_text(text_chunk, summary_length):
    length_instruction = {
        "Short": "Summarize the following text with a quarter the length of the whole content.",
        "Medium": "Summarize the following text with half the length of the whole content.",
        "Long": "Summarize the following text in as much detail as possible while remaining still clear."
    }[summary_length]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes extracted text from images."},
            {"role": "user", "content": f"""{length_instruction}:
Also do the following:
1. Clean up any OCR errors in the extracted text
2. Summarize the content in a few sentences
3. Provide a short title that captures the main idea

Text:
{text_chunk}

Return your response in this format:
Title: <title here>
<summary here>
"""}
        ]
    )
    return response.choices[0].message.content

# PDF
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = ""
    for i in doc:
        text += i.get_text()
    return text

def split_text_into_chunks(text, chunk_size=3000, overlap=100):
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

def summarize_text_chunk(text_chunk, summary_length):
    length_instruction = {
        "Short": "Summarize the following text with a quarter the length of the whole content.",
        "Medium": "Summarize the following text with half the length of the whole content.",
        "Long": "Summarize the following text in as much detail as possible while remaining still clear."
    }[summary_length]

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes big chunks of text and creates short, clear titles for them."},
            {"role": "user", "content": f"""{length_instruction}:
Also do the following:
1. Summarize the following text in a few sentences.
2. Then, provide a short title that captures the main idea.

Text:
{text_chunk}

Return your response in this format:
Title: <title here>
<summary here>
"""}
        ]
    )
    return response.choices[0].message.content

# App
file_type = st.radio("Select file type:", ["Image (JPEG)", "PDF"])
if file_type == "Image (JPEG)":
    photo = st.file_uploader("Upload a .jpeg file", type=["jpeg"])
    ocr_engine = st.radio("Choose OCR engine", ["GPT-4o (slower and more accurate)", "Tesseract (faster and less accurate)"], index=0)

    if photo:
        summary_length = st.selectbox(
            "Choose summary length:",
            ["Short", "Medium", "Long"],
            index=1
        )

        if st.button("Process Image"):
            with st.spinner("Extracting and summarizing text..."):
                if ocr_engine == "GPT-4o (online)":
                    st.session_state.extracted_text = extract_text_from_image_gpt(photo)
                else:
                    st.session_state.extracted_text = extract_text_from_image_tesseract(photo)

                if st.session_state.extracted_text:
                    summary = summarize_image_text(st.session_state.extracted_text, summary_length)
                    st.session_state.raw_text = summary
                    st.success("Image processed!")
                    st.subheader("Extracted Text:")
                    st.text_area("Raw extracted text", st.session_state.extracted_text, height=200)
                    
                    st.subheader("Summary:")
                    st.write(summary)
                else:
                    st.error("Could not extract text from image")

else: 
    uploaded_file = st.file_uploader("Upload a PDF file", type="pdf")

    if uploaded_file is not None:
        summary_length = st.selectbox(
            "Choose summary length:",
            ["Short", "Medium", "Long"],
            index=1
        )

        if st.button("Summarize PDF"):
            with st.spinner("Extracting text and summarizing..."):
                st.session_state.extracted_text = extract_text_from_pdf(uploaded_file)
                if st.session_state.extracted_text:
                    text_chunks = split_text_into_chunks(st.session_state.extracted_text)
                    full_summary = ""
                    for i, chunk in enumerate(text_chunks):
                        st.write(f"Summarizing chunk {i+1}...")
                        chunk_summary = summarize_text_chunk(chunk, summary_length)
                        full_summary += chunk_summary + "\n\n"

                    st.session_state.raw_text = full_summary
                    
                    st.subheader("Extracted Text:")
                    st.text_area("Raw extracted text", st.session_state.extracted_text, height=200)
                    
                    st.subheader("Summary:")
                    st.write(full_summary)
                else:
                    st.error("Could not extract text from PDF.")

st.markdown("""
<style>
html, body {
    background-color: #0e0e1e;
    color: #e0e0ff;
}
[data-testid="stFileUploader"] {
    background-color: #1b1b3c;
    border: 2px dashed #66ccff;
    padding: 20px;
    border-radius: 12px;
    transition: all 0.3s ease;
}
[data-testid="stFileUploader"]:hover {
    border-color: #99ddff;
    background-color: #23234d;
}
</style>
""", unsafe_allow_html=True)
