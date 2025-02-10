# CSV to Google Calendar

This application converts CSV-based event schedules into Google Calendar events. It provides a simple interface to select staff members and create their events in a chosen Google Calendar.

## Features

- Parse CSV files containing staff schedules
- Select specific staff members to view their events
- Choose an existing Google Calendar or create a new one
- Batch create events with room information
- OAuth2 authentication with Google Calendar

## Setup

1. Create a Google Cloud Project and enable the Google Calendar API
2. Download the OAuth 2.0 Client credentials and save them as `credentials.json` in the project root
3. Set up environment variables:
   ```
   FLASK_SECRET_KEY=your_secret_key
   GOOGLE_CREDENTIALS=base64_encoded_credentials
   RAILWAY_STATIC_URL=your_railway_url (in production)
   ```

4. Build and run the Docker container:
   ```bash
   docker build -t julie-calendar .
   docker run -p 3000:5000 -p 3001:8080 -v ${PWD}:/app julie-calendar
   ```

5. On first run, you'll need to authenticate with Google Calendar

## Usage

1. Access the application at `http://localhost:3000`
2. Select a staff member from the dropdown
3. Click "Show Events" to view their schedule
4. Choose an existing calendar or create a new one
5. Click "Create Calendar Events" to add the events

## CSV Format

The CSV file should have the following columns:
- Date
- Start Time
- End Time
- Session/Title/Event Name
- Meeting Room
- Staff member columns (one per person)

## API Endpoints

- GET `/get-names`: Get list of staff names from CSV
- POST `/parse`: Parse events for a selected person
- GET `/get-calendars`: Get list of available Google Calendars
- POST `/create-calendar`: Create a new Google Calendar
- POST `/create-events`: Create events in a specified calendar

## Requirements

- Docker
- Google Calendar API credentials
- Python 3.9+
- CSV file with staff schedules

## Deployment

This application is designed to be deployed on Railway.app. Required environment variables should be set in the Railway project settings.
