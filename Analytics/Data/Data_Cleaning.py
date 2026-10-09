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

#print(match_df)

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

print(match_df)

match_df = match_df.rename(columns={'match_id': 'MatchID', 
                        'match_date': 'MatchDate',
                        'home_score': 'HomeScore',
                        'away_score': 'AwayScore',
                        'home_team.home_team_name': 'HomeTeamName',
                        'home_team.country.name': 'HomeTeamCountry',
                        'away_team.away_team_name': 'AwayTeamName',
                        'away_team.country.name': 'AwayTeamCountry',
                        'stadium.name': 'StadiumName',
                        'referee.name': 'RefereeName'
                        })


match_df.to_csv('Clean_Statsbomb_Data/matchCollection.csv', index = False)

print(match_df.columns)
print(len(match_df))

print((match_df["MatchID"]))

match_id_lookup = {
    "2003-04":"3752619",
    "2004-05":"2302764",
    "2006-07":"3750200",
    "2008-09":"3750201",
    "2009-10":"18235",
    "2010-11":"18236",
    "2011-12":"18237",
    "2012-13":"18240",
    "2013-14":"18241",
    "2014-15":"18242",
    "2015-16":"18243",
    "2016-17":"18244",
    "2017-18":"18245",
    "2018-19":"22912",
}


shot_df = []

shot_directory = Path("Raw_Statsbomb_Data/CL_Final_Shot_Data")
for file_path in shot_directory.glob("*.json"):

    with open(file_path, "r") as file:
        shot_data = json.load(file)

    file_name = Path(file_path).stem

    shot_file = pd.json_normalize(shot_data)
    shot_file["MatchID"] = match_id_lookup[file_name]
    shot_df.append(shot_file)

shot_df = pd.concat(shot_df, ignore_index = True)

# print(shot_df)

shot_df = shot_df[shot_df['type.name'] == 'Shot']




shot_df = shot_df.drop( columns = ["index", 
                                     "possession", "duration", "type.id", "possession_team.id", "play_pattern.id", 
                                     "play_pattern.name", "team.id", "tactics.formation", "tactics.lineup", "related_events", "player.id", 
                                     "position.id", "pass.recipient.id", 
                                     "pass.height.id", "pass.height.name",  "pass.type.id",  
                                     "pass.body_part.id",  "carry.end_location", "pass.outcome.id",  
                                     "ball_receipt.outcome.id",  "under_pressure", "counterpress", "dribble.outcome.id", 
                                     "off_camera", "foul_won.defensive", "pass.switch", "dribble.overrun", "duel.type.id", 
                                     "duel.type.name", "duel.outcome.id", "duel.outcome.name",  "pass.assisted_shot_id", 
                                     "shot.key_pass_id", "shot.type.id",  "shot.outcome.id", 
                                     "shot.technique.id",  "shot.body_part.id", 
                                     "shot.freeze_frame", "goalkeeper.position.id",  "goalkeeper.technique.id", 
                                     "goalkeeper.outcome.id", "goalkeeper.outcome.name", "goalkeeper.type.id", 
                                     "goalkeeper.body_part.id",  "interception.outcome.id", 
                                     "interception.outcome.name", "pass.backheel", "foul_committed.advantage", "foul_won.advantage", 
                                     "foul_committed.card.id", "foul_committed.card.name", "foul_committed.type.id", "foul_committed.type.name",                                        "foul_committed.offensive", 
                                     "block.deflection",  "pass.deflected", "clearance.aerial_won", 
                                     "ball_recovery.recovery_failure", "pass.cut_back", "bad_behaviour.card.id", "bad_behaviour.card.name", 
                                     "substitution.outcome.id", "substitution.outcome.name", "substitution.replacement.id", 
                                     "substitution.replacement.name", "50_50.outcome.id", "50_50.outcome.name", "out", "pass.outswinging", 
                                     "pass.technique.id", "pass.technique.name", "clearance.head", "clearance.body_part.id", "clearance.body_part.name", 
                                     "clearance.right_foot", "clearance.left_foot", "block.offensive", "pass.through_ball", "pass.inswinging", "clearance.other", 
                                     "pass.no_touch", "pass.miscommunication", "dribble.no_touch", "shot.aerial_won", "injury_stoppage.in_chain", 
                                     "ball_recovery.offensive", "foul_committed.penalty", "foul_won.penalty", "dribble.nutmeg", "miscontrol.aerial_won", 
                                     "pass.straight", "goalkeeper.punched_out", "goalkeeper.lost_in_play"])

for x in (shot_df.columns):
    print(x)


shot_df = shot_df.rename(columns={
    "id": "ShotID",
    "period": "Period",
    "timestamp": "TimeStamp",
    "minute": "Minunte",
    "second": "Second",
    "type.name": "TypeName",
    "possession_team.name": "PossessionTeamName",
    "team.name": "TeamName",
    "location": "Location",
    "player.name": "PlayerName",
    "position.name": "PositionName",
    "pass.recipient.name": "PassRecipientName",
    "pass.length": "PassLength",
    "pass.angle": "PassAngle",
    "pass.end_location": "PassEndLocation",
    "pass.type.name": "PassTypeName",
    "pass.body_part.name": "PassBodyPartName",
    "pass.outcome.name": "PassOutcomeName",
    "ball_receipt.outcome.name": "BallReceiptOutcomeName",
    "dribble.outcome.name": "DribbleOutcomeName",
    "pass.cross": "PassCross",
    "pass.shot_assist": "PassShotAssist",
    "shot.statsbomb_xg": "ShotStatsbombXG",
    "shot.end_location": "ShotEndLocation",
    "shot.type.name": "ShotTypeName",
    "shot.outcome.name": "ShotOutcomeName",
    "shot.technique.name": "ShotTechniqueName",
    "shot.body_part.name": "ShotBodyPartName",
    "goalkeeper.position.name": "GoalkeeperPositionName",
    "goalkeeper.technique.name": "GoalkeeperTechniqueName",
    "goalkeeper.type.name": "GoalkeeperTypeName",
    "goalkeeper.body_part.name": "GoalkeeperBodyPartName",
    "pass.aerial_won": "PassAerialWon",
    "pass.goal_assist": "PassGoalAssist",
    "shot.deflected": "ShotDeflected",
    "shot.first_time": "ShotFirstTime",
    "goalkeeper.end_location": "GoalkeeperEndLocation",
    "MatchID": "MatchID",
    "shot.one_on_one": "ShotOneOnOne",
    "shot.redirect": "ShotRedirect",
    "shot.open_goal": "ShotOpenGoal",
    "block.save_block": "BlockSaveBlock"

    })


shot_df.to_csv('Clean_Statsbomb_Data/shotCollection.csv', index = False)