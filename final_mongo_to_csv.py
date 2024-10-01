#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Sep 30 20:18:56 2024

@author: snehbhandari
"""

import csv
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os
from datetime import datetime

# Set the working directory to where your script is located
os.chdir('/Users/snehbhandari/Documents/Project/Calendar Automation Project')

# MongoDB connection URI
uri = "mongodb+srv://snehbhandari:4umZ36RvSekIk1Xu@calendardata.erd5u.mongodb.net/?retryWrites=true&w=majority&appName=CalendarData"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# Cluster and collection names
cls_name = 'CalendarData'
col_name = "activity"

# Specify the collection you want to work with
collection = client[cls_name][col_name]

# Find all documents in the collection
documents = collection.find()

# Save CSV file to this location 
save_in_directory = os.path.join("/Users/snehbhandari/Documents/Project/Calendar Automation Project/", "data")

# Check if the directory exists and create it if it doesn't
os.makedirs(save_in_directory, exist_ok=True)

# Final path for the CSV file
csv_file = 'activity_data.csv'
csv_file_path = os.path.join(save_in_directory, csv_file)

# Check if the file already exists and generate a new filename if it does
if os.path.exists(csv_file_path):
    base_name, extension = os.path.splitext(csv_file_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file_path = f"{base_name}_{timestamp}{extension}"

# Fetch all fieldnames dynamically from the documents
fieldnames = set()
for document in documents:
    fieldnames.update(document.keys())

# Reset the cursor since it is exhausted after iterating
documents = collection.find()

# Write to CSV file
try:
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(fieldnames))
        writer.writeheader()
        for document in documents:
            writer.writerow(document)

    print(f"Data has been saved to {csv_file_path}")
except Exception as e:
    print(f"Error writing to CSV file: {e}")
