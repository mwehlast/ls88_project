#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 25 13:12:16 2018

@author: Morten
"""

import pandas as pd
import sqlite3 


# Create your connection.
cnx = sqlite3.connect('database.sqlite')

# Create data frame for each table
df_countries = pd.read_sql_query("SELECT * FROM Country", cnx)
df_matches = pd.read_sql_query("SELECT * FROM Match", cnx)
df_leagues = pd.read_sql_query("SELECT * FROM League", cnx)
df_teams = pd.read_sql_query("SELECT * FROM Team", cnx)
df_player = pd.read_sql_query("SELECT * FROM Player", cnx)

""""
# Attributes are large tables that are not used right now. Uncomment to load
df_player_attributes = pd.read_sql_query("SELECT * FROM Player_Attributes", cnx)
df_team_attributes = pd.read_sql_query("SELECT * from Team_Attributes",cnx)
"""

# Close connection
cnx.close()