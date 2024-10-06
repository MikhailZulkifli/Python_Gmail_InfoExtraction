import re
import psycopg2
import os.path
import json

from psycopg2 import OperationalError
from psycopg2.extras import execute_batch
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pprint import pprint

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_messageid_threadid(creds):
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
    data["sender"] = str([(match.group(1) if (match := re.search(r'<(.*?)>', key["value"])) else key["value"]) for key in results["payload"]["headers"] if key.get("name") == "From"][0])
    data["sizeEstimate"] = results["sizeEstimate"]
    data["snippet"] = results["snippet"]
    data["threadId"] = results["threadId"]

    return data
  except HttpError as error:
    # TODO(developer) - Handle errors from gmail API.
    print(f"An error occurred: {error}")

def check_connection():
  try:
    conn = psycopg2.connect(
      database = "dev_g_db04", 
      user = "superuser_dev", 
      host = "192.168.68.53", 
      password = "Capo36296", 
      port = 5432
      )
    if conn.status == psycopg2.extensions.STATUS_READY:
      print("Connection is successful!")

    cur = conn.cursor()
    cur.execute("SELECT 1")  # Simple query to check the connection
    cur.fetchone()  # Fetch result to ensure the query works
    print("Database query executed successfully!")

    # Close cursor and connection
    cur.close()

    conn.close()
  except OperationalError as e:
    print(f"Connection failed: {e}")

def insert_emails(conn, data):
  insert_query = """
  INSERT INTO dev_g_s04_gmail.tdev04_gmail_raw (
    date,
    id,
    "internalDate",
    "labelIds",
    "sourceEmail",
    "headerDate",
    subject,
    sender,
    "sizeEstimate",
    snippet,
    "threadId"
  ) VALUES (
    NOW(),
    %(id)s,
    %(internalDate)s,
    %(labelIds)s,
    %(sourceEmail)s,
    %(headerDate)s,
    %(subject)s,
    %(sender)s,
    %(sizeEstimate)s,
    %(snippet)s,
    %(threadId)s
  );
  """

  with conn.cursor() as cur:
    execute_batch(cur, insert_query, data)
    conn.commit()


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

  test_ids = get_messageid_threadid(creds)
  # To get total message
  print("\nTotal message: ", len(test_ids))

  # To test 5 message only
  # test_ids_5 = test_ids[0:2]
  # print(test_ids_5)

  new_data = [format_data(id[0], creds) for id in test_ids]
  # pprint(new_data)

  # postgresql db connection
  check_connection()

  try:
    conn = psycopg2.connect(
      database = "dev_g_db04", 
      user = "superuser_dev", 
      host = "192.168.68.53", 
      password = "Capo36296", 
      port = 5432
    )
    
    # Insert data into the emails table and automatically add the current timestamp
    insert_emails(conn, new_data)
    
    print("Data inserted successfully with current timestamps!")
    
  except psycopg2.DatabaseError as error:
    print(f"Error: {error}")
    
  finally:
    if conn:
      conn.close()


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