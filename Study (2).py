import pandas as pd
from bokeh.io import output_file, show
from bokeh.layouts import column, row
from bokeh.plotting import figure
from bokeh.models.widgets.sliders import Slider
import numpy as np
import util as u
from pandas_datareader import data
import datetime

start = datetime.datetime(2010,1,1)
end = datetime.datetime(2017,7,13)
stocks = ['SPY', 'XLI', 'XLB', 'XLE', 'XLU', 'XLF', 'XLV', 'XLY', 'XLP', 'XLK']
g=data.DataReader(stocks, 'google', start, end)
price = g['Close']
#price = pd.read_csv('F:\Stock Market\Ziggy Lines\Correlation\Including SPY.csv',encoding = 'mbcs',index_col=0)
u.print_stats(price)

w = 20 #rolling correlation window
s = 5 #SMA smoothing interval 
lo = 60 #low correlation threshold 

spy = price['SPY'].copy()
price = price.drop('SPY', 1)

delta = pd.DataFrame(index=price.index, columns=price.columns)
for c in price.columns:
    delta[c] = price[c].pct_change()
days = delta.shape[0]
symbols = delta.shape[1]
i = 0
corr_tab = np.empty(shape=[days, symbols**2])
for c1 in delta.columns:
    for c2 in delta.columns:
        corr_tab[:,i] = delta[c1].rolling(window=w).corr(delta[c2])
        i += 1 
avg_corr = pd.DataFrame(index=delta.index, columns=['Correlation'])
avg_corr['Correlation'] = 100 * (corr_tab.sum(axis=1) - symbols) / 2 / u.pairs(symbols)
avg_corr['SPY'] = spy
avg_corr['Date'] = pd.to_datetime(avg_corr.index)
avg_corr['Smooth SPY'] = avg_corr['SPY'].rolling(window=s).mean()
avg_corr['Smooth Corr'] = avg_corr['Correlation'].rolling(window=s).mean()
avg_corr = avg_corr.iloc[w+s:,:] #truncate the wasted w+s days
avg_corr.loc[avg_corr['Correlation'] <= lo, 'Low'] = True 

box = avg_corr.loc[:,['Date', 'Low']]
box = box[box['Low'] == True] 
top = avg_corr['SPY'].max()
bottom = avg_corr['SPY'].min()
box['Top'] = top
box['Bottom'] = bottom
box['Right'] = box['Date'] + pd.DateOffset(2)

s1 = figure(plot_width=940, plot_height=420, title='SPY', x_axis_type='datetime')

#Examine deltas directly
#for i in delta.columns:
#    delta[i] = delta[i].rolling(window=s).mean()
#delta = delta.iloc[w+s:,:]
#s1.multi_line(xs=[delta.index.values]*9, ys=[delta[name].values for name in delta], 
#    color=['red','firebrick','orange','yellow', 'blue','green','gray','indigo','violet'])
s1.line(avg_corr['Date'], avg_corr['Smooth SPY'], line_color='red')
s1.quad(left=box['Date'], right=box['Right'], top=box['Top'], bottom=box['Bottom'],
        color='grey', alpha=0.2)

s2 = figure(plot_width=940, plot_height=150, title='Correlation', x_axis_type='datetime')
s2.line(avg_corr['Date'], avg_corr['Smooth Corr'], line_color='blue')
s2.line(avg_corr['Date'], lo, line_color='black')

show(column(s1, s2))
