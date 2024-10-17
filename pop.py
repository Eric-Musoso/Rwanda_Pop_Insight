import geopandas as gpd
import folium
from dash import dcc, html
from dash.dependencies import Input, Output
from dash import Dash
import json
import plotly.express as px
import plotly.graph_objects as go
import branca.colormap as cm

# Initialize Dash app
app = Dash(__name__)

# Read the GeoJSON and population data
gdf = gpd.read_file(r'D:\Munster\ThirdSemester\Mystuff\Popdata.geojson')
gdf1 = gpd.read_file(r'D:\Munster\ThirdSemester\Mystuff\adminbdr.geojson')

# Filter relevant columns from admin boundaries
filtered_gdf1 = gdf1[['shapeName', 'geometry']]

# Group and sum population data by province, district, and period
gdf = gdf.groupby(['province', 'district', 'period'])[['Male', 'Female', 'Total']].sum().reset_index()

# Merge the boundary data with population data
all_gdf = filtered_gdf1.merge(gdf, left_on='shapeName', right_on='district')

# Ensure both dataframes have the same CRS
if not all_gdf.crs == filtered_gdf1.crs:
    all_gdf = all_gdf.to_crs(filtered_gdf1.crs)

# Convert the merged GeoDataFrame to a valid GeoJSON for Folium
merged_geojson = json.loads(all_gdf.to_json())

# Function to generate the Folium map
# Function to generate the Folium map
def generate_map(data, year):
    # Filter data for the selected year
    dff = data[data["period"] == year]

    # Create a base map centered on Rwanda
    m = folium.Map(location=[-1.9403, 29.8739], zoom_start=8, tiles='cartodb positron')

    # Min and max for total population
    min_population = dff['Total'].min()
    max_population = dff['Total'].max()

    # Create a custom color scale using branca.colormap.LinearColormap with 5 categories
    colormap = cm.LinearColormap(
        colors=['#fee0d2', '#fcbba1', '#fc9272', '#fb6a4a', '#de2d26'],  # 5 color categories
        vmin=min_population,
        vmax=max_population
    )

    # Add the choropleth layer manually, using the custom colormap
    folium.GeoJson(
        data=merged_geojson,
        style_function=lambda feature: {
            'fillColor': colormap(dff[dff['district'] == feature['properties']['district']]['Total'].values[0])
            if feature['properties']['district'] in dff['district'].values
            else '#ffffff',
            'color': 'white',
            'weight': 0.5,
            'fillOpacity': 0.5,
        },
        tooltip = folium.features.GeoJsonTooltip(
       fields=['district', 'Male', 'Female', 'Total'],
       aliases=['District:', 'Male Pop:', 'Female Pop:', 'Total Pop:'],
       localize=True,
       labels=True,  # Correct parameter
      max_width=750,  # Works properly
      style="""
        background-color: #F0EFEF;
        border: 2px solid black;
        border-radius: 3px;
        box-shadow: 3px;
        font-size: 12px;
       """)
).add_to(m)

    # Add the colormap as a legend with white-colored title and values
    colormap.caption = 'Total Population'
    colormap.add_to(m)

    return m._repr_html_()


# Function to generate population per province chart sorted in descending order
def population_per_district(data, year):
    dff = data[data["period"] == year].groupby('district')['Total'].sum().reset_index()
    dff = dff.sort_values(by='Total', ascending=False)  # Sort by total population in descending order
    fig = px.bar(dff, x='Total', y='district', title=f"Total Population per Distric in {year}",
                 orientation='h', template='plotly_dark')  # Horizontal bar chart
    fig.update_layout(paper_bgcolor='#2c2f38', plot_bgcolor='#2c2f38')
    return fig

# Function to generate male vs female chart per district
def male_vs_female(data, year):
    dff = data[data["period"] == year]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=dff['district'], y=dff['Male'], name='Male', marker_color='blue'))
    fig.add_trace(go.Bar(x=dff['district'], y=dff['Female'], name='Female', marker_color='pink'))
    fig.update_layout(barmode='group', title=f"Male vs Female Population per District in {year}", template='plotly_dark',
                      paper_bgcolor='#2c2f38', plot_bgcolor='#2c2f38')
    return fig

