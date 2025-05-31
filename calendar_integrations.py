import os.path
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from datetime import datetime, timedelta
import dateparser
import uuid

CALENDAR_ID = 'primary'
TIMEZONE = 'Asia/Kolkata'
SCOPES = ['https://www.googleapis.com/auth/calendar']
token_path = 'token.json'
creds_path = 'desktop_credentials.json'

def authenticate_google_calendar():
    """
    Authenticates the user with Google Calendar API using OAuth 2.0.
    """
    creds = None

    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)        

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
            creds = flow.run_local_server(port=0)
        
        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())

    return creds

creds = authenticate_google_calendar()
service = build('calendar', 'v3', credentials=creds)

def get_available_slots_on_calender(start, end, duration_minutes=30):
    """
    Finds available time slots between the given start and end datetime range 
    by checking free/busy information from the user's Google Calendar.
    """

    available_slots = []

    body = {
        "timeMin": start.isoformat(),
        "timeMax": end.isoformat(),
        "timeZone": TIMEZONE,
        "items": [{"id": CALENDAR_ID}]
    }

    eventsResult = service.freebusy().query(body=body).execute()
    busy_times = eventsResult['calendars'][CALENDAR_ID]['busy']
    busy_slots = [
    (datetime.fromisoformat(busy["start"]), datetime.fromisoformat(busy["end"])) 
    for busy in busy_times
    ]
    
    start_dt = start
    end_dt = end

    while start_dt + timedelta(minutes=duration_minutes) <= end_dt:
        slot_end = start_dt + timedelta(minutes=duration_minutes)
        overlap = any(
            start_dt < busy[1] and
            slot_end > busy[0]
            for busy in busy_slots
        )
        if not overlap:
            available_slots.append((start_dt, slot_end))
        start_dt += timedelta(minutes=30)

    return available_slots, busy_slots

def book_slot_on_calendar(slot):
    """
    Books a 30-minute meeting on the user's Google Calendar at the specified time.
    The input time is parsed using ISO String or natural language string (e.g., "2025-05-30T09:00:00+05:30" or "20th May 05:30 PM IST").
    If parsing succeeds, a calendar event is created with a Google Meet link.
    """

    try:
        start_dt = datetime.fromisoformat(slot)
    except ValueError:
        # Fallback to natural language parsing
        start_dt = dateparser.parse(slot, settings={'TIMEZONE': 'Asia/Kolkata', 'RETURN_AS_TIMEZONE_AWARE': True})
    
    if not start_dt:
        return "Could not understand the time slot. Please use a format like '2025-05-30T09:00:00+05:30'."

    end_dt = start_dt + timedelta(minutes=30)

    event = {
        'summary': 'Meeting with Zeeshan',
        'description': 'Auto-scheduled via assistant.',
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        "conferenceData": {
        "createRequest": {
            "requestId": str(uuid.uuid4()),
            "conferenceSolutionKey": { "type": "hangoutsMeet" },
        },
        }
    }

    event = service.events().insert(
        calendarId=CALENDAR_ID,
        body=event,
        conferenceDataVersion=1
    ).execute()

    meet_link = event.get('hangoutLink', 'No meet link generated')
    return f"Slot booked for {start_dt.strftime('%d %b %I:%M %p')}. Meet link: {meet_link}"

from zoneinfo import ZoneInfo

if __name__ == "__main__":
    tz = ZoneInfo("Asia/Kolkata")
    start = datetime.now(tz)
    end = start + timedelta(hours=2)
    print("Start:",start) #Timezone aware start ISO
    print("End:",end) #Timezone aware end ISO
    slots, busy = get_available_slots_on_calender(start, end)
    print("Available slots:", slots) #start,end datetime range for available slots 
    print("Busy slots:", busy) #start,end datetime range for busy slots 
    
    def format_slot_range(slots):
            """
            Augments the slots in natural language for forwarding it to LLM
            """
            return "\n".join(
                f"{start.strftime('%d %b %I:%M %p')} to {end.strftime('%I:%M %p')}" for start, end in slots
            ) or "None"

    free_str = format_slot_range(slots)
    busy_str = format_slot_range(busy)
    print(f"BUSY SLOTS:\n{busy_str}\n\nFREE SLOTS:\n{free_str}") #Augmented info
    test_slot = (datetime.now(tz) + timedelta(hours=1)).replace(microsecond=0).isoformat() #Creates a slot for testing
    print(book_slot_on_calendar(test_slot)) #Books the test slot on calendar