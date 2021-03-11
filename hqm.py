#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import pandas as pd
import requests
import numpy as np
import math
from scipy import stats
from himitsu import TOKEN
from statistics import mean


# In[ ]:


stocks = pd.read_csv("s&p500.csv")


# In[ ]:


symbol = "NKE"
api_url = f"https://sandbox.iexapis.com/stable/stock/{symbol}/stats?token={TOKEN}"
data = requests.get(api_url).json()
data


# In[ ]:


def hoge(lst,n):
    for i in range(0,len(lst),n):
        yield lst[i:i + n]
        
symbol_groups = list(hoge(stocks["Ticker"],100))
symbol_strings = [] # empty list which will be filled with stocks
for i in range(0,len(symbol_groups)):
    symbol_strings.append(",".join(symbol_groups[i]))
    
my_columns = ["Ticker","Price","One-Year Price Return","Number of Shares to Buy"]


# In[ ]:


final_dataframe = pd.DataFrame(columns = my_columns)

for symbol_string in symbol_strings:
    batch_api_call_url = f'https://sandbox.iexapis.com/stable/stock/market/batch/?types=stats,quote&symbols={symbol_string}&token={TOKEN}'
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(','):
        final_dataframe = final_dataframe.append(
                                        pd.Series([symbol, 
                                                   data[symbol]['quote']['latestPrice'],
                                                   data[symbol]['stats']['year1ChangePercent'],
                                                   'N/A'
                                                   ], 
                                                  index = my_columns), 
                                        ignore_index = True)
        
    
final_dataframe


# # Extracting only high momentum stocks

# (How): remove unqualified stocks in the DataFrame
# (ToDo): "sort" the DataFrame with "one-year price return", then specifiy top 50 stocks

# In[ ]:


final_dataframe.sort_values("One-Year Price Return",ascending=False,inplace=True)
final_dataframe = final_dataframe[:51] # modify the original dataframe with new one of top 50 stocks
final_dataframe.reset_index(drop=True,inplace=True)
final_dataframe


# In[ ]:


def portfolio_input():
    global portfolio_size
    portfolio_size = input("How big is your PF:")
    
    try:
        val = float(portfolio_size)
    except ValueError:
        print("Error:It is not number")
        portfolio_size = input("Enter the value of your portfolio")
        
portfolio_input()
print(portfolio_size)


# In[ ]:


position_size = float(portfolio_size) / len(final_dataframe.index)
for i in range(0,len(final_dataframe["Ticker"])):
    final_dataframe.loc[i,"Number of Shares to Buy"] = math.floor(position_size / final_dataframe["Price"][i])
final_dataframe


# In[ ]:


hqm_columns = [
    "Ticker",
    "Price",
    "Number of Shares to Buy",
    "One-Year Price Return",
    "One-Year Return Percentile",
    "Six-Month Price Return",
    "Six-Month Return Percentile",
    "Three-Month Price Return",
    "Three-Month Return Percentile",
    "One-Month Price Return",
    "One-Month Return Percentile",
    "HQM Score"
]

hqm_dataframe = pd.DataFrame(columns = hqm_columns)

for symbol_string in symbol_strings:
    batch_api_call_url = f"https://sandbox.iexapis.com/stable/stock/market/batch/?types=stats,quote&symbols={symbol_string}&token={TOKEN}"
    data = requests.get(batch_api_call_url).json()
    for symbol in symbol_string.split(","):
        hqm_dataframe = hqm_dataframe.append(
        pd.Series([symbol,
                   data[symbol]["quote"]["latestPrice"],
                   "N/A",
                   data[symbol]["stats"]["year1ChangePercent"],
                   "N/A",
                   data[symbol]["stats"]["month6ChangePercent"],
                   "N/A",
                   data[symbol]["stats"]["month3ChangePercent"],
                   "N/A",
                   data[symbol]["stats"]["month1ChangePercent"],
                   "N/A",
                   "N/A"
                  ],
                 index = hqm_columns),
        ignore_index = True)
        
hqm_dataframe.columns


# # Calculation for momentum %

# In[ ]:


time_periods = [
                'One-Year',
                'Six-Month',
                'Three-Month',
                'One-Month'
                ]

for row in hqm_dataframe.index:
    for time_period in time_periods:
        hqm_dataframe.loc[row, f'{time_period} Return Percentile'] = stats.percentileofscore(hqm_dataframe[f'{time_period} Price Return'], 
        hqm_dataframe.loc[row, f'{time_period} Price Return'])/100

# Print each percentile score to make sure it was calculated properly
for time_period in time_periods:
    print(hqm_dataframe[f'{time_period} Return Percentile'])

#Print the entire DataFrame    
hqm_dataframe


# # Calculation for High Quality Momentum score

# (Why): to filter stocks

# In[ ]:


for row in hqm_dataframe.index:
    momentum_percentiles = []
    for time_period in time_periods:
        momentum_percentiles.append(hqm_dataframe.loc[row, f"{time_period} Return Percentile"])
    hqm_dataframe.loc[row,"HQM Score"] = mean(momentum_percentiles)


# In[ ]:


hqm_dataframe.sort_values(by = "HQM Score",ascending=False)
hqm_dataframe = hqm_dataframe[:5]


# In[ ]:


portfolio_input()


# In[ ]:


position_size= float(portfolio_size) / len(hqm_dataframe.index)
for i in range(0, len(hqm_dataframe["Ticker"])-1):
    hqm_dataframe.loc[i, "Number of Shares to Buy"] = math.floor(position_size / hqm_dataframe["Price"][i])
hqm_dataframe

