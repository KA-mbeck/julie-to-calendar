from flask import Flask, request, jsonify, send_from_directory, redirect, session, url_for
from flask_cors import CORS
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import json
import datetime
import re
from dateutil import parser
import secrets
import base64
import pandas as pd
import logging

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))
CORS(app)

# Configure logging
import sys
app.logger.addHandler(logging.StreamHandler(sys.stdout))
app.logger.setLevel(logging.DEBUG)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'  # Only for development

# Get the OAuth credentials from environment variable
GOOGLE_CREDENTIALS = os.environ.get('GOOGLE_CREDENTIALS')
if GOOGLE_CREDENTIALS:
    credentials_dict = json.loads(base64.b64decode(GOOGLE_CREDENTIALS))
    with open('credentials.json', 'w') as f:
        json.dump(credentials_dict, f)

# Get the base URL from environment or default to localhost
BASE_URL = os.environ.get('RAILWAY_STATIC_URL', 'http://localhost:5000')

def create_flow():
    return Flow.from_client_secrets_file(
        'credentials.json',
        scopes=SCOPES,
        redirect_uri=f'{BASE_URL}/oauth2callback'
    )

@app.route('/authorize')
def authorize():
    flow = create_flow()
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )
    session['state'] = state
    return jsonify({"auth_url": authorization_url})

@app.route('/oauth2callback')
def oauth2callback():
    flow = create_flow()
    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    
    with open('token.json', 'w') as token:
        token.write(credentials.to_json())
    
    return 'Authorization successful! You can close this window and return to the application.'

def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        else:
            return None
    
    return creds

