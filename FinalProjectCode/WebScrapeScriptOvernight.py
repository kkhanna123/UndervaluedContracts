### Imports
from IPython.core.display import display, HTML

import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup, Comment
import matplotlib.pyplot as plt
import sys
import os
import time
from unidecode import unidecode
import math


def scrapePlayerData(firstName, lastName):
    # Players with similar names have uncommon url structures
    curNumber = 1
    
    brunson_url = 'https://www.basketball-reference.com/players/'+lastName[0].lower()+'/'+lastName[:5].lower()+firstName[:2].lower()+'0'+str(curNumber)+'.html'
    
    # Use requests to retrieve data from a given URL
    brunson_response = requests.get(brunson_url)

    # Parse the whole HTML page using BeautifulSoup
    brunson_soup = BeautifulSoup(brunson_response.text, 'html.parser')

    # Title of the parsed page
    brunson_soup.title.string

    # Find instance of paragraph markers for height and weight scraping
    strongMarkersBrunson = brunson_soup.find_all('strong')

    # unidecode removes accents from letters (helpful for international players)
    while unidecode(strongMarkersBrunson[0].string.lower()) != unidecode(firstName.lower() + " " + lastName.lower()):
        brunson_url = 'https://www.basketball-reference.com/players/'+lastName[0].lower()+'/'+lastName[:5].lower()+firstName[:2].lower()+'0'+str(curNumber)+'.html'
    
        # Use requests to retrieve data from a given URL
        brunson_response = requests.get(brunson_url)
        
        # Basketball reference has maximum of 20 requests per minute, so this will ensure we stay below that limit
        time.sleep(5)

        # Parse the whole HTML page using BeautifulSoup
        brunson_soup = BeautifulSoup(brunson_response.text, 'html.parser')

        # Title of the parsed page
        brunson_soup.title.string

        # Find instance of paragraph markers for height and weight scraping
        strongMarkersBrunson = brunson_soup.find_all('strong')
        
        
        curNumber+=1
        
        if curNumber > 9:
            return {"success":False, "Height":float("NaN"), "Weight":float("NaN")}
            


    # Basketball reference has maximum of 20 requests per minute, so this will ensure we stay below that limit
    time.sleep(3)



    # Create a dictionary to cache all of the player statistics
    brunsonInfoDict = {}

    print(strongMarkersBrunson[0].string.lower()+" found successfully!")


    # Find instance of paragraph markers for height and weight scraping
    paraMarkersBrunson = brunson_soup.find_all('p')

    # Basketball reference has maximum of 20 requests per minute, so this will ensure we stay below that limit
    time.sleep(3)

    for sectionNum in range(len(paraMarkersBrunson)):

        # Find Height data in cm's (standard for all player pages)
        if paraMarkersBrunson[sectionNum].string != None and "tall" in paraMarkersBrunson[sectionNum].string:
            # All centimeter height values for NBA players are in triple digits so the format is constant
            print("Height: ", paraMarkersBrunson[sectionNum].string[-13:-9].strip())
            brunsonInfoDict['Height'] = int(paraMarkersBrunson[sectionNum].string[-13:-9].strip())
            
        
        # Find Weight data in lbs (standard for all player pages)
        if paraMarkersBrunson[sectionNum].string != None and "weigh" in paraMarkersBrunson[sectionNum].string:
            # All kg weight values for NBA players are in double or triple digits
            weight = paraMarkersBrunson[sectionNum].string[paraMarkersBrunson[sectionNum].string.index('(')+1:paraMarkersBrunson[sectionNum].string.index(')')-3].strip()
            if weight[0] == '(':
                weight = weight[1:]
            brunsonInfoDict['Weight'] = int(weight.strip())
            
            # Passes 3 digit and 2 digit weight case in kg (Walker Kessler and Jalen Brunson)
            print("Weight: ", weight)
            
    print(brunsonInfoDict)   # Height and Weight Successfully Scraped

    # Basketball reference has maximum of 20 requests per minute, so this will ensure we stay below that limit
    time.sleep(3)

    ### PER 100 POSSESSIONS DATA
    # Attempt to extract data from the tables (Per 100 possesions table first)
    brunson_soup_2 = BeautifulSoup(requests.get(brunson_url).content, "lxml")
    brunson_soup_3 = BeautifulSoup("\n".join(brunson_soup_2.find_all(text=Comment)), "lxml")

    try:
        brunson_per_poss_df = pd.read_html(str(brunson_soup_3.select_one("table#per_poss")))[0]
    except ValueError as ve:
    	return {"success":False, "Height":float("NaN"), "Weight":float("NaN")}
        

        

    brunson_per_poss_df = brunson_per_poss_df.loc[:list(brunson_per_poss_df['Season']).index('Career')-1].dropna(axis=1, how='all')

    #display(brunson_per_poss_df) # Prints the full dataframe correctly

    brunsonInfoDict['per_100poss_df'] = brunson_per_poss_df


    # Basketball reference has maximum of 20 requests per minute, so this will ensure we stay below that limit
    time.sleep(3)

    ### SHOOTING DATA
    # Attempt to extract data from the tables (Shooting table next)
    try:
    	brunson_shooting_df = pd.read_html(str(brunson_soup_3.select_one("table#shooting")))[0]
    except ValueError as ve:
    	return {"success":False, "Height":float("NaN"), "Weight":float("NaN")}

    brunson_shooting_df.columns = [x[0].strip() + " ("+x[1].strip()+")" if "named" not in x[0].strip() else x[1].strip() for x in brunson_shooting_df.columns]
    brunson_shooting_df = brunson_shooting_df.loc[:list(brunson_shooting_df['Season']).index('Career')-1].dropna(axis=1, how='all')

    #display(brunson_shooting_df) # Prints the full dataframe correctly
        
    brunsonInfoDict['shooting_df'] = brunson_shooting_df
    
    brunsonInfoDict['success'] = True
    
    print("Successfully Completed "+firstName+" "+lastName)
    
    return brunsonInfoDict
        
                


