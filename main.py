from __future__ import print_function

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().messages().list(userId='me', maxResults=500).execute()
        messages = results.get('messages', [])
        
        email_list = []

        if not messages:
            print('No messages found.')
            return

        # count = 5
        print('Extracting message...')
        for message in messages:
            # if count == 0: For testing purpose, to test on several message, uncomment and set count
            #     print('Message stop')
            #     print(email_list)
            #     return
            msg = service.users().messages().get(userId='me', id=message.get('id')).execute()
            headers = msg["payload"]["headers"]
            # from_row = [header_list.get("value") for header_list in headers if header_list.get("name") == 'From']
            # print(from_row)
            # count -= 1
            for header in headers:
                if header.get("name") == 'From':
                    from_email = header.get("value")
                    email = from_email[from_email.find('<')+1:from_email.find('>')]
                    email_domain = email[email.find('@')+1:]
                    email_list.append(email_domain)
            
        print(email_list)
        print('Email_list length:', len(email_list))
        print()

        dist_email_list = [*set(email_list)]
        print(dist_email_list)
        print('dist_email_list length:', len(dist_email_list))

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()