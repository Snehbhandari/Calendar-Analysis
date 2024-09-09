# +
from dash import Dash, html, dash_table, dcc, callback, Input, Output
import pandas as pd 
import plotly.express as px
import numpy as np

# dcc module has dcc.Graphs which helps render interactive graphs 

# read data 
df = pd.read_csv("calendar_events.csv") 


# +
# converting objects to integers 
df['Duration'] = pd.to_timedelta(df['Duration']) 
df['Minutes_duration'] = df['Duration'].dt.total_seconds() / 60 
df['Hours_duration'] = df['Minutes_duration']/ 60 

df['Start Date'] = pd.to_datetime(df['Start Date'], format='%Y-%m-%d') 

df['End Date'] = pd.to_datetime(df['End Date'], format='%Y-%m-%d') 

df.drop(columns=["Start Time", "End Time", "Event ID"], inplace=True) 
# -

# study dataset
new_df_st = df[df['Calendar Name'] == 'Study']
new_df_st = new_df_st.rename(columns={'Calendar Name': 'Study'})
# projects dataset
new_df_proj = df[df['Calendar Name'] == 'Projects']
new_df_proj = new_df_proj.rename(columns={'Calendar Name': 'Projects'})

# initialize the dash app using the Dash constructor 
app = Dash() 

# App layout
app.layout = html.Div(children=[
    # Heading 
    html.H1(children='My First App with Data'),
    
    # Display Data 
    dash_table.DataTable(data=df.to_dict('records'), page_size=10),
    
    # First Graph - Total Time spent per Calendar 
    html.H2(children="Total Time/ Calendar"),
    dcc.Graph(
        figure=px.histogram(
            df, 
            x='Calendar Name', 
            y='Hours_duration', 
            histfunc='sum'
        ).update_layout(
        yaxis_title="Total Time Spent (In Hours)")
    ), 
    
    # Second Graph - Total number of events per Calendar 
    html.H2(children="Total Events/ Calendar"),
    dcc.Graph(
        figure=px.histogram(
            df, 
            x='Calendar Name', 
            histfunc='count', 
        ).update_layout(
        yaxis_title="Total Events Created")
    ), 
    
    html.H2(children="Histogram for Duration of events"),
    # Radio Buttons 
    # dcc.RadioItems(options=["Study", "Projects"], value ="Study", id="hist_radioButtons"),
    dcc.Dropdown(
    options=[
        {'label': 'Study Cal', 'value': 'Study'},
        {'label': 'Projects Clndr', 'value': 'Projects'}
    ],
    value='Study',
    id='hist_dropdown'
    ), 
    dcc.Graph(figure={}, id="graph_controls")
])


@callback(
    Output(component_id='graph_controls', component_property='figure'),
    Input(component_id='hist_dropdown', component_property='value')
)
def update_graph(name): 
    if name == "Study":
        dataframe=new_df_st
    elif name =="Projects":
        dataframe=new_df_proj
    
    fig=px.histogram(dataframe, x='Hours_duration', histfunc='count').update_layout(
        title="Study", 
        yaxis_title="Total Events Created")
    return fig


if __name__ == '__main__':
    app.run(debug=True)


