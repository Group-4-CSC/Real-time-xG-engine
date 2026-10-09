from pathlib import Path
import pandas as pd
import json

#The data set has data for multiple competitions we filtered the data based on only Champions League games and found the season id for each season. With the season id we were able to find all final matches of each season. After cleaning the data and removing unecessary fields we convereted the dataframe into a CSV to import to MongoDB.

#Step One: Read the data files
#Create the file path to the competitions.json folder 
competitions_file = (
    Path(__file__).resolve().parent
    / "Raw_Statsbomb_Data"
    / "competitions.json"
)
competitions_df = pd.read_json(competitions_file)

print(competitions_df.head())
print(competitions_df.columns)
print(len(competitions_df))

#Step Two: Filter/clean data

champions_league_competitions_df = competitions_df[competitions_df['competition_name'] == 'Champions League']

print(len(champions_league_competitions_df))

#Seasons to exclude: 
#season_id: 76, Year: 99/00, 
#season_id: 277, Year: 72/73,
#season_id: 71, Year: 71/72, 
#season_id: 276, Year: 70/71

champions_league_competitions_df = champions_league_competitions_df[~champions_league_competitions_df['season_id'].isin([76,277,71,276])]

print(champions_league_competitions_df.head())
print(len(champions_league_competitions_df))

print(champions_league_competitions_df['season_id'])

#Step Three: Read and clean up match data
match_df = []

#Iterate through match data directory, read each JSON file and concatonate into one dataframe
#Combining 14 different files and outputting one file
match_directory = Path("Raw_Statsbomb_Data/CL_Final_Match_Data")
for file_path in match_directory.glob("*.json"):
    
    with open (file_path, "r" ) as file:
        match_data = json.load(file)
        
    match_file = pd.json_normalize(match_data)
    match_df.append(match_file)

match_df = pd.concat(match_df, ignore_index = True)

# print(match_df)

# Remove multiple columns at once
match_df = match_df.drop(columns=['kick_off','match_status', 'match_status_360', 'last_updated', 'last_updated_360',
       'match_week', 'competition.competition_id', 'competition.country_name',
       'competition.competition_name', 'season.season_id',
       'season.season_name', 'home_team.home_team_id','home_team.home_team_gender',
       'home_team.home_team_group', 'home_team.country.id','home_team.managers',
       'away_team.away_team_id', 'away_team.away_team_gender', 'away_team.away_team_group',
       'away_team.country.id', 'away_team.managers',
       'metadata.data_version', 'competition_stage.id',
       'competition_stage.name', 'stadium.id', 'stadium.country.id', 'stadium.country.name', 'referee.id', 'referee.country.id', 'referee.country.name','metadata.shot_fidelity_version', 'metadata.xy_fidelity_version'])


match_df = match_df.rename(columns={'match_id': 'MatchID', 
                        'match_date': 'HomeTeam',
                        'home_score': 'AwayTeam',
                        'away_score': 'MatchDate',
                        'home_team.home_team_name': 'HomeScore',
                        'home_team.country.name': 'AwayScore',
                        'away_team.away_team_name': 'StadiumName',
                        'away_team.country.name': 'HomeTeamCountry',
                        'stadium.name': 'AwayTeamCountry',
                        'referee.name': 'RefereeName'
                        })


match_df.to_csv('Clean_Statsbomb_Data/matchCollection.csv', index = False)

print(match_df.columns)
print(len(match_df))