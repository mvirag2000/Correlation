import pandas as pd
from bokeh.io import output_file, show, reset_output
from bokeh.layouts import column, row
from bokeh.plotting import figure, output_server, curdoc
from bokeh.models import CustomJS, ColumnDataSource
from bokeh.models.widgets.inputs import Slider
import numpy as np
from pandas.io.pytables import IndexCol
from pandas.io.tests.parser import index_col
from bokeh.command.subcommands import serve
price = pd.read_csv('F:\Stock Market\Ziggy Lines\Correlation\Including SPY2.csv',encoding = 'mbcs',index_col=0)
spy = price['SPY'].copy()
price = price.drop('SPY', 1)
delta = pd.DataFrame(index=price.index, columns=price.columns)
s = 5
w = 20
t = 60
for c in price.columns:
    delta[c] = price[c].pct_change()
    
def pairs(n):
    """Number of times n people clink glasses when toasting"""
    return n * (n-1) / 2
    
def correlator(w):
    global delta
    days = delta.shape[0]
    symbols = delta.shape[1]
    i = 0
    corr_tab = np.empty(shape=[days, symbols**2])
    for c1 in delta.columns:
        for c2 in delta.columns:
            corr_tab[:,i] = delta[c1].rolling(window=w).corr(delta[c2])
            i += 1 
    avg_corr = pd.DataFrame(index=delta.index, columns=['Correlation'])
    avg_corr['Correlation'] = 100 * (corr_tab.sum(axis=1) - symbols) / 2 / pairs(symbols)
    avg_corr['Date'] = pd.to_datetime(avg_corr.index)
    return(avg_corr)

def smoother(s):
    global avg_corr
    #avg_corr['Smooth SPY'] = avg_corr['SPY'].rolling(window=s).mean()
    avg_corr['Smooth Corr'] = avg_corr['Correlation'].rolling(window=s).mean()
    return()
    
def boxer(lo):
    global avg_corr
    min = avg_corr['SPY'].min()
    max = avg_corr['SPY'].max()
    avg_corr.loc[avg_corr['Smooth Corr'] <= lo, 'Low'] = True 
    box = avg_corr.loc[:,['Low']]
    box['Date'] = pd.to_datetime(box.index)
    box = box[box['Low'] == True] 
    box['Top'] = max
    box['Bottom'] = min
    box['Right'] = box['Date'] + pd.DateOffset(2)
    return(box)

lookback = Slider(start=10, end=30, value=w, step=5, title="Lookback")
smooth = Slider(start=1, end=10, value=s, step=2, title="Smooth")
threshold = Slider(start=50, end=70, value=t, step=5, title="Threshold")

def corr_handler(attr, old, new):
    w = lookback.value
    avg_corr = correlator(w)
    smooth_handler(s)
       
def smooth_handler(attr, old, new):   
    s = smooth.value
    avg_corr['SPY'] = spy
    smoother(s)
    s2.line(avg_corr['Date'], avg_corr['Smooth Corr'], line_color='blue') 
    box_handler(t)
    
def box_handler(attr, old, new):
    t = threshold.value 
    box = boxer(t)
    s1.quad(left=box['Date'], right=box['Right'], top=box['Top'], bottom=box['Bottom'], color='grey', alpha=0.3)
    
lookback.on_change('value', corr_handler)
threshold.on_change('value', box_handler)
smooth.on_change('value', smooth_handler)

s1 = figure(plot_width=940, plot_height=420, title='SPY', x_axis_type='datetime')
s2 = figure(plot_width=940, plot_height=150, title='Correlation', x_axis_type='datetime')

avg_corr = correlator(w)
avg_corr['SPY'] = spy
smoother(s)
box = boxer(t)

cs = ColumnDataSource(avg_corr)

s1.line(source=cs, x='Date', y='SPY', line_color='red')
s1.quad(left=box['Date'], right=box['Right'], top=box['Top'], bottom=box['Bottom'], color='grey', alpha=0.3)
#s2.line(avg_corr['Date'], avg_corr['Smooth Corr'], line_color='blue') 
#s2.line('Date', 'Smooth Corr', source=corr_source, line_color='blue') 
s2.line(source=cs, x='Date', y='Smooth Corr', line_color='blue') 
curdoc().add_root(column(s1, row(lookback, smooth, threshold), s2))

