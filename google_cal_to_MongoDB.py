#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep  9 14:42:22 2024

@author: snehbhandari
"""

import datetime
import os
import json
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.credentials import Credentials
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
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

def sync_calendar_to_mongodb(service, calendar_ids, collection):
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

    # Compare with MongoDB and perform updates
    db_event_ids = set(event['Event ID'] for event in collection.find({}, {'Event ID': 1}))
    current_event_ids = set(current_events.keys())

    # Update existing events and insert new events
    for event_id, event in current_events.items():
        start = event['start'].get('dateTime', event['start'].get('date'))
        end = event['end'].get('dateTime', event['end'].get('date'))
        start_date, start_time = start.split('T')
        end_date, end_time = end.split('T')
        duration = calculate_duration(start, end)
        event_title = event.get('summary', 'No Title')

        row = {
            'Event ID': event_id,
            'Start Date': start_date,
            'Start Time': start_time,
            'End Date': end_date,
            'End Time': end_time,
            'Duration': duration,
            'Event Title': event_title,
            'Calendar Name': event.get('calendarName', 'Unknown')
        }

        existing_event = collection.find_one({'Event ID': event_id})
        if existing_event:
            # Update if the event has changed
            if any(existing_event.get(field) != row.get(field) for field in row):
                collection.update_one({'Event ID': event_id}, {'$set': row})
                print(f"Updated: {row}")
            else:
                print(f"No update needed: Event ID {event_id}")
        else:
            # Insert new event
            collection.insert_one(row)
            print(f"Inserted: {row}")

    # Delete events from MongoDB that are no longer in the calendar
    events_to_delete = db_event_ids - current_event_ids
    for event_id in events_to_delete:
        collection.delete_one({'Event ID': event_id})
        print(f"Deleted: Event ID {event_id} as it is no longer in the calendar")

def main():
    # Google Calendar API authentication
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

    # MongoDB connection setup
    uri = "mongodb+srv://snehbhandari:4umZ36RvSekIk1Xu@calendardata.erd5u.mongodb.net/?retryWrites=true&w=majority&appName=CalendarData"
    client = MongoClient(uri, server_api=ServerApi('1'))

    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
        return

    # Specify the collection to work with
    collection = client['CalendarData']['activity']

    # Load calendar IDs from a JSON file (replace with your method of loading calendar IDs)
    calendar_ids = load_calendar_ids('calendars.json')

    # Sync calendar events to MongoDB
    sync_calendar_to_mongodb(service, calendar_ids, collection)

if __name__ == '__main__':
    main()
