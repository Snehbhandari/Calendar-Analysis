#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb  7 01:35:13 2024

@author: snehbhandari
"""

# Make a functions that reads calendar csvs and outputs 
# a graph that outputs a dashboard (multiple graphs summarizing 
# the data).  

# libraries
import pandas as pd 
import numpy as np
import glob 

# input files 
files = glob.glob("Files\*.csv")
print("okay")
new_df = pd.DataFrame()
for file in files:
    df = pd.read_csv(file)
    new_df = pd.concat([new_df, df])

print(new_df)