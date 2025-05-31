# Meet Booking Assistant

Meet Booking Assistant is a chat-based tool that enables seamless scheduling and management of meetings via Google Calendar. It integrates a LangChain-powered chatbot backend with Socket.IO-based real-time communication and Google Calendar APIs.

---

## Project Structure
```
- app.py                   # Main entry point with SocketIO server
- calendar_integrations.py # Google Calendar utils
- langchain_chat.py        # LangChain-based Chat class
- requirements.txt         # Python dependencies
- .env.example             # Example environment config
```
---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/zeeshan1807/Meet-Booking-Assistant.git
cd Meet-Booking-Assistant
```

### 2. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create .env, copy the `.env.example` in it and add your OpenAI key:

### 5. Add Google Calendar Credentials
Download your `desktop_credentials.json` file from Google Cloud Console and place it in the root directory.

- Follow [Google Calendar API quickstart](https://developers.google.com/calendar/quickstart/python)
- Ensure OAuth consent screen and Calendar API are enabled

---

## Running the App

You can run the SocketIO app with:

```bash
python app.py
```

The app can now accept chat messages and booking requests from a frontend or Postman.

---

## Testing

### 1. Chat Engine
You can test `langchain_chat.py` in isolation to evaluate responses:
Run the `langchain_chat.py` and type whenever the console prompts `User:` 
while the chatbot's reply would be framed within `Agent:`
You can trail through the logs to see what's happening in the background

### 2. Calendar Integration
Test `calendar_integrations.py` directly to verify authentication and booking behavior.

---

## Architecture Overview

- **SocketIO API**: Receives chat prompts and returns structured responses in real-time.
- **LangChain Chat**: Interprets user input and generates calendar-related intents.
- **Google Calendar Integration**: Handles auth, availability checks, and event creation via `google-api-python-client`.

---

## Known Limitations

- **No Multi-user Support**: Currently assumes a single calendar/user context.
- **No Persistent Storage**: Chat history and events are limited to a session and not stored locally or in a DB.
- **No Email-based Notification**: Even when the meeting is scheduled and calendar is blocked, two limitations in place -
1. Users are not prompted to provided their personal information like name, email, contact etc.
2. Attendees are not informed via email (requires Google Workspace subscription)
- **Single Timezone**: Prompted to handle all the interactions in a pre-defined timezone (IST)

---

## Tools & Tech

- Python 3.11(preferred) or above
- LangChain
- OpenAI GPT
- Google Calendar API
- Flask-SocketIO

---

## Author

Developed by [Zeeshan](https://github.com/zeeshan1807)

---