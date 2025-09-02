from dash import Dash, html, dash_table, dcc
import pandas as pd
import os
from dotenv import load_dotenv
from sodapy import Socrata
from typing import Final, Tuple, Dict, Any
import plotly.express as px

# Configure pandas
pd.options.mode.copy_on_write = "warn"

# get APP_TOKEN and initialize Socrata client

# Constants
WHERE_CLAUSE: Final = "border = 'US-Canada Border' AND date >= '2016-01-01'"
DATASET_IDENTIFIER: Final = "keg4-3bc2"

def initialize_client() -> Tuple[Socrata, str]:
    """Initialize and return Socrata client and app token status."""
    load_dotenv()
    app_token = os.getenv("SOCRATA_APP_TOKEN")

    if app_token:
        app_token_status = "Successfully loaded app token."
    else:
        app_token_status = "Warning: APP_TOKEN not found."

    print(app_token_status)
    client = Socrata("data.bts.gov", app_token)
    return client, app_token_status

# refactor this into main later
client, app_token_status = initialize_client()

def fetch_border_data(client: Socrata) -> pd.DataFrame:
    """Fetch border crossing data from Socrata API."""
    # Get row count first
    row_count = int(client.get(
        DATASET_IDENTIFIER,
        query=f"SELECT count(*) WHERE {WHERE_CLAUSE}",
    )[0]["count"])
    results = client.get(DATASET_IDENTIFIER, limit=row_count, where=WHERE_CLAUSE)
    return pd.DataFrame.from_records(results)

# refactor into main later
# Convert to pandas DataFrame
results_df = fetch_border_data(client)
client.close()

def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Clean the data."""
    # Drop unnecessary columns
    df = df.drop(columns=["point", "latitude", "longitude"], errors='ignore')

    # Filter for null values
    nulls_df = df[df.isnull().any(axis=1)]

    # Fix missing state for port_code "3315"
    df["port_code"] = df["port_code"].astype(str)
    df.loc[df["port_code"] == "3315", "state"] = "MT"

    return df, nulls_df

# refactor into main later
results_df, nulls_df = clean_data(results_df)

# Data transformation
def transform_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Transform the data for analysis and visualization."""
    # Convert date and extract components
    df["date"] = pd.to_datetime(df["date"])
    # results_df["month"] = results_df["date"].dt.strftime('%b')
    df["month"] = df["date"].dt.month
    df["year"] = df["date"].dt.year
    df["date"] = df["date"].dt.date

    # Ensure value is integer
    df['value'] = df['value'].astype(int)

    # Filter for passenger and pedestrian data only
    filtered_df = df[df.measure.str.contains("passenger|pedestrian", na=False, case=False)]

    # Calculate monthly sums
    sum_by_month = filtered_df.groupby(['year', 'month'])['value'].sum().reset_index()

    return filtered_df, sum_by_month

# refactor into main later
results_df, sum_by_month = transform_data(results_df)

# Dash app
app = Dash()
app.layout = [
    html.H1(children="m2m-capstone1-dash!"),
    html.P(children=f"App token status: {app_token_status}"),
    dcc.Graph(figure=px.line(sum_by_month, x="month", y="value", color="year", symbol="year")),
    html.Div(children="Null values: "),
    dash_table.DataTable(data=nulls_df.to_dict("records"), page_size=10),
    html.Hr(),
    dash_table.DataTable(data=results_df.to_dict("records"), page_size=10),
    html.Hr(),
    dash_table.DataTable(data=sum_by_month.to_dict("records"), page_size=12),
    html.Hr(),
    dash_table.DataTable(
        data=results_df.to_dict("records"),
        columns=[{"name": i, "id": i} for i in results_df.columns],
    ),
]

# gunicorn entry point
server = app.server

if __name__ == "__main__":
    print("m2m-capstone1-dash is running")
    app.run(debug=True, host="0.0.0.0", port=10000)
