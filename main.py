import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import requests
import json
import plotly.graph_objects as go
from dash.dependencies import Input, Output

# Any dictionary values to be used repeatedly
ENDPOINT = "https://api.coronavirus.data.gov.uk/v1/data"

structure = {
    "date": "date",
    "areaName": "areaName",
    "areaCode": "areaCode",
    "newCasesByPublishDate": "newCasesByPublishDate",
    "cumCasesByPublishDate": "cumCasesByPublishDate",
    "newDeaths28DaysByPublishDate": "newDeaths28DaysByPublishDate",
    "cumDeaths28DaysByPublishDate": "cumDeaths28DaysByPublishDate"}

metric_label = {
    "date": "Date",
    "areaName": "Area Name",
    "areaCode": "Area Code",
    "newCasesByPublishDate": "New Cases By Publish Date",
    "cumCasesByPublishDate": "Cumulative Cases By Publish Date",
    "newDeaths28DaysByPublishDate": "New Deaths 28Days By Publish Date",
    "cumDeaths28DaysByPublishDate": "Cumulative Deaths 28Days By Publish Date"}

country_d = {
    "United Kingdom": "overview",
    "England": "England",
    "Scotland": "Scotland",
    "Wales": "Wales"}

app = dash.Dash(__name__)


# Automate dataframe creation
def create_dataframe(area_name, structures):
    if area_name == "overview":
        filters = [
            f"areaType=overview"]
    else:
        filters = [
            f"areaType=nation",
            f"areaName={area_name}"]

    api_params = {
        "filters": str.join(";", filters),
        "structure": json.dumps(structures, separators=(",", ":"))
    }
    url = requests.get(ENDPOINT, api_params)
    url_ = json.loads(url.text)
    return pd.DataFrame(url_.get('data'))


# App layout
app.layout = html.Div(children=[
    html.Div([
        html.H1(children='COVID Data in the United Kingdom')
    ]),
    html.Div([
        html.H2(children='A web-based visualisation tool for COVID-19 in the UK')
    ]),
    html.Div([
        html.H3(children='This application is designed to provide an insight into COVID related date in'
                         'the UK'),

    ]),
    html.Div([
        html.P(children="Please select a country to start comparing statistics", className='one-half column'),
        html.P(children="Please select a metric to start comparing statistics", className='one-half column'),

    ]),

    html.Div([

        dcc.Dropdown(
            className="dropdown one-half column",
            id='country',
            options=[
                {'label': x, 'value': country_d[x]}
                for x in country_d
            ],
            value=['overview'],
            placeholder='Please select a country/countries',
            multi=True
        ),
    ]),
    html.Div([

        dcc.Dropdown(
            className="dropdown one-half column",
            id='metric_dropdown',
            options=[
                {'label': 'New Cases By Publish Date', 'value': 'newCasesByPublishDate'},
                {'label': 'New Deaths 28Days By Publish Date', 'value': 'newDeaths28DaysByPublishDate'},
                {'label': 'Cumulative Cases By Publish Date', 'value': 'cumCasesByPublishDate'},
                {'label': 'Cumulative Deaths 28Days By Publish Date', 'value': 'cumDeaths28DaysByPublishDate'}
            ],
            value='newCasesByPublishDate'
        ),
    ]),
    html.Br(),
    html.Br(),
    html.Div([
        html.H2("Quick Look", className='header'),
        html.P(className='quickLook', id='cases'),
        html.Div([
            dcc.Graph(
                className="line_chart",
                id='line_graph')

        ]),
    ]),
    html.Div([
        html.H3("Please choose a date to inspect the relevant data", className='header'),
        dcc.DatePickerSingle(className="date",
                             id='date_picker',
                             display_format='YYYY-MM-DD',

                             ),
    ]),

    html.Br(),
    html.Div([

        dcc.Graph(className="one-half column",
                  id='bar_chart'),

        dcc.Graph(className="one-half column",
                  id='age_bar')
    ]),
    html.Div([

    ]),

])


# Update line graph with country and metric
@app.callback(
    Output('line_graph', 'figure'),
    Input('country', 'value'),
    Input('metric_dropdown', 'value'))
def create_line_graph(country1, value):
    # Checks if the list is empty i.e. no country is selected and returns an empty graph as so
    if not country1:
        fig = px.line()
        return fig
    # If values exist it will create a dataframe with the first value
    else:
        df = create_dataframe(country1[0], structure)

        # For any extra values it creates a dataframe and concatenates to allow comparison of areas
        for x in country1:
            if country1[0] != x:
                df = pd.concat([df, create_dataframe(x, structure)])

        fig = px.line(df, x='date', y=value,
                      title=metric_label[value],
                      labels={
                          "date": "Date",
                          value: metric_label[value]
                      },
                      color="areaName")
        return fig


