from dash import Dash, html, dash_table
import pandas as pd
import os
from dotenv import load_dotenv
from sodapy import Socrata
from typing import Final

# get APP_TOKEN and initialize Socrata client

load_dotenv()
print("appname", os.getenv("app"))
# Constants
APP_TOKEN: Final = os.getenv("SOCRATA_APP_TOKEN")
WHERE_CLAUSE: Final = "border = 'US-Canada Border' AND date >= '2017-01-01'"
DATASET_IDENTIFIER: Final = "keg4-3bc2"

if APP_TOKEN:
    print("Successfully loaded app token.")
else:
    print("Warning: APP_TOKEN not found. Make sure it's set in your .env file.")

client = Socrata("data.bts.gov", APP_TOKEN)
# First 2000 results, returned as JSON from API / converted to Python list of
# dictionaries by sodapy.
row_count = client.get(
    DATASET_IDENTIFIER,
    query=f"SELECT count(*) WHERE {WHERE_CLAUSE}",
)[0]["count"]
print("row_count", row_count)
row_count = int(row_count)
results = client.get(DATASET_IDENTIFIER, limit=row_count, where=WHERE_CLAUSE)
client.close()
print("length", len(results))
# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results)

# Data cleaning
results_df.drop(columns=["point"], inplace=True)

# Null values
nulls_df = results_df[results_df.isnull().any(axis=1)]

# "State" field of new port of entry "Chief Mountain Mt Poe" hasn't been populated yet.
# Will set "state" to "MT" for all records with port_code == "3315"
results_df["port_code"] = results_df["port_code"].astype(str)
results_df.loc[results_df["port_code"] == "3315", "state"] = "MT"


# Data transformation
results_df["date"] = pd.to_datetime(results_df["date"])
results_df["month"] = results_df["date"].dt.strftime('%b')
results_df["year"] = results_df["date"].dt.year
results_df["date"] = results_df["date"].dt.date

results_df['value'] = results_df['value'].astype(int)
sum_by_month = results_df.groupby(['year', 'month'])['value'].sum()
print("info", results_df.info())

# Get different entry categories (measure)
entry_categories = results_df['measure'].unique()
print("entry_categories", entry_categories)


# Dash app
app = Dash()
app.layout = [
    html.H1(children="m2m-capstone1-dash!"),
    html.Div(children="Null values: "),
    dash_table.DataTable(data=nulls_df.to_dict("records"), page_size=10),
    html.Hr(),
    dash_table.DataTable(data=results_df.to_dict("records"), page_size=10),
    html.Hr(),
    dash_table.DataTable(
        data=results_df.to_dict("records"),
        columns=[{"name": i, "id": i} for i in results_df.columns],
    ),
]

server = app.server

if __name__ == "__main__":
    print("m2m-capstone1-dash is running")
    app.run(debug=True, host="0.0.0.0", port=10000)
