from datetime import date

import requests
import json
import os 
from dotenv import load_dotenv
load_dotenv()  
import psycopg2


api_key = os.getenv('FRED_API_KEY')
file_type = 'json'

series_id = {
    'CPIAUCSL': 'cpi',
    'PPIACO': 'ppi',
    'DCOILWTICO': 'oil_amt', 
    'M2SL': 'prev_m2'
}



for fred_code, nickname in series_id.items():
    url = f'https://api.stlouisfed.org/fred/series/observations?series_id={fred_code}&api_key={api_key}&file_type={file_type}&output_type=2'
    response = requests.get(url)
        
    if response.status_code == 200:
        data = response.json()
        with open(f'{nickname}_observations.json', 'w') as f:
                json.dump(data, f)
    else: 
        print(f'Error fetching data for {fred_code} - observations: {response.status_code}')


database = psycopg2.connect(
    dbname = 'InflationProject',
    user = 'postgres',
    host = 'localhost'
)




cursor = database.cursor()

example_query = """
INSERT INTO raw_series (series_id, observation_date, value, release_date, vintage, time_tale) 
VALUES (%s, %s, %s, %s, %s, %s)
"""


for nickname in series_id.values():
    
    filename_observations = f'{nickname}_observations.json'
    if not os.path.exists(filename_observations):
        print(f'File {filename_observations} does not exist. Skipping.')
        continue
    else: 
        with open(f'{nickname}_observations.json', 'r') as f:
            data = json.load(f)
            records = data.get('observations', [])
            for record in records:
                ser_id = nickname
                observation_date = record['date']
                if record['value'] == '.':
                    value = None
                else:
                    value = float(record['value'])
                release_date = record.get('realtime_start', None)
                vintage = record.get('realtime_end', None) 
                time_tale = date.today()

                cursor.execute(example_query, (ser_id, observation_date, value, release_date, vintage, time_tale))
                
database.commit() 
cursor.close()
database.close()
                

