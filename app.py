from dash import Dash, html, dash_table, dcc
import pandas as pd
import os
from dotenv import load_dotenv
from sodapy import Socrata
from typing import Final, Tuple, Dict, Any
import plotly.express as px

# Configure pandas
pd.options.mode.copy_on_write = "warn"

# Constants
WHERE_CLAUSE: Final = "border = 'US-Canada Border' AND date >= '2016-01-01'"
DATASET_IDENTIFIER: Final = "keg4-3bc2"


def initialize_client() -> Tuple[Socrata, str]:
    """Initialize and return Socrata client and app token status.
        returns client, app_token_status
    """
    load_dotenv()
    app_token = os.getenv("SOCRATA_APP_TOKEN")

    if app_token:
        app_token_status = "Successfully loaded app token."
    else:
        app_token_status = "Warning: APP_TOKEN not found."

    print(app_token_status)
    client = Socrata("data.bts.gov", app_token)
    return client, app_token_status

def fetch_border_data(client: Socrata) -> pd.DataFrame:
    """Fetch border crossing data from Socrata API."""
    # Get row count first
    row_count = int(client.get(
        DATASET_IDENTIFIER,
        query=f"SELECT count(*) WHERE {WHERE_CLAUSE}",
    )[0]["count"])
    results = client.get(DATASET_IDENTIFIER, limit=row_count, where=WHERE_CLAUSE)
    return pd.DataFrame.from_records(results)


def clean_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Clean and preprocess the data.
    Returns df, nulls_df
    """
    # Drop unnecessary columns
    df = df.drop(columns=["point", "latitude", "longitude"], errors='ignore')

    # Filter for null values
    nulls_df = df[df.isnull().any(axis=1)]

    # Fix missing state for port_code "3315"
    df["port_code"] = df["port_code"].astype(str)
    df.loc[df["port_code"] == "3315", "state"] = "Montana"

    return df, nulls_df


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


def create_dash_app(df: pd.DataFrame, sum_df: pd.DataFrame, nulls_df: pd.DataFrame, token_status: str) -> Dash:
    """Create and configure the Dash application."""

    app = Dash(__name__)

    # Create the line figure
    fig = px.line(sum_df, x="month", y="value", color="year", symbol="year",
                 title="Monthly Border Crossings by Year")

    app.layout = html.Div([
        html.H1(children="US-Canada Border Crossings Dashboard"),
        html.P(children=f"App token status: {token_status}"),

        # Main visualization
        dcc.Graph(figure=fig),

        # Data tables section
        html.H2("Data Tables"),
        html.H3("Null Values in Data"),
        dash_table.DataTable(
            data=nulls_df.to_dict("records"),
            page_size=10,
            style_table={'overflowX': 'auto'}
        ),

        html.H3("Monthly Summary"),
        dash_table.DataTable(
            data=sum_df.to_dict("records"),
            page_size=12,
            style_table={'overflowX': 'auto'}
        ),

        html.H3("Raw Data"),
        dash_table.DataTable(
            data=df.to_dict("records"),
            page_size=100,
            style_table={'overflowX': 'auto'}
        ),
    ])

    return app


def main():
    """Main function to run the application."""
    # Initialize client and fetch data
    client, token_status = initialize_client()
    try:
        df = fetch_border_data(client)
    finally:
        client.close()

    # Process data
    cleaned_df, nulls_df = clean_data(df)
    processed_df, monthly_summary = transform_data(cleaned_df)

    # Create and run app
    app = create_dash_app(processed_df, monthly_summary, nulls_df, token_status)

    # gunicorn entry point
    server = app.server

    if __name__ == "__main__":
        print("m2m-capstone1-dash is running")
        app.run(debug=True, host="0.0.0.0", port=10000)


