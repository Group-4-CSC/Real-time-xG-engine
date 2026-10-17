# Statsbomb Data

**Database Information**
- To download the Statsbomb data go here: https://github.com/hudl/open-data
- Create a folder called Analytics/Data/Raw_Statsbomb_Data/ then create two more folders CL_Final_Match_Data and CL_Final_Shot_Data insert match and shot data.
- Run Data_Cleaning.py
- Credit to Statsbomb for providing the data for our project.
- The CSV matchCollection collects relevant data for our application such as the Match Date, Home Score, Away Score, Home Team Name, Away Team Name etc. 
- The CSV shotCollection collects relevant data for our application such as  the x and y coordinates that represent  the shot's position as a percentage of the entire pitch, the name of the player taking the shot, the team name etc.

**Data_Cleaning.py Setup**
- Data_Cleaning.py is being used to prepare the data for the application
- Before running the file you must install the required dependinces using the command pip install -r ../../requirements.txt
- Before running Data_Cleaning.py you must run cd Analytics/Data
- Run the application using the following command: python3 Analytics/Data/Data_Cleaning.py
- The raw statsbomb data is stored inside Analytics/Data/Raw_Statsbomb_Data/CL_Final_Match_Data and Analytics/Data/Raw_Statsbomb_Data/CL_Final_Shot_Data
- The generated CSV files are outputted to Analytics/Data/Clean_Statsbomb_Data/

**MongoDB Data Ingestion**
- Collection Names: shotCollection, matchCollection
- CSVs are manually inserted into MongoDB 