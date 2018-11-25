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

# Get matches data without players, odds etc.

col_get = ['id', 'country_id', 'league_id', 'season', 'stage', 'date', 'match_api_id',
           'home_team_api_id', 'away_team_api_id', 'home_team_goal', 'away_team_goal']

df_matches_small = df_matches.loc[:, col_get] #Slice to smaller dataframe

#Get country code and slice
country = 'England'
count_id = df_countries.loc[df_countries['name'] == 'England'].iloc[0]['id']

#Reslice smaller dataframe to get desired league
df = df_matches_small.loc[df_matches_small['country_id'] == count_id].copy() #CHANGE NAME

#Get match ids
match_ids = df['id'].unique()

#%% 

#Create dictionary for team names
team_name_dict = {}

for team_id in df_teams['team_api_id']: #Extract every Series update and extract its value as string
    team_name_dict[team_id] = df_teams.loc[df_teams.team_api_id == team_id, 'team_long_name'].\
                                values[0]
                                
#Update team names in dataframe
df['home_team_name'] = 0
df['away_team_name'] = 0

for match in df['id']: #Extract home team and away team ids and look up in dictionary
    home_team_id = df.loc[df.id == match, 'home_team_api_id'].values[0]
    away_team_id = df.loc[df.id == match, 'away_team_api_id'].values[0]
    
    df.loc[df.id == match, 'home_team_name'] = team_name_dict[home_team_id]
    df.loc[df.id == match, 'away_team_name'] = team_name_dict[away_team_id]

#%%
#Read in detailed cards information
df_cards = pd.read_csv('card_detail.csv')
df_cards_small = df_cards.loc[:,['card_type', 'match_id', 'team']].dropna() #Drop NA values
df_cards_small = df_cards_small[df_cards_small['match_id'].isin(match_ids)] #Index to desired league
df_cards_small.team = df_cards_small.team.astype(int) #Convert team to int in order to merge


# Add columns to dataframe
df['home_y1'] = 0
df['home_y2'] = 0
df['home_r'] = 0
df['away_y1'] = 0
df['away_y2'] = 0
df['away_r'] = 0


# Count cards and add to original datafame
for match in df_cards_small['match_id'].unique():
    df_temp = df_cards_small[df_cards_small['match_id'] == match] #Create temp dataframe
    teams = df_cards_small[df_cards_small['match_id'] == match]['team'].unique()
    
    for team in teams: #Count first yellow, second yellow and reds for teams
        team_y1 = df_temp[(df_temp.card_type == 'y') & (df_temp.team == team)].count()[0]
        team_y2 = df_temp[(df_temp.card_type == 'y2') & (df_temp.team == team)].count()[0]
        team_r = df_temp[(df_temp.card_type == 'r') & (df_temp.team == team)].count()[0]
        
        if not df.loc[(df.id == match) & (df.home_team_api_id == team)].empty:
            df.loc[(df.id == match) & (df.home_team_api_id == team), 'home_y1'] = team_y1
            df.loc[(df.id == match) & (df.home_team_api_id == team), 'home_y2'] = team_y2
            df.loc[(df.id == match) & (df.home_team_api_id == team), 'home_r'] = team_r
        else:
            df.loc[(df.id == match) & (df.away_team_api_id == team), 'away_y1'] = team_y1
            df.loc[(df.id == match) & (df.away_team_api_id == team), 'away_y2'] = team_y2
            df.loc[(df.id == match) & (df.away_team_api_id == team), 'away_r'] = team_r
    
    

#%%
#Read in detailed fouls information
df_fouls = pd.read_csv('foulcommit_detail.csv')
df_fouls_small = df_fouls.loc[:,['match_id', 'team']] #Subset
df_fouls_small = df_fouls_small[df_fouls_small['match_id'].isin(match_ids)] #Index to desired league
df_fouls_small = df_fouls_small[df_fouls_small.team.notnull()]
df_fouls_small.team = df_fouls_small.team.astype(int) #Convert team to int in order to merge


# Add columns to dataframe
df['home_fouls'] = 0
df['away_fouls'] = 0

for match in df_fouls_small['match_id'].unique():
    df_temp = df_fouls_small[df_fouls_small['match_id'] == match]
    teams = df_fouls_small[df_fouls_small['match_id'] == match]['team'].unique()
    
    for team in teams: #Add foul counts to home and away
        team_fouls = df_temp[(df_temp.match_id == match) & (df_temp.team == team)].count()[0]
        
        if not df.loc[(df.id == match) & (df.home_team_api_id == team)].empty:
            df.loc[(df.id == match) & (df.home_team_api_id == team), 'home_fouls'] = team_fouls
        
        else:
            df.loc[(df.id == match) & (df.away_team_api_id == team), 'away_fouls'] = team_fouls