# Function to generate a new population chart showing total population per district over time with years in the legend
def population_per_district_year(data):
    fig = px.line(data, x='district', y='Total', color='period', title="Population per District Over Time",
                  template='plotly_dark', line_shape='spline')  # Smooth the line using 'spline'
    fig.update_layout(paper_bgcolor='#2c2f38', plot_bgcolor='#2c2f38')
    return fig

# Updated layout to position the "Population per District Over Time" chart horizontally
app.layout = html.Div([
    html.Div([  # Left side - Map
    html.H1("Rwanda Population Insights", style={'text-align': 'center', 'color': 'white'}),

    # Dropdown for year selection
    dcc.Dropdown(id="slct_year",
                 options=[{"label": "2002", "value": 2002},
                          {"label": "2012", "value": 2012},
                          {"label": "2022", "value": 2022}],
                 multi=False,
                 value=2022,
                 style={'width': "40%", 'color': 'black'}
                 ),

    html.Div(id='output_container', style={'color': 'gray'}),
    html.Br(),

     html.Iframe(id='map', srcDoc=None, width='100%', height='600'),
    ], style={'width': '50%', 'display': 'inline-block', 'vertical-align': 'top'}),

html.Div([  # Main container for the dashboard

    # Right side - Dashboard with indicators and bar charts
    html.Div([  
        # Indicators for male, female, and total population
        html.Div(id='total_male', style={'display': 'inline-block', 'width': '30%', 'color': 'white', 'text-align': 'center', 'background-color': '#2c2f38', 'padding': '10px', 'margin': '10px'}),
        html.Div(id='total_female', style={'display': 'inline-block', 'width': '30%', 'color': 'white', 'text-align': 'center', 'background-color': '#2c2f38', 'padding': '10px', 'margin': '10px'}),
        html.Div(id='total_population', style={'display': 'inline-block', 'width': '30%', 'color': 'white', 'text-align': 'center', 'background-color': '#2c2f38', 'padding': '10px', 'margin': '10px'}),
    ], style={'display': 'flex', 'justify-content': 'space-around', 'align-items': 'center'}),
     
    # Bar chart showing total population per province (now horizontal)
    dcc.Graph(id='population_per_district_year', style={'background-color': '#2c2f38', 'padding': '5px', 'margin': '3px', 'height': '40%'}),

    # Bar chart showing male vs female population per district
    dcc.Graph(id='male_vs_female', style={'background-color': '#2c2f38', 'padding': '10px', 'margin': '3px', 'height': '40%',}),

], style={'width': '30%', 'height': '100%', 'display': 'inline-block', 'vertical-align': 'top'}),  # Set width for the right-side dashboard

# Another section with line chart
html.Div([  
    # Line chart showing population per district with year as the legend
    dcc.Graph(id='population_per_district', 
              style={'background-color': '#2c2f38', 'padding': '10px', 'margin': '16px', 'height': '90%', 'width': '92%'})  # Ensure the chart takes full space
], style={'width': '20%', 'height': '100%', 'display': 'inline-block', 'vertical-align': 'top'}),  # Corrected the style

], style={'background-color': '#1c1e24', 'padding': '10px', 'height': '100vh',})  # Main container style



# Callback to update the map and charts
@app.callback(
    [Output('output_container', 'children'),
     Output('map', 'srcDoc'),
     Output('total_male', 'children'),
     Output('total_female', 'children'),
     Output('total_population', 'children'),
     Output('population_per_district_year', 'figure'),
     Output('male_vs_female', 'figure'),
     Output('population_per_district', 'figure')],
    [Input('slct_year', 'value')]  # Input should reference the dropdown ID
)
def update_graph(option_slctd):
    # Filter data for the selected year
    dff = all_gdf[all_gdf['period'] == option_slctd]

    # Update indicators
    total_male = f"Male Population: {dff['Male'].sum():,.0f}"
    total_female = f"Female Population: {dff['Female'].sum():,.0f}"
    total_population = f"Total Population: {dff['Total'].sum():,.0f}"

    # Generate the Folium map for the selected year
    map_html = generate_map(all_gdf, option_slctd)

    # Generate bar charts and the new line chart
    gender_chart = male_vs_female(all_gdf, option_slctd)
    district_chart_year = population_per_district_year(all_gdf)
    district_pop_chart = population_per_district(all_gdf, option_slctd)

    container = f"The year chosen by the user was: {option_slctd}"

    return container, map_html, total_male, total_female, total_population, district_chart_year, gender_chart, district_pop_chart

if __name__ == '__main__':
    app.run_server(debug=True)
