import streamlit as st
import pandas as pd
import base64
import random
import time
import datetime
import psycopg2
import os
import socket
import platform
import geocoder
import secrets
import io
import plotly.express as px
from geopy.geocoders import Nominatim

# PDF PARSER FIXED IMPORTS
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import TextConverter

from pyresparser import ResumeParser
from streamlit_tags import st_tags
from PIL import Image

from Courses import (
    ds_course,
    web_course,
    android_course,
    ios_course,
    uiux_course,
    resume_videos,
    interview_videos,
)

# NLTK SAFE DOWNLOAD
import nltk

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

# SPACY MODEL DOWNLOAD
import spacy

try:
    spacy.load("en_core_web_sm")
except:
    os.system("python -m spacy download en_core_web_sm")


# =========================
# MYSQL DATABASE CONNECTION
# =========================

# FOR STREAMLIT CLOUD
# USE STREAMLIT SECRETS

# Create .streamlit/secrets.toml locally
# DO NOT PUSH secrets.toml TO GITHUB

# Example:
# [mysql]
# host = "your-host"
# user = "your-user"
# password = "your-password"
# database = "cv"


connection = None
cursor = None

try:
    connection = pymysql.connect(
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"]
    )

    cursor = connection.cursor()

except Exception as e:
    st.warning("Database not connected")
    st.error(e)


# =========================
# PAGE CONFIG
# =========================

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon='./Logo/recommend.png',
)


# =========================
# CSV DOWNLOAD
# =========================

def get_csv_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


# =========================
# PDF READER
# =========================

def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()

    converter = TextConverter(
        resource_manager,
        fake_file_handle,
        laparams=LAParams()
    )

    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    with open(file, 'rb') as fh:
        for page in PDFPage.get_pages(
            fh,
            caching=True,
            check_extractable=True
        ):
            page_interpreter.process_page(page)

        text = fake_file_handle.getvalue()

    converter.close()
    fake_file_handle.close()

    return text


# =========================
# SHOW PDF
# =========================

def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')

    pdf_display = f'''
        <iframe
            src="data:application/pdf;base64,{base64_pdf}"
            width="700"
            height="1000"
            type="application/pdf">
        </iframe>
    '''

    st.markdown(pdf_display, unsafe_allow_html=True)


# =========================
# COURSE RECOMMENDER
# =========================

def course_recommender(course_list):
    st.subheader("Courses & Certificates Recommendations")

    c = 0
    rec_course = []

    no_of_reco = st.slider(
        'Choose Number of Course Recommendations:',
        1,
        10,
        5
    )

    random.shuffle(course_list)

    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)

        if c == no_of_reco:
            break

    return rec_course


# =========================
# MAIN APP
# =========================

def run():

    img = Image.open('./Logo/RESUM.png')
    st.image(img)

    st.title("AI Resume Analyzer")

    st.markdown(
        "Upload your resume and get smart recommendations"
    )

    pdf_file = st.file_uploader(
        "Choose your Resume",
        type=["pdf"]
    )

    if pdf_file is not None:

        with st.spinner('Analyzing Resume...'):
            time.sleep(2)

        save_image_path = './Uploaded_Resumes/' + pdf_file.name

        with open(save_image_path, "wb") as f:
            f.write(pdf_file.getbuffer())

        show_pdf(save_image_path)

        # PARSE RESUME
        resume_data = ResumeParser(save_image_path).get_extracted_data()

        if resume_data:

            st.success("Resume Parsed Successfully")

            st.subheader("Basic Information")

            st.write("Name:", resume_data.get('name'))
            st.write("Email:", resume_data.get('email'))
            st.write("Mobile:", resume_data.get('mobile_number'))
            st.write("Skills:", resume_data.get('skills'))

            # OPTIONAL MYSQL SAVE
            if connection:
                try:
                    sql = """
                    INSERT INTO user_data(name, email)
                    VALUES(%s, %s)
                    """

                    cursor.execute(
                        sql,
                        (
                            resume_data.get('name'),
                            resume_data.get('email')
                        )
                    )

                    connection.commit()

                except Exception as e:
                    st.error(e)

            st.balloons()

        else:
            st.error("Resume Parsing Failed")


run()
