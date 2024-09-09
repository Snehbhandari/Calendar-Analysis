import datetime
import json
import csv
import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from dateutil import parser

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

def load_calendar_ids(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def calculate_duration(start, end):
    start_time = parser.parse(start)
    end_time = parser.parse(end)
    duration = end_time - start_time
    return str(duration)

def get_calendar_events(service, calendar_id):
    events = []
    page_token = None
    # Set timeMin to a past date to include past events
    time_min = (datetime.datetime.utcnow() - datetime.timedelta(days=365)).isoformat() + 'Z'

    while True:
        try:
            response = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min,
                singleEvents=True,
                orderBy='startTime',
                pageToken=page_token
            ).execute()

            events.extend(response.get('items', []))
            page_token = response.get('nextPageToken')

            if not page_token:
                break

        except HttpError as error:
            print(f'An error occurred: {error}')
            break

    return events

def load_existing_events(file_path):
    if not os.path.exists(file_path):
        return {}

    events = {}
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        if 'Event ID' not in reader.fieldnames:
            raise ValueError("CSV file does not have 'Event ID' header.")
        events = {row['Event ID']: row for row in reader}
    return events

def update_csv_with_events(file_path, events_to_add_or_update, events_to_remove):
    # Read existing events
    existing_events = load_existing_events(file_path)
    
    # Update or add events
    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Event ID', 'Start Date', 'Start Time', 'End Date', 'End Time', 'Duration', 'Event Title', 'Calendar Name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write updated or new events
        for event_id, event in events_to_add_or_update.items():
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            start_date, start_time = start.split('T')
            end_date, end_time = end.split('T')
            duration = calculate_duration(start, end)
            event_title = event.get('summary', 'No Title')  # Get event title, default to 'No Title' if not available

            writer.writerow({
                'Event ID': event_id,
                'Start Date': start_date,
                'Start Time': start_time,
                'End Date': end_date,
                'End Time': end_time,
                'Duration': duration,
                'Event Title': event_title,
                'Calendar Name': event.get('calendarName', 'Unknown')
            })

def main():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'calendar_auth.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)

    calendar_ids = load_calendar_ids('calendars.json')
    output_file = 'calendar_events.csv'
    
    # Load existing events from the CSV file
    existing_events = load_existing_events(output_file)

    # Dictionary to store events from Google Calendar
    current_events = {}

    for calendar_name, calendar_id in calendar_ids.items():
        print(f'Fetching events from {calendar_name} ({calendar_id})')
        events = get_calendar_events(service, calendar_id)
        if not events:
            print(f'No events found for {calendar_name}.')
        else:
            for event in events:
                event_id = event.get('id')
                if event_id:
                    current_events[event_id] = event
                    current_events[event_id]['calendarName'] = calendar_name
                    print(f'Added event {event_id} from {calendar_name}.')

    # Determine which events to add/update or remove
    events_to_add_or_update = {}
    events_to_remove = set(existing_events.keys())
    
    for event_id, event in current_events.items():
        if event_id in existing_events:
            # Compare and update event if modified
            existing_event = existing_events[event_id]
            if (event.get('start') != existing_event['Start Date'] + 'T' + existing_event['Start Time'] or
                event.get('end') != existing_event['End Date'] + 'T' + existing_event['End Time']):
                events_to_add_or_update[event_id] = event
                print(f'Updated event {event_id}.')
        else:
            events_to_add_or_update[event_id] = event
            print(f'New event {event_id} added.')
        
        # Remove from the set of events to remove
        events_to_remove.discard(event_id)

    # Remove events that are no longer in Google Calendar
    if events_to_remove:
        with open(output_file, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = [row for row in reader if row['Event ID'] not in events_to_remove]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        print(f'Removed {len(events_to_remove)} events from CSV.')

    # Update CSV with new or updated events
    update_csv_with_events(output_file, events_to_add_or_update, events_to_remove)
    print('CSV file updated.')

if __name__ == '__main__':
    main()