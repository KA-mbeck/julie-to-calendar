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

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(16))
CORS(app)

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

def parse_events(text):
    events = []
    lines = text.strip().split('\n')
    current_date = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for date headers (e.g., "February 17:")
        date_match = re.match(r'(?i)(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?::|$)', line)
        if date_match:
            month = date_match.group(1)
            day = int(date_match.group(2))
            # Use current year since it's not specified
            current_date = datetime.datetime.strptime(f"{month} {day} 2025", "%B %d %Y")
            continue
            
        # Look for time patterns
        time_pattern = r'(\d{1,2}):(\d{2})\s*(AM|PM|am|pm)'
        times = re.findall(time_pattern, line)
        
        if times and current_date:
            # Extract event description (remove the time parts)
            description = re.split(time_pattern, line)[0].strip()
            if description.endswith('(') or description.endswith('-'):
                description = description[:-1].strip()
            
            # Parse start time
            start_hour = int(times[0][0])
            start_minute = int(times[0][1])
            start_meridian = times[0][2].upper()
            
            if start_meridian == 'PM' and start_hour != 12:
                start_hour += 12
            elif start_meridian == 'AM' and start_hour == 12:
                start_hour = 0
                
            start_time = current_date.replace(hour=start_hour, minute=start_minute)
            
            # Parse end time if available
            end_time = None
            if len(times) > 1:
                end_hour = int(times[1][0])
                end_minute = int(times[1][1])
                end_meridian = times[1][2].upper()
                
                if end_meridian == 'PM' and end_hour != 12:
                    end_hour += 12
                elif end_meridian == 'AM' and end_hour == 12:
                    end_hour = 0
                    
                end_time = current_date.replace(hour=end_hour, minute=end_minute)
            else:
                # Default to 1 hour duration if no end time specified
                end_time = start_time + datetime.timedelta(hours=1)
            
            event = {
                "summary": description,
                "start": {
                    "dateTime": start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "timeZone": "America/New_York"
                },
                "end": {
                    "dateTime": end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "timeZone": "America/New_York"
                }
            }
            events.append(event)
    
    return events

@app.route('/parse', methods=['POST'])
def parse_text():
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400
    
    events = parse_events(data['text'])
    return jsonify(events)

@app.route('/create-events', methods=['POST'])
def create_calendar_events():
    try:
        creds = get_credentials()
        if not creds:
            return jsonify({"error": "Not authorized", "needs_auth": True}), 401
            
        service = build('calendar', 'v3', credentials=creds)
        
        data = request.json
        if not data or 'events' not in data:
            return jsonify({"error": "No events provided"}), 400
        
        created_events = []
        for event in data['events']:
            created_event = service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            created_events.append(created_event)
        
        return jsonify({"message": f"Created {len(created_events)} events", "events": created_events})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
