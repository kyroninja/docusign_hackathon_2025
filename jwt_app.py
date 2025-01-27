from docusign_esign import ApiClient
from docusign_esign.client.api_exception import ApiException
from app.jwt_helpers import get_private_key
from app.jwt_config import DS_JWT

from flask import Flask, request, render_template, send_file, after_this_request, redirect, session, url_for

import sys
import os
from datetime import datetime

from app.sentiment import return_sentiment
from app.chatgpt import get_ai_response
from app.whatsapp import send_message
from app.helper_funcs import get_envelope_by_id, list_envelopes, download_document, list_documents_in_envelope, get_consent_url, get_token

from PyPDF2 import PdfReader


def get_envelopes(private_key, api_client):
    jwt_values = get_token(private_key, api_client)
    # Fetch envelope details
    try:
        envelope = list_envelopes(
            api_account_id=jwt_values["api_account_id"],
            access_token=jwt_values["access_token"],
            base_path=jwt_values["base_path"]
        )
        print("Envelope details retrieved successfully.")
        return envelope
    except ApiException:
        print("Failed to retrieve the envelope.")
        return None
    
def get_details(private_key, api_client, envelope_id):
    jwt_values = get_token(private_key, api_client)

    # Prompt the user for the envelope ID
    # envelope_id = input("Please enter the envelope ID: ")

    # Fetch envelope details
    try:
        envelope = get_envelope_by_id(
            api_account_id=jwt_values["api_account_id"],
            access_token=jwt_values["access_token"],
            base_path=jwt_values["base_path"],
            envelope_id=envelope_id
        )
        print("Envelope details retrieved successfully.")
        return envelope
    except ApiException:
        print("Failed to retrieve the envelope.")
        return None
    
def list_en_docs(private_key, api_client, envelope_id):
    jwt_values = get_token(private_key, api_client)

    # Prompt user for envelope ID
    # envelope_id = input("Please enter the envelope ID: ")

    # Fetch document metadata
    docs = list_documents_in_envelope(
        api_account_id=jwt_values["api_account_id"],
        access_token=jwt_values["access_token"],
        base_path=jwt_values["base_path"],
        envelope_id=envelope_id
    )
    return docs

def get_docs(private_key, api_client, envelope_id, document_id):
    jwt_values = get_token(private_key, api_client)

    # Prompt user for envelope ID
    # envelope_id = input("Please enter the envelope ID: ")
    
    temp_file = download_document(
        api_account_id=jwt_values["api_account_id"],
        access_token=jwt_values["access_token"],
        base_path=jwt_values["base_path"],
        envelope_id=envelope_id,
        document_id=document_id
    )
    return temp_file

_app = Flask(__name__)

@_app.route('/')
def home():
    """Serve the login page or the home page based on login status."""
    if session.get('logged_in'):
        return render_template('home.html')  # Home page template after login
    return render_template('login.html')  # Login page template
    #return render_template('home.html')  # Pass the list to the template

@_app.route('/get-envelopes', methods=['POST'])
def envelopes():
    items = get_envelopes(private_key, api_client)
    # You can render the same template with additional data or a new template
    return render_template('envelopes.html', details=items)

@_app.route('/query-envelope-details', methods=['POST'])
def details():
    envelope_id = request.form.get('envelope_id')  # Get the envelope ID from the form
    details = get_details(private_key, api_client, envelope_id)
    doc_details = list_en_docs(private_key, api_client, envelope_id)
    if doc_details:
        return render_template('details.html', details=details, doc_details=doc_details)
    else:
        return render_template('details.html', details=details, doc_details={})
    
# New route for downloading the document
@_app.route('/download/<envelope_id>/<document_id>', methods=['GET'])
def download(document_id, envelope_id):
    # Logic to fetch and download the document using the document_id
    document = get_docs(private_key, api_client, envelope_id=envelope_id, document_id=document_id)
    
    if document:
        @after_this_request
        def cleanup_file(response):
            try:
                if os.path.exists(document):
                    os.remove(document)
            except Exception as e:
                _app.logger.error(f"Error removing file {document}: {e}")
            return response

        # Serve the file for download
        return send_file(document, as_attachment=True, download_name=f"{os.path.split(document)[-1]}")
    else:
        return "Document not found", 404
    
@_app.route('/process_ai/<envelope_id>/<document_id>', methods=['GET'])
def process_ai(document_id, envelope_id):
    # Logic to fetch and download the document using the document_id
    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    document = get_docs(private_key, api_client, envelope_id=envelope_id, document_id=document_id)
    text = ""
    if document:
        @after_this_request
        def cleanup_file(response):
            try:
                if os.path.exists(document):
                    os.remove(document)
            except Exception as e:
                _app.logger.error(f"Error removing file {document}: {e}")
            return response

        # Function to extract text from a PDF file
        with open(document, 'rb') as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"

        # Split the text into lines
        lines = text.split('\n')
        
        sentiment, sentences = return_sentiment(lines)
        gpt = get_ai_response(sentences)
    
        info = {
            "Envelope ID": envelope_id,
            "Document ID": document_id,
            "Status": "Processed",
            "Timestamp": date,
            "Comments": gpt
        }
        # Send message via WhatsApp after 1min
        hour, minute = datetime.now().hour, datetime.now().minute + 1
        send_message("+27XXXXXXXXX", gpt, hour=hour, min=minute)
        return render_template('results.html', info=info)
    else:
        pass
        #return "Document not found", 404

@_app.route('/grant-consent')
def grant_consent():
    consent_url = get_consent_url()
    return redirect(consent_url)

# Route to process consent (Yes or No)
@_app.route('/process-consent', methods=['POST'])
def process_consent():
    consent_granted = request.form.get('consent_granted')
    
    if consent_granted == 'Yes':
        session['logged_in'] = True
        return redirect(url_for('home'))
    elif consent_granted == 'No':
        pass

    return redirect(url_for('home'))
    
if __name__ == '__main__':
    api_client = ApiClient()
    api_client.set_base_path(DS_JWT["authorization_server"])
    api_client.set_oauth_host_name(DS_JWT["authorization_server"])

    # Load private key
    private_key = get_private_key(DS_JWT["private_key_file"]).encode("ascii").decode("utf-8")
    
    # Set the secret key 
    _app.secret_key = "secret_key"

    try:
        pass
    except ApiException as err:
        body = err.body.decode('utf8')
        if "consent_required" in body:
            consent_url = get_consent_url()
            print("Open the following URL in your browser to grant consent to the application:")
            print(consent_url)
            consent_granted = input("Consent granted? Select one of the following: \n 1)Yes \n 2)No \n")
            if consent_granted == "1":
                pass
            else:
                sys.exit("Please grant consent")
        else:
            print(f"API Error: {err}")
            
    _app.run(debug=True)