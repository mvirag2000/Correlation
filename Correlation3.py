import pandas as pd
import numpy as np
import util as u
from bokeh.plotting import figure
from bokeh.io import show, output_file  
from bokeh.layouts import column, row, grid 
from bokeh.models import Label, ColumnDataSource 
from bokeh.models.widgets import DataTable, TableColumn, StringFormatter, Paragraph, Div
from scipy import stats 
from pandas_datareader import data
import datetime
import math

start = datetime.datetime(2014,1,1) #DBC starts 2/1/06 
end = datetime.datetime(2019,1,1)
stocks = ['AGG', 'TLT', 'EEM', 'IWM', 'IYR', 'DBC', 'GLD'] #Best small group with low correlation 
#stocks = ['SPY', 'EFA', 'IEF', 'TIP', 'EEM', 'IWM', 'XLB', 'IYR', 'TLT', 'GLD', 'AGG', 'RSP', 'DBC', 'IYM'] #Full set of all relevant symbols
#stocks = ['EEM', 'EFA', 'IEF', 'IWM', 'IYR', 'SPY', 'TIP', 'TLT', 'XLB'] #Group from my original 2014 study 
ref_stocks = ['SPY', 'TIP']
g=data.get_data_yahoo(stocks, start, end, interval='m') 
price = g['Close']
g=data.get_data_yahoo(ref_stocks, start, end, interval='m')
lookback = 3
ref_price = g['Close']
ref_price['Date'] = pd.to_datetime(ref_price.index)
ref_price.insert(0, 'ID', range(0, ref_price.shape[0]))
ref_price['SPY_Bal'] = ref_price['SPY'] * 10000 / ref_price['SPY'][lookback]
#print(ref_price)
#u.print_stats(price)

#Delta = DF of monthly differentials with fixed one-period lookback
delta = pd.DataFrame(index=price.index, columns=price.columns)
for c in price.columns:
    delta[c] = price[c].pct_change()  
#print(delta)

#Delta3 = delta DF with variable lookback 
delta3 = pd.DataFrame(index=price.index, columns=price.columns)
for c in price.columns:
    delta3[c] = price[c].pct_change(periods=lookback)
print(delta3)

#Winners = DF of positive returns
winners = pd.DataFrame(index=delta3.index, columns=delta3.columns)
for c in delta3.columns:
    winners[c] = delta3[c][delta3[c]>0]
winners.fillna(0, inplace=True)
winners['Total'] = winners.sum(axis=1)
#print(winners)

#Alloc = DF of pro-rata winners
alloc = pd.DataFrame(index=delta3.index, columns=delta3.columns)
for c in delta3.columns:
    alloc[c] = winners[c] / winners['Total']    #What if they're all losers?
#alloc.fillna(1 / delta3.shape[1], inplace=True) #Allocate evenly?
alloc.fillna(method='ffill', inplace=True)      #Use previous row 
print(alloc)

#Distro = DF average allocation to each issue
distro = pd.DataFrame(alloc.mean())
distro.columns = ['Alloc']
distro.sort_values(by='Alloc', inplace=True, ascending=False) 
distro['Symbol'] = distro.index
#print(distro)

#Model_tab = NP of allocations (in period t) and returns (period t+1) 
rows = alloc.shape[0] - lookback - 1
columns = delta3.shape[1]
model_alloc = np.empty(shape=[rows, columns])
model_return = np.empty(shape=[rows, columns])
i = 0
balance = 10000
for row in alloc.index[lookback:-1]:
    j = 0
    for c in alloc.columns:
        model_alloc[i, j] = alloc.loc[row, c] * balance
        j +=1
    j = 0
    balance = 0
    for c in delta.columns:
        model_return[i, j] = model_alloc[i, j] * (1 + delta.loc[row + pd.DateOffset(months=1), c])
        balance += model_return[i, j]
        j += 1
    i += 1
model_return = np.insert(model_return, 0, model_alloc[0,:], axis=0)
model = pd.DataFrame(model_return, columns=delta.columns, index=delta.index[lookback:])
model['End_Bal'] = model.sum(axis=1)
model['Mo_Chg'] = model['End_Bal'].pct_change()

drawdown = np.empty(shape=[model.shape[0]])
i = 1
drawdown[0] = 0
for row in model.index[1:]: 
    drawdown[i] = min(0, model.loc[row, 'Mo_Chg'] + drawdown[i-1])
    i += 1
model['DD'] = drawdown
print(model)

#Rank = DF rank among returns in each month  
rank = delta3.rank(method='max', axis=1, ascending=False)
#print(rank)

#Rank_tab = DF of delta columns by rank
#rank_tab = pd.DataFrame(index=price.index[lookback:], columns=range(1, len(stocks)+1))
#i = 0
#for row in rank.index[lookback:]:  #need to skip NaN rows but keep correct dates    
#    for c in rank.columns:
#        j = int(rank.loc[row, c]-1)
#        rank_tab.iloc[i, j] = c  #there is no pythonic way to do this  
#    i += 1
#print(rank_tab)

