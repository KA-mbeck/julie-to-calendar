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
from flask_session import Session

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

# Configure session to use filesystem
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(os.getcwd(), 'flask_session')
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(minutes=60)

# Ensure session directory exists
os.makedirs(app.config['SESSION_FILE_DIR'], exist_ok=True)

Session(app)  # Initialize Flask-Session
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
if BASE_URL and not BASE_URL.startswith(('http://', 'https://')):
    BASE_URL = 'https://' + BASE_URL

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
        include_granted_scopes='true',
        prompt='consent'  # Force consent screen to get refresh token
    )
    session['state'] = state
    return jsonify({"auth_url": authorization_url})

@app.route('/oauth2callback')
def oauth2callback():
    try:
        app.logger.info("Starting OAuth callback...")
        flow = create_flow()
        flow.fetch_token(authorization_response=request.url)
        credentials = flow.credentials
        
        app.logger.info("Got credentials, checking refresh token...")
        if not hasattr(credentials, 'refresh_token'):
            app.logger.error("No refresh token in credentials!")
        else:
            app.logger.info("Refresh token present")
        
        # Store credentials in session instead of file
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        
        return 'Authorization successful! You can close this window and return to the application.'
    except Exception as e:
        app.logger.error(f"Error in OAuth callback: {str(e)}")
        import traceback
        app.logger.error(traceback.format_exc())
        return f'Authorization failed: {str(e)}'

def get_credentials():
    if 'credentials' not in session:
        return None
        
    creds_data = session['credentials']
    creds = Credentials(
        token=creds_data['token'],
        refresh_token=creds_data['refresh_token'],
        token_uri=creds_data['token_uri'],
        client_id=creds_data['client_id'],
        client_secret=creds_data['client_secret'],
        scopes=creds_data['scopes']
    )
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Update session with new token
            session['credentials']['token'] = creds.token
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
                
                event = {
                    "summary": summary,
                    "location": row['Meeting Room'].strip(),  # This will be empty string if no room
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
        app.logger.info("Getting credentials...")
        creds = get_credentials()
        if not creds:
            app.logger.error("No credentials found")
            return jsonify({"error": "Not authorized", "needs_auth": True}), 401
            
        app.logger.info("Building calendar service...")
        service = build('calendar', 'v3', credentials=creds)
        
        # Get list of calendars
        app.logger.info("Fetching calendar list...")
        calendar_list = service.calendarList().list().execute()
        app.logger.info(f"Found {len(calendar_list.get('items', []))} calendars")
        
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
        import traceback
        app.logger.error(traceback.format_exc())
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

@app.route('/download-calendar-csv', methods=['POST'])
def download_calendar_csv():
    try:
        data = request.get_json()
        selected_name = data.get('name')
        if not selected_name:
            return jsonify({'error': 'No name selected'}), 400

        events = parse_events_from_csv(selected_name)
        if not events:
            return jsonify({'error': 'No events found'}), 404

        # Create CSV content for Google Calendar
        csv_data = [['Subject', 'Start Date', 'Start Time', 'End Date', 'End Time', 'Description', 'Location']]
        
        for event in events:
            start = parser.parse(event['start']['dateTime'])
            end = parser.parse(event['end']['dateTime'])
            
            csv_data.append([
                event['summary'],
                start.strftime('%m/%d/%Y'),
                start.strftime('%I:%M %p'),
                end.strftime('%m/%d/%Y'),
                end.strftime('%I:%M %p'),
                event.get('description', ''),
                event.get('location', '')
            ])

        # Create a temporary file
        temp_csv = 'temp_calendar.csv'
        with open(temp_csv, 'w', newline='') as f:
            import csv
            writer = csv.writer(f)
            writer.writerows(csv_data)

        # Send the file
        response = send_from_directory(
            os.getcwd(),
            'temp_calendar.csv',
            as_attachment=True,
            download_name=f'{selected_name}_calendar_events.csv'
        )
        
        # Clean up after sending
        @response.call_on_close
        def cleanup():
            if os.path.exists(temp_csv):
                os.remove(temp_csv)
                
        return response

    except Exception as e:
        app.logger.error(f"Error generating CSV: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
