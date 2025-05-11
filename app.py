from flask import Flask, request, render_template, send_from_directory, redirect, url_for
import os
import json
from analyzer import analyze_apk, save_json, create_pdf

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
RESULT_FOLDER = 'results'

# Configure upload and result folders
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

@app.route('/')
def landing():
    # Landing page
    return render_template('landing.html')

@app.route('/upload-page')
def upload_page():
    # Upload form page
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('apkfile')
    if not file or file.filename == '':
        return "No APK file selected.", 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    # Analyze the APK
    result = analyze_apk(file_path)

    # Save JSON and PDF
    json_name = 'analysis_output.json'
    pdf_name = 'analysis_summary.pdf'

    save_json(result, os.path.join(app.config['RESULT_FOLDER'], json_name))
    create_pdf(result, os.path.join(app.config['RESULT_FOLDER'], pdf_name))

    return render_template('index.html', json_file=json_name, pdf_file=pdf_name)

@app.route('/download/<filename>')
def download(filename):
    return send_from_directory(app.config['RESULT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