#Return_tab = NP of next month's return by rank
rows = rank.shape[0] - lookback - 1
ranks = rank.shape[1]
return_tab = np.empty(shape=[rows, ranks]) 
i = 0
s = rank.shape[0] - 1
for row in rank.index[lookback:s]:
    for c in rank.columns:
        j = int(rank.loc[row, c]-1)
        return_tab[i, j] = delta.loc[row + pd.DateOffset(months=1), c]
    i += 1
#print(return_tab)

#Average returns by rank
avg_return = np.average(return_tab, axis=0)
#print(avg_return)

#Corr_Tab = NP of rolling pairwise correlations
rows = delta.shape[0]
symbols = delta.shape[1] 
i = 0
corr_tab = np.empty(shape=[rows, symbols**2])
for c1 in delta.columns:
    for c2 in delta.columns:
        corr_tab[:,i] = delta[c1].corr(delta[c2])
        i += 1 

#Corr_Grid = DF of average pairwise correlations 
corr_grid = pd.DataFrame(index=price.columns, columns=price.columns)
i = 0
for c1 in delta.columns:
    for c2 in delta.columns:
        corr_grid[c1][c2] = int (100 * corr_tab[:,i].mean())
        i += 1

corr_grid['Mean'] = (corr_grid.sum(axis=1) - 100) / (symbols - 1)
corr_grid.insert(0, 'Symbol', corr_grid.index)
columns = [TableColumn(field = c, title = c) for c in corr_grid.columns]
corr_grid_display = DataTable(source=ColumnDataSource(corr_grid), columns=columns, width=600, height=280)

model_gain = model['End_Bal'][-1] / model['End_Bal'][lookback] - 1 
spy_gain = ref_price['SPY_Bal'][-1] / ref_price['SPY_Bal'][lookback] - 1 
months = model.shape[0] - lookback 
CAGR = (model['End_Bal'][-1] / model['End_Bal'][lookback])**(12/months) - 1 
tip_CAGR = (ref_price['TIP'][-1] / ref_price['TIP'][lookback])**(12/months) - 1 
stdev = model['Mo_Chg'].std() * math.sqrt(months/12) #Annualize monthly stdev 
Sharpe = (CAGR - tip_CAGR) / stdev 

returns = pd.DataFrame()
returns['Return'] = avg_return
returns['Rank'] = returns.index + 1
x = returns['Rank']
y = returns['Return']
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y) 
returns['Pred'] = returns['Rank'] * slope + intercept

string1 = "<b>Momentum-Based Balancing <br>{:%a %b %d, %Y, %I:%M %p } </b><br>".format(datetime.datetime.now())
string1 += "Number of symbols: " + str(symbols) + "<br>"  
string1 += "Test period: {:%b %d %Y} ".format(start)
string1 += "to {:%b %d %Y} ".format(end)
string1 += "with " + format(lookback, "1.0f") + " months lookback<br>" 
string1 += "Total of " + format(model.shape[0], "1.0f") + " months<br>"
string1 += "<br>" #Result variables below 
string1 += "Average correlation among symbols: %.1f <br>" % corr_grid['Mean'].mean()
string1 += "R-Square of rank as predictor: %1.3f <br>" % (r_value * r_value) 
string1 += "Model gain (loss): %1.3f <br>" % model_gain
string1 += "Max drawdown: %1.3f <br>" % model['DD'].min() 
string1 += "Market gain (loss): %1.3f <br>" % spy_gain
string1 += "Model CAGR: %1.3f <br>" % CAGR
string1 += "Sharpe Ratio: %1.3f <br>" % Sharpe 
para1 = Div(text=string1, width=450) 

title = "Rank for past " + format(lookback, "1.0f") + " months, R-Square = " + format(r_value * r_value, "1.3f")
s1 = figure(plot_width=450, plot_height=420, title=title)
s1.vbar(returns['Rank'], width=0.5, top=returns['Return'])
s1.line(returns['Rank'], returns['Pred'], line_color = 'red')
s1.xaxis.axis_label = 'Symbol Rank'
s1.yaxis.axis_label = 'Following Month Return'

s2 = figure(x_range=distro['Symbol'], plot_width=450, plot_height=420, title="Average Allocation by Symbol")
s2.vbar(distro['Symbol'], width=0.5, top=distro['Alloc'])

mp = figure(plot_width=650, plot_height=420, title="Model Performance")
dd = figure(plot_width=650, plot_height=420, title="Drawdown") 
mp.xaxis.major_label_overrides = {
    i: date.strftime('%b %y') for i, date in enumerate(pd.to_datetime(ref_price['Date']))
}
dd.xaxis.major_label_overrides = {
    i: date.strftime('%b %y') for i, date in enumerate(pd.to_datetime(ref_price['Date']))
}
ref_price.drop(ref_price.index[:lookback], inplace=True)
mp.line(ref_price['ID'], ref_price['SPY_Bal'], line_color='red', legend="SPY")
mp.line(ref_price['ID'], model['End_Bal'], line_color='black', legend="Model") 
mp.legend.location = "top_left"
dd.line(ref_price['ID'], model['DD'], line_color='red')

output_file('chart.htm')
l = grid([
    [para1, corr_grid_display],
    [s1, mp],
    [s2, dd]
])
show(l, browser=None) 