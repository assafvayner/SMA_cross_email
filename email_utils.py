import pickle
import os.path
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import base64

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
CREDENTIALS = 'client_secret.json' 

def load_credentials_build_service():
    """
    this function loads the credentials either from a present token.pickle file
    if credentials have been loaded in the past or from a credentials JSON which
    requests authorization in the browser on this machine
    """
    
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    #if there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        # if creds and creds.expired and creds.refresh_token:
        #    creds.refresh(Request())
        #else:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS, SCOPES)
        creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)
    return service

def create_email(sender, reciever, subject, text_content, img_filename):
    """
    all params should be strings
    sender is the account this email is sent from
    reciever is the account this email is sent to
    subject is the subject line of the email
    content is the text content of the email
    img_filename is the name of the png to be attached

    this funtion creates a base64 encoding of the whole email and stores it
    in a JSON formatted to be able to be sent by the Gmail API
    """
    email_content = MIMEMultipart()
    
    email_content['to'] = reciever
    email_content['from'] = sender
    email_content['subject'] = subject

    email_content.attach(MIMEText(text_content))
    if img_filename is not None:
        email_content.attach(gen_MIMEImage(img_filename))

    b64_bytes = base64.urlsafe_b64encode(email_content.as_bytes())
    b64_str = b64_bytes.decode()
    return {'raw':b64_str}

def gen_MIMEImage(file_name):
    """
    generates MIMEImage object for given 'png' file to be attached to the email
    if given file does not have png extension will raise a value error
    """
    if not file_name.endswith('.png'):
        raise ValueError('file name given to gen_MIMEImage is not a \'.png\' file.')

    with open(file_name, 'rb') as f:
        img_raw = f.read()
    img_mime = MIMEImage(img_raw, 'png')
    img_mime.add_header('Content-Disposition', 'attachment', filename=file_name)
    return img_mime

def send_email(service, content, sender):
    """
    service should be the resulting object from building the build('gmail') command
    with valid version and credentials, the content is a JSON containing a tag 'raw'
    with the value being a base 64 encoded email (return value of create_email)
    sender should be the email this email is sent from, which will have to correspond
    to the credentials used to build service
    """
    try:
        message = (service.users().messages().send(userId=sender, body=message).execute())
        # returns status of sending the email
        return message
    except (HttpError, error) as e:
        print('An error occurred: %s' % e)