# Returns the total number of cases for each country
@app.callback(
    Output('cases', 'children'),
    Input('country', 'value'))
def update_cases(country):
    if not country:
        return html.Div([
            html.P("Please select a country to view total cases and deaths")

        ])
    else:
        df = create_dataframe(country[0], structure)
        cases = df["cumCasesByPublishDate"]
        death = df["cumDeaths28DaysByPublishDate"]
        total_cases = cases.max()
        total_deaths = death.max()
        if country[0] == "overview":
            country[0] = "the UK"

        return html.Div([
            html.P("Total cases in {}: {}".format(country[0], total_cases), className='box1 card_container',
                   id='totalCase cases'),
            html.P("Total deaths in {}: {}".format(country[0], total_deaths), className='box2 card_container',
                   id='totalDeath cases')
        ])


# Allows countries to be compared in a chosen metric for a chosen date
@app.callback(
    Output('bar_chart', 'figure'),
    Input('country', 'value'),
    Input('date_picker', 'date'),
    Input('metric_dropdown', 'value'))
def update_bar_chart(country, start_date, metric):
    fig = px.bar()
    # If there is no value in country or start date then it returns an empty graph
    if not country or not start_date:

        return fig
    else:
        df = create_dataframe(country[0], structure)
        for x in country:
            if country[0] != x:
                df = pd.concat([df, create_dataframe(x, structure)])
            if country[0] == "overview":
                country[0] = "United Kingdom"
        try:
            fig = px.bar(df.loc[df['date'] == start_date], x=country, y=metric,
                         text=metric,
                         color=country,
                         labels={
                             "x": "Country",
                             metric: metric_label[metric]})
            fig.update_traces(texttemplate='%{text:.3s}', textposition='outside')
        except ValueError:
            return fig
        except IndexError:
            return fig
    return fig


# Takes in a date and displays the number of cases in each age group and gender
@app.callback(
    Output('age_bar', 'figure'),
    Input('date_picker', 'date'))
def age_compare(date):
    fig = px.bar(title="Cases in England")
    # Creates a link with the following params
    structures = {
        "date": "date",
        "areaName": "areaName",
        "maleCases": "maleCases",
        "femaleCases": "femaleCases"
    }

    filters = [
        f"areaType=nation",
        f"areaName=England"]

    api_params = {
        "filters": str.join(";", filters),
        "structure": json.dumps(structures, separators=(",", ":"))
    }
    url = requests.get(ENDPOINT, api_params)
    url_ = json.loads(url.text)

    df = pd.DataFrame(url_.get('data'))
    # If a date has been selected a dataframe will be created

    if date:
        try:
            # Search data frame for correct date and create 2 new ones with both male and female cases
            date_ind = df[df['date'] == date].index.values
            df_m = pd.DataFrame(url_.get('data')[date_ind[0]].get('maleCases'))
            df_f = pd.DataFrame(url_.get('data')[date_ind[0]].get('femaleCases'))

            df4 = pd.concat([df_m, df_f], axis=0, ignore_index=False)

            df4['Gender'] = (len(df_m) * (1,) + len(df_f) * (2,))

            df4.sort_values(by=['age', 'Gender'], inplace=True)
            # Takes the previous days cumulative cases and subtracts them from the selected date
            df_m2 = pd.DataFrame(url_.get('data')[date_ind[0] + 1].get('maleCases'))
            df_f2 = pd.DataFrame(url_.get('data')[date_ind[0] + 1].get('femaleCases'))

            df5 = pd.concat([df_m2, df_f2], axis=0, ignore_index=False)
            df5['Gender'] = (len(df_m2) * (1,) + len(df_f2) * (1,))
            df5.sort_values(by=['age', 'Gender'], inplace=True)

            df4 = df4.set_index('age').subtract(df5.set_index('age'))
            # Replaces integers with male and female for easier labelling and comparison
            df4["Gender"] = df4["Gender"].astype(str)
            df4 = df4.replace(to_replace='0', value='Male')
            df4 = df4.replace(to_replace='1', value='Female')
            fig = px.bar(df4.reset_index(), x='age', y='value',
                         color='Gender',
                         barmode='group',
                         title="Cases in England",
                         labels={
                             'value': 'Number of Cases',
                             'age': 'Age'

                         })

            return fig

        except IndexError:
            return fig
        except ValueError:
            return fig

    else:

        return fig


if __name__ == '__main__':
    app.run_server(debug=True)
