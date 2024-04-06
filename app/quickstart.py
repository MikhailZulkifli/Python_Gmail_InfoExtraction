import os.path
import json

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pprint import pprint

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_message_id_threadid(creds):
  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId="me", maxResults=500).execute()
    messages = results.get("messages", [])
    nextTokenPage = results.get("nextPageToken")

    while nextTokenPage:
      next_respone = service.users().message().list_next(previous_request=results, previous_response=results).execute()
      next_message = next_respone.get("message", [])
      messages.extend(next_message)
      nextTokenPage = next_message.get("nextTokenPage")

    data = []

    if not results:
      print("No messages found.")
      return
    data = [[message['id'], message['threadId']] for message in messages]
    return data

  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")

def format_data(message_id, creds):
  try:
    # Call the Gmail API
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().get(userId="me", id=message_id).execute()
    # pprint(results)
    nextTokenPage = results.get("nextPageToken")

    if not results:
      print("No messages found.")
      return
    
    data = {}

    data["id"] = results["id"]
    data["internalDate"] = results["internalDate"]
    data["labelIds"] = results["labelIds"]
    data["sourceEmail"] = str([key["value"] for key in results["payload"]["headers"] if key.get("name") == "Delivered-To"][0])
    data["headerDate"] = str([key["value"] for key in results["payload"]["headers"] if key.get("name") == "Date"][0])
    data["subject"] = str([key["value"] for key in results["payload"]["headers"] if key.get("name") == "Subject"][0])
    data["sender"] = str([key["value"] for key in results["payload"]["headers"] if key.get("name") == "From"][0])
    data["sizeEstimate"] = results["sizeEstimate"]
    data["snippet"] = results["snippet"]
    data["threadId"] = results["threadId"]

    return data
  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")

def main():
  """Shows basic usage of the Gmail API.
  Lists the user's Gmail labels.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  test_ids = get_message_id_threadid(creds)
  new_data = [format_data(id[0], creds) for id in test_ids]
  pprint(new_data[:5])

  # try:
  #   # Call the Gmail API
  #   service = build("gmail", "v1", credentials=creds)
  #   results = service.users().messages().get(userId="me", id="18de4f564df5224e").execute()
  #   test_headers = results["payload"]["headers"]
  #   pprint(results)
  #   for key in test_headers:
  #     if key.get("name") == "Delivered-To":
  #       new_value = key["value"]
  #       print(new_value)
  #   nextTokenPage = results.get("nextPageToken")

  #   if not results:
  #     print("No messages found.")
  #     return

  # except HttpError as error:
  #   # TODO(developer) - Handle errors from gmail API.
  #   print(f"An error occurred: {error}")

if __name__ == "__main__":
  main()