# Event to Google Calendar

This application converts text-based event descriptions into Google Calendar events. It provides a simple interface to input event text and automatically creates corresponding calendar events.

## Setup

1. Create a Google Cloud Project and enable the Google Calendar API
2. Download the OAuth 2.0 Client credentials and save them as `credentials.json` in the project root
3. Build and run the Docker container:

```bash
docker build -t event-calendar .
docker run -p 5000:5000 -v ${PWD}:/app event-calendar
```

4. On first run, you'll need to authenticate with Google Calendar. Follow the URL provided in the console.

## Usage

1. Input your event text in the format:
```
Event description at 10:00am
Another event at 2:30pm
```

2. The application will parse the text and create calendar events with appropriate times.

## API Endpoints

- POST `/parse`: Parse text into event JSON
- POST `/create-events`: Create events in Google Calendar

## Requirements

- Docker
- Google Calendar API credentials
- Python 3.9+
