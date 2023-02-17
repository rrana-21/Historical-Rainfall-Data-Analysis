
# # Import packages
import pandas as pd 
import geopandas as gdp 
import matplotlib.pyplot as plt 
import pathlib
import streamlit as st
from pandas import json_normalize 
import requests
import plotly.express as px

st.title("Historical Rainfall Data Analysis for The City of Calgary")

st.write('This web application aims to analyze historical rainfall data for The City of Calgary sort it by the quadrants of The City, and display the total rainfall per year for each quadrant through this choropleth map. By providing insights into the historical rainfall patterns of The City, this project will help inform future infrastructure and land use decisions while also providing valuable information to local residents.')

st.markdown('***')

# ## DATA
# ### Importing data from City of Calgary's Open Data
#histroical rainfall 
r = requests.get('https://data.calgary.ca/resource/d9kv-swk3.json?$limit=1000000')
arr = r.json()
df = pd.DataFrame.from_dict(arr)
#rainfall gauge locations 
g = requests.get('https://data.calgary.ca/resource/x9fe-3zah.json?$limit=1000')
loc_arr = g.json()
loc_df =  pd.DataFrame.from_dict(loc_arr)
#quadrant boundaries - bring in geojson file
f = pathlib.Path('City_Quadrants.geojson')
gdf = gdp.read_file(f)
#convert channel feature for each dataframe is an int, and change rainfall feature datatype to float 
df['channel'] = df['channel'].astype(int)
df['rainfall'] = df['rainfall'].astype(float)
loc_df['channel'] = loc_df['channel'].astype(int)
### Merge df and loc_df on channel 
channel_df = df.merge(loc_df, on='channel')
#only select the necessary features and store it in c_df
c_df = channel_df[['name_x', 'year', 'rainfall', 'channel', 'quadrant']]
#group by name and year, and sum by rainfall
sum_df = c_df.groupby(['quadrant','year'])['rainfall'].sum().reset_index()
###merge c_df with quadrants to bring in multipolygon data for all rows
geo_df = sum_df.merge(gdf, on='quadrant', how='outer')
#remove quadrant status from the dataframe and rename some columns 
del geo_df['quadrant_status']
geo_df = geo_df.rename(columns={'name_x': 'name'})
### Clean the dataframe to ensure we are only including years 1990-Present
#convert "year" to int 
geo_df['year'] = geo_df['year'].astype(int)
#drop years before 1990
geo_df = geo_df.drop(geo_df[geo_df.year.isin([1988,1989])].index)
#ensure it is a geodataframe
results_gdf = gdp.GeoDataFrame(geo_df)
#change column name datatype to str 
results_gdf.columns = results_gdf.columns.astype(str)

#User Input for Year
year_value = st.slider('Slide to select a year', min_value=1990, max_value=2021, value=None, step=1)

# Display the value of the slider
st.write('Selected year:', year_value)

#Output of map
mapped_gdf = results_gdf[results_gdf.year == year_value]

Rainfall = mapped_gdf['rainfall']

fig = px.choropleth_mapbox(mapped_gdf,
                           geojson=mapped_gdf['geometry'],
                           color=Rainfall,
                           locations=mapped_gdf.index,
                           color_continuous_scale="Reds",
                           mapbox_style="carto-positron",
                           center={'lat':51.0447, 'lon':-114.0719},
                           zoom=9.5,
                           opacity=0.8,
                           height=900,
                           hover_name='quadrant',
                           hover_data=['rainfall'],
                           labels=False)

fig.update_layout(coloraxis_colorbar=dict(title="Rainfall (mm)"),
                  hovermode="closest")

fig.update_traces(hovertemplate='<b>%{hovertext}</b><br>Rainfall: %{z:,.0f}')

# Render the plotly figure using Streamlit
st.plotly_chart(fig)


