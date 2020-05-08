import math

import pandas as pd
import numpy as np

from bokeh.tile_providers import get_provider, Vendors
from bokeh.plotting import figure, show
from bokeh.palettes import Dark2_8, brewer, Viridis, Viridis5, Viridis6, OrRd, Greys256, cividis, gray, viridis, linear_palette, Category10, Category20, Category20_16, RdYlGn
from bokeh.models import Legend, LegendItem, LogTicker, ColumnDataSource, Range1d, GeoJSONDataSource, ColorBar, BasicTicker, Label, LabelSet, Span, CategoricalColorMapper, HoverTool, Panel, FuncTickFormatter, SingleIntervalTicker, LinearAxis, Button
from bokeh.core.enums import LegendLocation
import itertools
from bokeh.models.mappers import ColorMapper, LinearColorMapper, LogColorMapper
from bokeh.models.widgets import CheckboxGroup, Slider, RangeSlider, Tabs, CheckboxButtonGroup, TableColumn, DataTable, Select
from bokeh.layouts import column, row, WidgetBox

import geopandas
import json


def prepare_covid_data_timeseries(df_cases):
    df = df_cases.copy()
    df = df.drop(['Lat', 'Long'], axis=1)
    df = df.groupby('Country/Region').sum()
    df.reset_index(inplace = True)

    diff_df = df.copy()
    diff_df.drop(['Population'], axis=1, inplace=True)
    diff_df.sort_values(by='Country/Region', inplace=True)
    c_r=diff_df['Country/Region']
    diff_df = diff_df.diff(axis=1)
    diff_df.fillna(0, inplace=True)
    diff_df['Country/Region']=c_r
    diff_df.set_index('Country/Region', inplace=True, drop=True)
    diff_df = diff_df.T
    diff_df.columns.name = ""
    diff_df.index.name = "Date"
    diff_df.reset_index(inplace=True)

    df.drop(['Population'], axis=1, inplace=True)
    df.set_index('Country/Region', inplace=True, drop=True)
    df = df.T
    df.columns.name = ""
    df.index.name = "Date"
    df.reset_index(inplace=True)

    return df, diff_df

