import pandas as pd
import numpy as np
import geopandas

def read_covid_df(filename):
    df = pd.read_csv(filename)
    df = df.fillna({'Province/State':''})
    df['Combined_Key'] = df.apply(lambda x: x['Province/State']+', '+x['Country/Region'] if x['Province/State']!='' else x['Country/Region'], axis=1)
    df = df.set_index(['Combined_Key', 'Province/State', 'Country/Region', 'Lat', 'Long'])
    df.columns = pd.to_datetime(df.columns)
    df = df.reset_index()
    return df

def remove_na(df_in):
    df = df_in.copy()
    df.loc[df['Combined_Key']=='Northwest Territories, Canada', 'iso3'] = 'CAN'
    df.loc[df['Population'].isna(), 'Population'] = 0
    df.drop(labels = df.loc[df['Combined_Key']=='Diamond Princess'].index, inplace=True)
    df.drop(labels = df.loc[df['Combined_Key']=='MS Zaandam'].index, inplace=True)
    return df

def prepare_covid_data_map(df_recovered_pop, df_dead_pop, df_confirmed_pop):
    columns_ = ['Combined_Key', 'Province/State', 'Country/Region', 'Lat', 'Long', 'iso3', 'Population']
    df_recovered_pop_index = df_recovered_pop.set_index(columns_)
    df_dead_pop_index = df_dead_pop.set_index(columns_)
    df_confirmed_pop_index = df_confirmed_pop.set_index(columns_)
    tser = df_confirmed_pop_index.iloc[:,-1]
    tser.name = "Confirmed"
    tdf = tser.reset_index()
    # Add in deaths
    tser = df_dead_pop_index.iloc[:,-1]
    tser.name = "Deaths"
    map_df = tdf.join(tser.reset_index(drop=True))
    # Add in Recovered
    tser = df_recovered_pop_index.iloc[:,-1]
    tser.name = "Recovered"
    map_df = map_df.join(tser.reset_index(drop=True))
    map_df.fillna({'Combined_Key':'', 'Province/State':'', 'Country/Region':'', 'Lat':0, 'Long':0, 'iso3':'', 'Population':0, 'Confirmed':0, 'Deaths':0, 'Recovered':0}, inplace=True)
    map_df['Size'] = np.log1p(map_df['Confirmed']) * 1.5
    df_map_gr = map_df.groupby('iso3').agg({'Combined_Key':'first', 'Province/State':'first', 'Country/Region':'first', 'Population':'sum', 'Confirmed':'sum', 'Deaths':'sum', 'Recovered':'sum'}).reset_index()
    df_map_gr = df_map_gr.sort_values(by='Country/Region')

    df_map_gr['ConfirmedDensity']    = df_map_gr['Confirmed']/df_map_gr['Population']
    df_map_gr['DeathsDensity']       = df_map_gr['Deaths']/df_map_gr['Population']
    df_map_gr['RecoveredDensity']    = df_map_gr['Recovered']/df_map_gr['Population']
    
    return map_df, df_map_gr

def merge_countries(gdfo, sovereignt, name_en, iso_a3):
    gdf = gdfo.copy()
    feat = 'SOVEREIGNT'
    if sovereignt=='Palestine':
        feat = 'ADMIN'
    df = gdf.loc[(gdf[feat]==sovereignt) & (gdf['ISO_A3']=='-99')]
    print(df.index[0:-1])
    index = df.index[0:-1].tolist()
    #print(df[['SOVEREIGNT', 'NAME_EN', 'ISO_A3']])
    df_merged = df.unary_union 
    gdf = gdf.drop(labels=index)
    gdf.loc[(gdf[feat]==sovereignt) & (gdf['ISO_A3']=='-99'), 'geometry'] = geopandas.GeoDataFrame(geometry=[df_merged]).geometry.values
    gdf.loc[(gdf[feat]==sovereignt) & (gdf['ISO_A3']=='-99'), 'NAME_EN'] = name_en
    gdf.loc[(gdf[feat]==sovereignt) & (gdf['ISO_A3']=='-99'), 'ISO_A3'] = iso_a3
    #print(gdf.loc[gdf[feat]==sovereignt, ['SOVEREIGNT', 'NAME_EN', 'ISO_A3']])
    #gdf.loc[gdf[feat]==sovereignt].plot()
    return gdf

