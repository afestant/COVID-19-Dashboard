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


def map_tab(map_cov, map_df, min_density, max_density):

    # Input GeoJSON source that contains features for plotting.
    geosource = GeoJSONDataSource(geojson=map_cov)
    
    palette = RdYlGn[11]
    low = min_density
    high = max_density
    color_mapper = LogColorMapper(palette = palette, low =low, high = high, nan_color = 'whitesmoke', low_color='whitesmoke')
    
    #Create color bar. 
    color_bar = ColorBar(color_mapper=color_mapper, location = (0,0), 
                         orientation = 'horizontal', ticker=LogTicker(), border_line_color=None, title='Density of confirmed cases')
    
    #Create figure object.
    p = figure(title = 'COVID-19 spread map', plot_height = 900 , plot_width = 1500, toolbar_location='below',
               toolbar_sticky=False, background_fill_color="whitesmoke")
    p.title.text_font = "helvetica"
    p.title.text_font_size = "20px"
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    
    #Add patch renderer to figure. 
    patches = p.patches('xs','ys', source = geosource, 
                        fill_color = {'field' :'ConfirmedDensity', 'transform' : color_mapper},
                        line_color = 'black', 
                        line_width = 0.25, 
                        fill_alpha = 0.5)
    
    p.renderers.append(patches)
    #Specify figure layout.
    p.add_layout(color_bar, 'below')
    
    #create hoover
    hover = HoverTool(tooltips=[('Country', '@{NAME_EN}'), ('Population', '@Population'), ('Confirmed', '@Confirmed'),
                              ('Deaths', '@Deaths'), ('Recovered', '@Recovered'), ('Conf. density', '@ConfirmedDensity'),
                              ('Deaths density', '@DeathsDensity'), ('Recovered density', '@RecoveredDensity')], renderers=[patches])
    p.add_tools(hover)
    
       
    # Input coronavirus data
    pointsource = ColumnDataSource(map_df)
    
    # color palette
    # palette_p = brewer['Blues'][9]
    # palette_p = palette_p[::-1]
    # palette_p[1::]
    # color_mapper_p = LinearColorMapper(palette=palette_p, low=0, high=17)

     # add points virus
    point = p.circle('Long', 'Lat', source=pointsource, size='Size', 
                    #color={'field': 'Size','transform': color_mapper_p}, 
                    color = 'lightskyblue',
                    fill_alpha=0.3, line_alpha=0.3)
    
    p.renderers.append(point)
    # create hoover
    hover_p = HoverTool(tooltips=[('Country', '@{Country/Region}'), ('Province', '@{Province/State}'), ('Confirmed', '@Confirmed'),
                             ('Deaths', '@Deaths'), ('Recovered', '@Recovered')], renderers=[point])
    p.add_tools(hover_p)
    
    # Add legend at fixed positions
    location, orientation, side = 'bottom_left', "horizontal", "center"
    legend = Legend(
                items=[("Nr. of confirmed cases", [point])],
                location=location, orientation=orientation,
                border_line_color="black",
                background_fill_alpha=0,
                border_line_alpha=0
             )
    p.add_layout(legend, side)    

    
    # Layout setup
    layout = p
    tab = Panel(child = layout, title = 'COVID-19 Map')

    return tab