# Use this as player model because he has played the most years in the NBA, so we can fill with 0's
carterDict = scrapePlayerData('Vince','Carter')


# Import all drafted players since 1989
draftedPlayersDF = pd.read_csv("nbaplayersdraft.csv")

# Filter out players without 3 years of experience past 2004 (non contract extension eligible)
draftedPlayersDF = draftedPlayersDF[draftedPlayersDF['years_active']!=float("NaN")][draftedPlayersDF['years_active']>=3][draftedPlayersDF['year']>=1996][draftedPlayersDF['year']<=2020].reset_index()

draftedPlayersDF = draftedPlayersDF[['year', 'rank', 'overall_pick', 'team', 'player','years_active']].astype('object')

draftedPlayersDF['height'] = -1
draftedPlayersDF['weight'] = -1

for col in carterDict['shooting_df'].columns:
    for yearVal in range(len(carterDict['shooting_df'])):
            draftedPlayersDF[col + " year "+ str(yearVal)] = -1
    
for col in carterDict['per_100poss_df'].columns:
    for yearVal in range(len(carterDict['per_100poss_df'])):
            draftedPlayersDF[col + " year "+ str(yearVal)] = -1
    

print(draftedPlayersDF.columns)


failedPlayersList = []

indexTemp = 859

#draftedPlayersDF = draftedPlayersDF.copy()
# Merge data onto the Kaggle Dataset
draftedPlayersDF = pd.read_csv('PlayerData.csv')

# If the player can't scrape, add to list of failed player names to see if I could fix their issue easily
for name in draftedPlayersDF['player'][indexTemp:]:
    try:
        firstName,lastName = name.strip().split()[:2]
    except ValueError as ve:
        failedPlayersList.append(name.strip())
        print(name.strip())
        continue

    print(firstName, lastName)
    
    # Remove periods for initials and the like within names
    firstName = unidecode(''.join([x for x in firstName if x.isalpha()]).strip())
    lastName = unidecode(''.join([x for x in lastName if x.isalpha()]).strip())
    

    # Call the function to scrape   
    curPlayerDict = scrapePlayerData(firstName,lastName)

    if curPlayerDict['success'] == False:
        draftedPlayersDF.loc[indexTemp,'height'] = float('NaN')
        draftedPlayersDF.loc[indexTemp,'weight'] = float('NaN')
        print(firstName+' '+lastName+' failed scraping...')
        failedPlayersList.append(firstName+' '+lastName)
        continue


    draftedPlayersDF.loc[indexTemp,'height'] = curPlayerDict['Height']
    draftedPlayersDF.loc[indexTemp,'weight'] = curPlayerDict['Weight']

    for col in curPlayerDict['shooting_df'].columns:
        for yearVal in range(len(curPlayerDict['shooting_df'])):
            draftedPlayersDF.loc[indexTemp,col + " year "+ str(yearVal)] = curPlayerDict['shooting_df'].loc[yearVal,col]

    for col in curPlayerDict['per_100poss_df'].columns:
        for yearVal in range(len(curPlayerDict['per_100poss_df'])):
            draftedPlayersDF.loc[indexTemp, col + " year "+ str(yearVal)] = curPlayerDict['per_100poss_df'].loc[yearVal,col]
   
    
    indexTemp+=1

    # Cache progress every ten players
    if indexTemp%10 == 0:
        draftedPlayersDF.to_csv('PlayerData.csv')
        np.savetxt("failedPlayersList.csv",failedPlayersList, delimiter =", ", fmt ='% s')

draftedPlayersDF.to_csv('PlayerData.csv')

# Most failed players have either a dash, apostrophe, or Jr. / III / IV suffix, however this was overly time consuming to fix for 10 players in total

    