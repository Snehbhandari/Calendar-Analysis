#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Sep  1 14:54:44 2024

@author: snehbhandari
"""

import csv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

uri = "mongodb+srv://snehbhandari:4umZ36RvSekIk1Xu@calendardata.erd5u.mongodb.net/?retryWrites=true&w=majority&appName=CalendarData"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e) 

# Specify the collection you want to work with
collection = client['CalendarData']['events']

header = ['Event ID', 'Start Date', 'Start Time', 'End Date', 'End Time', 'Duration', 'Event Title', 'Calendar Name']

csv_event_ids = set()

with open('calendar_events.csv', 'r') as csvFile:
    reader = csv.DictReader(csvFile)
    
    for each in reader:
        event_id = each.get('Event ID')
        csv_event_ids.add(event_id)
        
        # Check if an entry with the same Event ID exists in the collection
        existing_event = collection.find_one({'Event ID': event_id})
        
        row = {field: each.get(field) for field in header}
        
        if existing_event:
            # Check if the existing document differs from the new data
            if any(existing_event.get(field) != row.get(field) for field in header):
                # Update the document with the new data
                collection.update_one({'Event ID': event_id}, {'$set': row})
                print(f"Updated: {row}")
            else:
                print(f"No update needed: Event ID {event_id}")
        else:
            # Insert the new event if it does not exist
            collection.insert_one(row)
            print(f"Inserted: {row}")

# Find and delete any events in the database that are not in the CSV
db_event_ids = set(event['Event ID'] for event in collection.find({}, {'Event ID': 1}))

events_to_delete = db_event_ids - csv_event_ids

for event_id in events_to_delete:
    collection.delete_one({'Event ID': event_id})
    print(f"Deleted: Event ID {event_id} as it is no longer in the CSV")
