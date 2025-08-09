from dash import Dash, html
import pandas as pd
import os
from dotenv import load_dotenv
from sodapy import Socrata

# get APP_TOKEN and initialize Socrata client

load_dotenv()

APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")

if APP_TOKEN:
    print("Successfully loaded app token.")
else:
    print("Warning: APP_TOKEN not found. Make sure it's set in your .env file.")

client = Socrata("data.bts.gov", APP_TOKEN)
# First 2000 results, returned as JSON from API / converted to Python list of
# dictionaries by sodapy.
results = client.get("keg4-3bc2", limit=2000)

# Convert to pandas DataFrame
results_df = pd.DataFrame.from_records(results)

app = Dash()
app.layout = html.Div(children="Hello from m2m-capstone1-dash!")

def main():
    print("m2m-capstone1-dash is running")
    app.run(debug=True)


if __name__ == "__main__":
    main()
