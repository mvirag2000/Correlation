import pandas as pd
from bokeh.io import output_file, show
from bokeh.layouts import column
from bokeh.plotting import figure
import numpy as np
import virag as v
from pandas.io.pytables import IndexCol
from pandas.io.tests.parser import index_col
w = 20
price = pd.read_csv('F:\Stock Market\Ziggy Lines\Correlation\Including SPY2.csv',encoding = 'mbcs',index_col=0)
#v.print_stats(price)
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
        i = i + 1 
avg_corr = pd.DataFrame(index=delta.index, columns=['Correlation'])
avg_corr['Correlation'] = 100 * (corr_tab.sum(axis=1) - symbols) / 2 / v.pairs(symbols)
avg_corr['SPY'] = spy
avg_corr['Date'] = pd.to_datetime(avg_corr.index)
avg_corr = avg_corr.iloc[w:,:]

s1 = figure(plot_width=940, plot_height=400, title='SPY', x_axis_type='datetime')
s1.line(avg_corr['Date'], avg_corr['SPY'], line_color='red')

s2 = figure(plot_width=940, plot_height=150, title='Correlation', x_axis_type='datetime')
s2.line(avg_corr['Date'], avg_corr['Correlation'], line_color='blue')

show(column(s1, s2))
