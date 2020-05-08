import pandas as pd
import numpy as np
import geopandas
import json
import utils
# os methods for manipulating paths
from os.path import dirname, join

# Bokeh basics 
from bokeh.io import curdoc, show
from bokeh.models.widgets import Tabs

# Each tab is drawn by one script
from tabs.draw_map import map_tab
from tabs.draw_timeseries import time_series_tab


# Population
pop_file = join(dirname(__file__), 'data/csse_covid_19_data', 'UID_ISO_FIPS_LookUp_Table.csv')
#pop_file = 'data/csse_covid_19_data/UID_ISO_FIPS_LookUp_Table.csv'
df_pop = pd.read_csv(pop_file)
df_pop = df_pop.fillna({'Province_State':'', 'Population':0})
df_pop = df_pop.sort_values(by='Country_Region')
df_pop_reduced = df_pop[['iso3','Population','Combined_Key']]

# COVID data
filename = join(dirname(__file__), 'data/csse_covid_19_data/csse_covid_19_time_series', 'time_series_covid19_confirmed_global.csv')
df_confirmed = utils.read_covid_df(filename)
filename = join(dirname(__file__), 'data/csse_covid_19_data/csse_covid_19_time_series', 'time_series_covid19_deaths_global.csv')
df_dead = utils.read_covid_df(filename)
filename = join(dirname(__file__), 'data/csse_covid_19_data/csse_covid_19_time_series', 'time_series_covid19_recovered_global.csv')
df_recovered = utils.read_covid_df(filename)

# merge COVID and Population
df_confirmed_pop = pd.merge(left=df_confirmed, 
                            right=df_pop_reduced, 
                            how='left', 
                            on='Combined_Key')
df_dead_pop = pd.merge(left=df_dead, 
                        right=df_pop_reduced, 
                        how='left', 
                        on='Combined_Key')
df_recovered_pop = pd.merge(left=df_recovered, 
                            right=df_pop_reduced, 
                            how='left', 
                            on='Combined_Key')
# clean dataframes
df_confirmed_pop = utils.remove_na(df_confirmed_pop)
df_dead_pop = utils.remove_na(df_dead_pop)
df_recovered_pop = utils.remove_na(df_recovered_pop)
# data for map
map_circles, map_df = utils.prepare_covid_data_map(df_recovered_pop, df_dead_pop, df_confirmed_pop)
min_density = map_df['ConfirmedDensity'].min().min()
max_density = map_df['ConfirmedDensity'].max().max()

# WORLD MAP
m_units = join(dirname(__file__), 'data/map/ne_50m_admin_0_map_units', 'ne_50m_admin_0_map_units.shp')
gdf_m_units = geopandas.read_file(m_units)
gdf_m_units2 = geopandas.read_file(m_units)
gdf_m_units.loc[gdf_m_units['NAME_EN'] == 'Georgia', 'ISO_A3'] = 'GEO'
gdf_m_units.loc[gdf_m_units['NAME_EN'] == 'Kosovo', 'ISO_A3'] = 'XKS'
missing_r = ['Antigua and Barbuda', 'Belgium', 'Bosnia and Herzegovina', 'Norway', 'Papua New Guinea', 'Portugal', 'United Kingdom', 'Palestine', 'Republic of Serbia']
missing_iso = ['ATG', 'BEL', 'BIH', 'NOR', 'PNG', 'PRT', 'GBR', 'PSE', 'SRB']
counter = 0
for r in missing_r:
    iso = missing_iso[counter]
    print(f'{counter}, {r}, {iso}')
    gdf_m_units = utils.merge_countries(gdfo=gdf_m_units, sovereignt=r, name_en=r, iso_a3=iso)
    counter += 1
    print()
gdf_m_units_drop = gdf_m_units.drop(gdf_m_units.loc[gdf_m_units['NAME_EN']=='Antarctica'].index)
gdf_m_units_drop = gdf_m_units_drop.drop(gdf_m_units_drop.loc[gdf_m_units_drop['ISO_A3']=='-99'].index)
gdf_m_units_sel = gdf_m_units_drop[['NAME_EN', 'ISO_A3', 'geometry']]

# merge geometry and COVID
map_color_df = pd.merge(gdf_m_units_sel, map_df, left_on='ISO_A3', right_on='iso3', how='left')
map_color_df_sel_col = map_color_df[['ISO_A3', 'NAME_EN', 'Combined_Key', 'Population', 'Confirmed', 'Deaths','Recovered', 
                                     'ConfirmedDensity', 'DeathsDensity', 'RecoveredDensity', 
                                     'geometry']]
#print(map_color_df_sel_col.isna().sum())
map_color_df_sel_col.fillna({'ISO_A3':'', 'NAME_EN':'', 'Combined_Key':'', 'Population':0, 'Confirmed':0, 'Deaths':0,'Recovered':0, 
                            'ConfirmedDensity':0, 'DeathsDensity':0, 'RecoveredDensity':0, 
                            }, inplace=True)
#Read data to json.
merged_json = json.loads(map_color_df_sel_col.to_json())
#Convert to String like object.
json_data = json.dumps(merged_json)
#print(f'json {json_data}')

# create tabs
tab1 = map_tab(json_data, map_circles, min_density, max_density)
tab2 = time_series_tab(df_confirmed_pop, df_dead_pop, df_recovered_pop)

# put all the tabs into one application
tabs = Tabs(tabs = [tab1, tab2])

# put the tabs in the current document for display
curdoc().add_root(tabs)
#show(tabs)