def time_series_tab(df_confirmed_pop, df_dead_pop, df_recovered_pop):
    # prepare datasets
    df_conf, df_conf_diff = prepare_covid_data_timeseries(df_confirmed_pop)
    df_dead, df_dead_diff = prepare_covid_data_timeseries(df_dead_pop)
    df_reco, df_reco_diff = prepare_covid_data_timeseries(df_recovered_pop)
    
    def make_dataset(country):
        
        dates = df_conf['Date']
        confirmed = pd.Series(np.zeros(len(dates)))
        dead = pd.Series(np.zeros(len(dates)))
        recovered = pd.Series(np.zeros(len(dates)))
        confirmed_diff = pd.Series(np.zeros(len(dates)))
        dead_diff = pd.Series(np.zeros(len(dates)))
        recovered_diff = pd.Series(np.zeros(len(dates)))
        if country in df_conf.columns:  
            confirmed = df_conf[country]
            confirmed_diff = df_conf_diff[country]
        if country in df_dead.columns:  
            dead = df_dead[country]
            dead_diff = df_dead_diff[country]
        if country in df_reco.columns:  
            recovered = df_reco[country]
            recovered_diff = df_reco_diff[country]
        
        df_ts = pd.DataFrame(data={'Date':dates, 'Confirmed':confirmed, 'Deaths':dead ,'Recovered':recovered, 'ConfirmedDiff':confirmed_diff, 'DeathsDiff':dead_diff ,'RecoveredDiff':recovered_diff})
        
        return ColumnDataSource(df_ts)
    
    def make_plot(src, country_to_plot):
        
        p = figure(title=f"{country_to_plot}: Cumulative Number of Cases", 
                   y_axis_type="log", 
                   x_axis_type='datetime',
                   plot_height = 600 , plot_width = 950)
        p.title.text_font = "helvetica"
        p.title.text_font_size = "20px"
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None
        
        palette = Category20[7]  # brewer['PuBu'][9]#gray(21)
        colors = [palette[0], palette[6], palette[4]]
        cases = ['Confirmed', 'Deaths', 'Recovered']
        items = []
        for i, case in enumerate(cases):
            c = p.line('Date', case,
                   line_color=colors[i], 
                   line_width=2.5, source=src)
            point = p.circle('Date', case,
                   line_color=colors[i], fill_color=colors[i], fill_alpha=0, size=7, source=src)
            hover = HoverTool(tooltips=[("Date", "@Date{%F}"), (f"{case}", "$y")], 
                              formatters={
                                        '@Date': 'datetime'  # use 'datetime' formatter for '@date' field
                                        }, 
                              renderers=[c])
            items.append(LegendItem(label=case, renderers=[point, c]))
            p.add_tools(hover)
        
        legend = Legend(items=items, location='top_left')#, location=(0, -30))
        p.add_layout(legend, 'center')

        p.legend.location = "top_left"
        p.legend.click_policy = "hide"
        p.legend.background_fill_alpha = 0
        p.legend.border_line_alpha = 0
        p.legend.glyph_height = 20
        p.legend.glyph_width = 20
        p.legend.label_text_font_size = '20pt'
    
        p.xaxis.ticker.desired_num_ticks = 25

        p.xaxis.axis_label = 'Date'
        #p.yaxis.axis_label = 'Counts/100k inhabitants'
        p.yaxis.axis_label = 'Number of cases'
        
        return p
    
    def make_plot_diff(src, country_to_plot):
        
        p = figure(title=f"{country_to_plot}: Number of Cases Per Day Increase", 
                   #y_axis_type="log", 
                   x_axis_type='datetime',
                   plot_height = 600 , plot_width = 950)
        p.title.text_font = "helvetica"
        p.title.text_font_size = "20px"
        p.xgrid.grid_line_color = None
        p.ygrid.grid_line_color = None
        
        palette = Category20[7]  # brewer['PuBu'][9]#gray(21)
        colors = [palette[0], palette[6], palette[4]]
        cases = ['Confirmed', 'Deaths', 'Recovered']
        diffs = ['ConfirmedDiff', 'DeathsDiff', 'RecoveredDiff']
        items = []
        for i, case in enumerate(diffs):
            c = p.line('Date', case,
                   line_color=colors[i], 
                   line_width=2.5, source=src)
            point = p.circle('Date', case,
                   line_color=colors[i], fill_color=colors[i], fill_alpha=0, size=7, source=src)
            hover = HoverTool(tooltips=[("Date", "@Date{%F}"), (f"{case}", "$y")], 
                              formatters={
                                        '@Date': 'datetime'  # use 'datetime' formatter for '@date' field
                                        }, 
                              renderers=[c])
            items.append(LegendItem(label=cases[i], renderers=[point, c]))
            p.add_tools(hover)
        
        legend = Legend(items=items, location='top_left')#, location=(0, -30))
        p.add_layout(legend, 'center')

        p.legend.location = "top_left"
        p.legend.click_policy = "hide"
        p.legend.background_fill_alpha = 0
        p.legend.border_line_alpha = 0
        p.legend.glyph_height = 20
        p.legend.glyph_width = 20
        p.legend.label_text_font_size = '20pt'
    
        p.xaxis.ticker.desired_num_ticks = 25

        p.xaxis.axis_label = 'Date'
        #p.yaxis.axis_label = 'Counts/100k inhabitants'
        p.yaxis.axis_label = 'Per day increase'
        
        return p
    
    def update(attr, old, new):
        country_to_plot = country_selection.value
        new_src = make_dataset(country_to_plot)
        src.data.update(new_src.data)
        p.title.text = f'{country_to_plot}: Cumulative Number of Cases'
        p_diff.title.text = f'{country_to_plot}: Number of Cases Per Day Increase'
        
    
    cols = df_conf.columns
    countries = cols[1:].to_list()
    initial_country = 'Italy'
    country_selection = Select(title="Select Country", value=initial_country, options=countries)
    country_selection.on_change('value', update)
        
    initial_country = country_selection.value
    src = make_dataset(initial_country)
    p = make_plot(src, initial_country)
    p_diff = make_plot_diff(src, initial_country)

    
    layout = column(column(country_selection, width=200), row(p, p_diff))
    # Make a tab with the layout 
    tab = Panel(child=layout, title = 'Time Evolution')
    
    return tab