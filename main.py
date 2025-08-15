from dash import Dash, html, dash_table
import pandas as pd
import os
from dotenv import load_dotenv
from sodapy import Socrata

# get APP_TOKEN and initialize Socrata client

load_dotenv()
print('appname', os.getenv('app'))
APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")

if APP_TOKEN:
    print("Successfully loaded app token.")
else:
    print("Warning: APP_TOKEN not found. Make sure it's set in your .env file.")

client = Socrata("data.bts.gov", APP_TOKEN)
# First 2000 results, returned as JSON from API / converted to Python list of
# dictionaries by sodapy.
results = client.get("keg4-3bc2", limit=4000,
                     where="border = 'US-Canada Border'")
print('length', len(results))
# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results)

# Data cleaning
results_df.drop(columns=["point"], inplace=True)
results_df['date'] = pd.to_datetime(results_df['date'])
results_df['date'] = results_df['date'].dt.date
print('info', results_df.info())
nulls_df = results_df[results_df.isnull().any(axis=1)]
app = Dash()
app.layout = [
    html.H1(children="m2m-capstone1-dash!"),
    html.Div(children="Null values: "),
    dash_table.DataTable(data=nulls_df.to_dict("records"), page_size=10),
    html.Hr(),
    dash_table.DataTable(data=results_df.to_dict("records"), page_size=10),
    html.Hr(),
    dash_table.DataTable(data=results_df.to_dict("records"),
                         columns=[{"name": i, "id": i} for i in results_df.columns]),
]

def main():
    print("m2m-capstone1-dash is running")
    app.run(debug=True, host="0.0.0.0", port=10000)


if __name__ == "__main__":
    main()