#%%
#Read in detailed possession information
df_possession = pd.read_csv('possession_detail.csv')         
df_possession_small = df_possession.loc[:, ['match_id', 'homepos']]

#Add columns to dataframe
#Possession will be calculated as average for the entire game
df['home_poss'] = 0
df['away_poss'] = 0

for match in df_possession_small['match_id'].unique():
    home_avg_poss = df_possession_small[df_possession_small['match_id'] == match].mean()
    df.loc[df.id == match, 'home_poss'] = home_avg_poss['homepos']
    df.loc[df.id == match, 'away_poss'] = 100 - home_avg_poss['homepos']
    

#%%
#Read in detailed shoton information
df_shoton = pd.read_csv('shoton_detail.csv')
df_shoton = df_shoton.loc[df_shoton.match_id.isin(match_ids)]
df_shoton = df_shoton.loc[df_shoton.team.notnull()]
df_shoton.team = df_shoton.team.astype(int)

#Add columns to df
df['home_shoton'] = 0
df['away_shoton'] = 0


for match in df_shoton['match_id'].unique():
    grouped_by_team = df_shoton.loc[df_shoton.match_id == match].groupby(by = 'team') #Group events by team
    count_per_team = grouped_by_team.agg({'n' : ['count']}) #Aggregate by count of events
    
    for team in count_per_team.index:
        team_shoton = count_per_team.iloc[count_per_team.index == team].values[0][0]
        
        if not df.loc[(df.id == match) & (df.home_team_api_id == team)].empty:
            df.loc[df.id == match, 'home_shoton'] = team_shoton

        else:
            df.loc[df.id == match, 'away_shoton'] = team_shoton
    

#%%
#Read in detailed shotoff information
df_shotoff = pd.read_csv('shotoff_detail.csv')
df_shotoff = df_shotoff.loc[df_shotoff.match_id.isin(match_ids)]
df_shotoff = df_shotoff.loc[df_shotoff.team.notnull()]
df_shotoff.team = df_shotoff.team.astype(int) 

#Add columns to df
df['home_shotoff'] = 0
df['away_shotoff'] = 0


for match in df_shotoff['match_id'].unique():
    grouped_by_team = df_shotoff.loc[df_shotoff.match_id == match].groupby(by = 'team') #Group events by team
    count_per_team = grouped_by_team.agg({'n' : ['count']}) #Aggregate by count of events
    
    for team in count_per_team.index:
        team_shotoff = count_per_team.iloc[count_per_team.index == team].values[0][0]
        
        if not df.loc[(df.id == match) & (df.home_team_api_id == team)].empty:
            df.loc[df.id == match, 'home_shotoff'] = team_shotoff

        else:
            df.loc[df.id == match, 'away_shotoff'] = team_shotoff          

#%%
#Read in detailed corner information
df_corner = pd.read_csv('corner_detail.csv')
df_corner = df_corner.loc[df_corner.match_id.isin(match_ids)]
df_corner = df_corner.loc[df_corner.team.notnull()]
df_corner.team = df_corner.team.astype(int) 


#Add columns to df
df['home_corners'] = 0
df['away_corners'] = 0


for match in df_corner['match_id'].unique():
    grouped_by_team = df_corner.loc[df_corner.match_id == match].groupby(by = 'team') #Group events by team
    count_per_team = grouped_by_team.agg({'n' : ['count']}) #Aggregate by count of events
    
    for team in count_per_team.index:
        team_corners = count_per_team.iloc[count_per_team.index == team].values[0][0]
        
        if not df.loc[(df.id == match) & (df.home_team_api_id == team)].empty:
            df.loc[df.id == match, 'home_corners'] = team_corners

        else:
            df.loc[df.id == match, 'away_corners'] = team_corners
            
#%%Add points
            
df['home_points'] = 0
df['away_points'] = 0

for match in df['id']:
    
    if df.loc[df.id == match].home_team_goal.values[0] == df.loc[df.id == match].away_team_goal.values[0]:
        df.loc[df.id == match, 'home_points'] = 1
        df.loc[df.id == match, 'away_points'] = 1
    
    elif df.loc[df.id == match].home_team_goal.values[0] > df.loc[df.id == match].away_team_goal.values[0]:
        df.loc[df.id == match, 'home_points'] = 3
        df.loc[df.id == match, 'away_points'] = 0
    
    else:
        df.loc[df.id == match, 'home_points'] = 0
        df.loc[df.id == match, 'away_points'] = 3

#%%
#Save to CSV
df.to_csv('dataframe.csv')