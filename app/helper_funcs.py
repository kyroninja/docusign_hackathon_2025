from docusign_esign import ApiClient, EnvelopesApi
from docusign_esign.client.api_exception import ApiException
from datetime import datetime, timedelta
from app.jwt_helpers import get_jwt_token
from app.jwt_config import DS_JWT

SCOPES = ["signature", "impersonation"]

def get_consent_url():
    url_scopes = "+".join(SCOPES)
    redirect_uri = "https://developers.docusign.com/platform/auth/consent"
    consent_url = f"https://{DS_JWT['authorization_server']}/oauth/auth?response_type=code&" \
                  f"scope={url_scopes}&client_id={DS_JWT['ds_client_id']}&redirect_uri={redirect_uri}"
    return consent_url


def get_token(private_key, api_client):
    token_response = get_jwt_token(private_key, SCOPES, DS_JWT["authorization_server"], DS_JWT["ds_client_id"],
                                   DS_JWT["ds_impersonated_user_id"])
    access_token = token_response.access_token
    user_info = api_client.get_user_info(access_token)
    accounts = user_info.get_accounts()
    api_account_id = accounts[0].account_id
    base_path = accounts[0].base_uri + "/restapi"
    return {"access_token": access_token, "api_account_id": api_account_id, "base_path": base_path}

def get_envelope_by_id(api_account_id, access_token, base_path, envelope_id):
    """
    Retrieve envelope details based on the envelope ID.
    """
    envelop_details = {}
    try:
        # Set up API client
        api_client = ApiClient()
        api_client.host = base_path
        api_client.set_default_header("Authorization", f"Bearer {access_token}")

        # Use the Envelopes API to fetch the envelope
        envelopes_api = EnvelopesApi(api_client)
        envelope = envelopes_api.get_envelope(account_id=api_account_id, envelope_id=envelope_id)

        #print(f"Envelope ID: {envelope.envelope_id}")
        #print(f"Status: {envelope.status}")
        #print(f"Subject: {envelope.email_subject}")
        #print(f"Sender: {envelope._sender.email}")
        #print(f"Created: {envelope.created_date_time}")
        
        envelop_details[envelope.envelope_id] = {"Status": envelope.status, "Subject": envelope.email_subject, "Created_date_time": envelope.created_date_time, "Sender": envelope._sender.email}
        return envelop_details

    except ApiException as e:
        #print(f"Error retrieving envelope: {e}")
        raise
    
def list_documents_in_envelope(api_account_id, access_token, base_path, envelope_id):
    """
    List document IDs for an envelope.
    """
    document_list = {}
    try:
        api_client = ApiClient()
        api_client.host = base_path
        api_client.set_default_header("Authorization", f"Bearer {access_token}")

        # Get document metadata for the envelope
        envelopes_api = EnvelopesApi(api_client)
        docs_list = envelopes_api.list_documents(account_id=api_account_id, envelope_id=envelope_id)

        #print(f"Documents in Envelope {envelope_id}:")
        for doc in docs_list.envelope_documents:
            document_list[doc.document_id] = {"Name": doc.name, "Type": doc.type, "Document_ID": doc.document_id, "Envelope_ID": envelope_id}
            #print(f"- Document ID: {doc.document_id}, Name: {doc.name}, Type: {doc.type}")
        return document_list

    except ApiException as e:
        #print(f"Error retrieving documents: {e}")
        raise

def list_envelopes(api_account_id, access_token, base_path, days_back=30):
    """
    List all envelopes in the account created in the past `days_back` days.
    """
    envelop_details = {}
    try:
        # Set up the API client
        api_client = ApiClient()
        api_client.host = base_path
        api_client.set_default_header("Authorization", f"Bearer {access_token}")
        
        # Initialize the Envelopes API
        envelopes_api = EnvelopesApi(api_client)
        
        # Define the date range for envelopes to retrieve
        from_date = (datetime.now() - timedelta(days=days_back)).isoformat()

        # Call list_status_changes to get envelope details from inbox
        results = envelopes_api.list_status_changes(
            account_id=api_account_id,
            from_date=from_date,
            folder_ids="inbox"
        )

        # Print the envelope details
        #print(f"Envelopes created in the past {days_back} days:")
        for envelope in results.envelopes:
            #print(f"Envelope ID: {envelope.envelope_id}")
            #print(f"Status: {envelope.status}")
            #print(f"Subject: {envelope.email_subject}")
            #print(f"Created Date: {envelope.created_date_time}")
            #print(f"Sender: {envelope._sender.email}")
            #print("--------------------")
            envelop_details[envelope.envelope_id] = {"Status": envelope.status, "Subject": envelope.email_subject, "Created_date_time": envelope.created_date_time, "Sender": envelope._sender.email}
        
        return envelop_details

    except ApiException as e:
        #print(f"Error listing envelopes: {e}")
        raise
    
def download_document(api_account_id, access_token, base_path, envelope_id, document_id):
    """
    Download a document from an envelope and save it to a file.
    """
    try:
        api_client = ApiClient()
        api_client.host = base_path
        api_client.set_default_header("Authorization", f"Bearer {access_token}")

        # Fetch the document content
        envelopes_api = EnvelopesApi(api_client)
        document = envelopes_api.get_document(
            account_id=api_account_id,
            envelope_id=envelope_id,
            document_id=document_id
        )
        #print(f"Document {document_id} saved to {document}.")
        return document

    except ApiException as e:
        #print(f"Error downloading document: {e}")
        raise