@app.route('/get-names', methods=['GET'])
def get_names():
    try:
        print("Reading CSV file for names")
        df = pd.read_csv('Staff_Schedule.csv', dtype=str)
        print(f"CSV columns: {df.columns.tolist()}")
        
        # Get all column names
        all_columns = df.columns.tolist()
        
        # Exclude non-name columns and empty columns
        exclude_columns = ['Date', 'Start Time', 'End Time', 'Session/Title/Event Name', 'Meeting Room', '']
        names = [col for col in all_columns if col not in exclude_columns and col.strip()]
        
        print(f"Found {len(names)} names: {names}")
        return jsonify(names)
    except Exception as e:
        print(f"Error getting names: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify([])

def parse_events_from_csv(selected_name):
    events = []
    try:
        print(f"Reading CSV file for {selected_name}")
        # Read the CSV file
        df = pd.read_csv('Staff_Schedule.csv', dtype=str)
        print(f"CSV columns: {df.columns.tolist()}")
        
        # Clean up the data
        df = df.fillna('')
        df[selected_name] = df[selected_name].fillna('').str.strip()
        
        # Filter rows where the selected name has any non-empty value
        print(f"Checking column {selected_name} for values")
        person_events = df[df[selected_name].str.len() > 0].copy()
        print(f"Found {len(person_events)} events for {selected_name}")
        
        if len(person_events) == 0:
            print(f"Sample of values in {selected_name} column: {df[selected_name].head()}")
            return []
        
        # Convert date strings to datetime
        person_events['Date'] = pd.to_datetime(person_events['Date'], format='%m/%d')
        # Set the year to current year
        current_year = 2025
        person_events['Date'] = person_events['Date'].apply(lambda x: x.replace(year=current_year) if pd.notna(x) else None)
        
        for _, row in person_events.iterrows():
            try:
                print(f"Processing event: {row['Session/Title/Event Name']}")
                # Skip rows without a start time or event name
                if not row['Start Time'] or not row['Session/Title/Event Name']:
                    print(f"Skipping event due to missing start time or event name")
                    continue
                    
                # Parse the date
                event_date = row['Date']
                if pd.isna(event_date):
                    print(f"Skipping event due to invalid date")
                    continue
                
                # Parse start time
                start_time = pd.to_datetime(row['Start Time'], format='%I:%M %p', errors='coerce')
                if pd.isna(start_time):
                    start_time = pd.to_datetime(row['Start Time'], format='%H:%M', errors='coerce')
                if pd.isna(start_time):
                    start_time = pd.to_datetime(row['Start Time'], format='%I:%M%p', errors='coerce')
                if pd.isna(start_time):
                    print(f"Could not parse start time: {row['Start Time']}")
                    continue
                    
                # Parse end time (if available)
                end_time = None
                if row['End Time'].strip():
                    end_time = pd.to_datetime(row['End Time'], format='%I:%M %p', errors='coerce')
                    if pd.isna(end_time):
                        end_time = pd.to_datetime(row['End Time'], format='%H:%M', errors='coerce')
                    if pd.isna(end_time):
                        end_time = pd.to_datetime(row['End Time'], format='%I:%M%p', errors='coerce')
                
                # If no end time specified, make it 1 hour after start
                if pd.isna(end_time):
                    end_time = start_time + pd.Timedelta(hours=1)
                
                # Combine date with times
                start_datetime = pd.Timestamp.combine(event_date.date(), start_time.time())
                end_datetime = pd.Timestamp.combine(event_date.date(), end_time.time())
                
                # Create event summary with room if available
                summary = row['Session/Title/Event Name']
                if row['Meeting Room'].strip():
                    summary += f" (Room: {row['Meeting Room']})"
                
                event = {
                    "summary": summary,
                    "start": {
                        "dateTime": start_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                        "timeZone": "America/New_York"
                    },
                    "end": {
                        "dateTime": end_datetime.strftime("%Y-%m-%dT%H:%M:%S"),
                        "timeZone": "America/New_York"
                    }
                }
                events.append(event)
                print(f"Added event: {summary}")
            except Exception as e:
                print(f"Error processing event: {str(e)}")
                continue
            
    except Exception as e:
        print(f"Error parsing CSV: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return []
    
    print(f"Total events found: {len(events)}")
    return events

@app.route('/parse', methods=['POST'])
def parse_text():
    data = request.json
    if not data or 'selected_name' not in data:
        return jsonify({"error": "No name selected"}), 400
    
    events = parse_events_from_csv(data['selected_name'])
    return jsonify(events)

@app.route('/get-calendars')
def get_calendars():
    try:
        creds = get_credentials()
        if not creds:
            return jsonify({"error": "Not authorized", "needs_auth": True}), 401
            
        service = build('calendar', 'v3', credentials=creds)
        
        # Get list of calendars
        calendar_list = service.calendarList().list().execute()
        calendars = []
        for calendar_list_entry in calendar_list['items']:
            calendars.append({
                'id': calendar_list_entry['id'],
                'summary': calendar_list_entry['summary'],
                'primary': calendar_list_entry.get('primary', False)
            })
        
        return jsonify(calendars)
    except Exception as e:
        app.logger.error(f"Error getting calendars: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/create-calendar', methods=['POST'])
def create_calendar():
    try:
        creds = get_credentials()
        if not creds:
            return jsonify({"error": "Not authorized", "needs_auth": True}), 401
            
        service = build('calendar', 'v3', credentials=creds)
        
        data = request.json
        if not data or 'name' not in data:
            return jsonify({"error": "Calendar name is required"}), 400
            
        calendar = {
            'summary': data['name'],
            'timeZone': 'America/New_York'
        }
        
        created_calendar = service.calendars().insert(body=calendar).execute()
        return jsonify({
            'id': created_calendar['id'],
            'summary': created_calendar['summary']
        })
    except Exception as e:
        app.logger.error(f"Error creating calendar: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/create-events', methods=['POST'])
def create_calendar_events():
    try:
        creds = get_credentials()
        if not creds:
            return jsonify({"error": "Not authorized", "needs_auth": True}), 401
            
        service = build('calendar', 'v3', credentials=creds)
        
        data = request.json
        if not data or 'events' not in data or 'calendarId' not in data:
            return jsonify({"error": "Events and calendar ID are required"}), 400
        
        created_events = []
        for event in data['events']:
            created_event = service.events().insert(
                calendarId=data['calendarId'],
                body=event
            ).execute()
            created_events.append(created_event)
        
        return jsonify({"message": f"Created {len(created_events)} events", "events": created_events})
    
    except Exception as e:
        app.logger.error(f"Error creating events: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
