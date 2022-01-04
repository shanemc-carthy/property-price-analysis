#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 17 15:21:16 2021

@author: shanemccarthy
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 18 11:32:28 2020

@author: shanemccarthy
"""

#https://github.com/barrysmyth/data_science_in_practice/blob/master/notebooks/a_covid_19_lockdown_visualisation.ipynb
#https://medium.com/data-science-in-practice/a-covid-19-lockdown-visualisation-739f1357dad0


from datetime import date

import pandas as pd
import numpy as np

from matplotlib.pylab import plt
import matplotlib.dates as mdates

import seaborn as sns

import requests
import json

import os

os.chdir("/Users/shanemccarthy/Google Drive/Personal/Trading/Algo trading")



sns.set_style("white")
sns.set_context("paper")
dpi = 200
figsize=(15, 6)


date_range_endpoint = 'https://covidtrackerapi.bsg.ox.ac.uk/api/stringency/date-range/{from_date}/{to_date}'
from_date, today = '2019-09-01', date.today().strftime('%Y-%m-%d')


# The data we want is in a big json object under the 
r = requests.get(date_range_endpoint.format(from_date=from_date, to_date=today))
r

data = r.json()['data'] 
data['2020-04-17']['AUS'] 


df = pd.concat({k: pd.DataFrame(v).T for k, v in r.json()['data'].items()}, axis=0)
df.sample(3)


# Some cleanup - change the column names and drop some duplicated columns
# after the conversion to a df. Also change the date to a datetime data type.
df.reset_index(inplace=True)
df.drop(columns=['level_0', 'level_1'], inplace=True)
df = df.rename(columns={'confirmed': 'cases','date_value':'date','country_code':'country'})

df = df[['date', 'country', 'cases', 'deaths', 'stringency', 'stringency_actual']]

df['date'] = pd.to_datetime(df['date'])
df = df.set_index('date')

df.sample(3)


# Next we can calculate the number of days form a given date to the date of the kth case/death
df = df.reset_index().set_index('country')

# For various reasons it is going to be easier to create our graph by plotting 
# against an x-axis that is measuring an integer number of days since the first
# date in the dataset. Let's add this as a new column.
df['day'] = (df['date']-pd.to_datetime(df['date']).min()).map(lambda days: days.days)



ire =df.loc['IRL']
aus =df.loc['AUS']


# The SI levels
low_si = (df['stringency']>20) & (df['stringency']<=50)
med_si = (df['stringency']>50) & (df['stringency']<=65)
high_si = (df['stringency']>65) & (df['stringency']<=80)
vhigh_si = (df['stringency']>80)


df['si_level'] = np.where(low_si, 1, np.nan)
df['si_level'] = np.where(med_si, 2, df['si_level'])
df['si_level'] = np.where(high_si, 3, df['si_level'])
df['si_level'] = np.where(vhigh_si, 4, df['si_level'])

df.groupby('si_level').size()



# We need to sort our dataframe by the date of the first cases in a country.
# The easiest way to do this is to add a column with date of the first cases for
# each country so that we can sort by this column.

first_case_date_by_country = pd.DataFrame(df.groupby('country').apply(lambda g: g[g['cases']>0]['date'].min()), columns=['first_case_date'])

# Add these first cases dates to the main DF and sort it.
df = df.join(first_case_date_by_country).sort_values(by='first_case_date')


# And let's add corresponding day column -- the day number for the first case -- since
# we are using day numbers in our graph.
df['first_case_day'] = (df['date']-pd.to_datetime(df['first_case_date'], infer_datetime_format=True)).map(lambda td: td.days)

df.sample(3)

irl=df.loc['IRL']

# The countries to use in our graph.

# use_countries = [
#     'USA', 'FRA', 'DEU', 'FIN', 'GBR', 'SWE', 'RUS', 'ITA', 'ESP', 'BEL', 'CHE', 'HRV', 'AUT', 'ROU', 'NOR', 
#     'GRC', 'NLD', 'ISL', 'LUX', 'IRL', 'PRT', 'UKR', 'POL', 'HUN', 'SVN', 'SVK', 'SRB', 'BGR',]


#use_countries = ['AUS','NZL','SGP','CHN','TWN','HKG','JPN','VNM']
use_countries = ['CHN','JPN','TWN','USA','HKG','SGP','VNM','AUS','ITA','SWE','NZL']

stringency_palette = sns.color_palette("coolwarm", 41)

stringency_cmap = [stringency_palette[15], stringency_palette[25], stringency_palette[35], stringency_palette[40]]
sns.palplot(stringency_cmap)
date_interval = 14
df['date'].unique()[::date_interval]



# Now generate the date labels from these dates, by combining the month name and the day.
date_labels = [
    '{} {}'.format(pd.to_datetime(d).month_name()[:3], str(pd.to_datetime(d).day)) 
    for d in sorted(df['date'].unique())[::date_interval]
]

date_labels

stringency_for_country_by_date = df\
    .reset_index()\
    .set_index(['country', 'day'])['si_level']\
    .unstack()\
    .T.ffill().T


stringency_for_country_by_date.loc[['IRL', 'AUS', 'NZL']]

# For this heatmap want a matrix with a 1 in the cell for a country when the first case occured.
first_cases_for_country_by_date = df\
    .reset_index()\
    .set_index(['country', 'day'])['first_case_day']\
    .unstack()\
    .applymap(lambda n: 1 if n==0 else np.nan)  # We only mark the day of the first case; everything else is NaN.
    
    # We only mark the day of the first case; everything else is NaN.

first_cases_for_country_by_date.loc[['CHN', 'ITA', 'USA', 'ESP', 'IRL']].dropna(axis=1, how='all')



# Test a simple heatmap for using the SI dataframe for a sample
# of 10 countries

fig, ax = plt.subplots(figsize=(10, len(use_countries[:10])*.5))

sns.heatmap(stringency_for_country_by_date.loc[use_countries[:10]], ax=ax, cbar=True)



fig, ax = plt.subplots(figsize=(10, len(use_countries[:10])*.5))

sns.heatmap(first_cases_for_country_by_date.loc[use_countries[:10]], ax=ax, cbar=True)


sns.set_context('poster', font_scale=1)

fig, ax = plt.subplots(figsize=(30, len(use_countries)*1.5))



# ----------------------------
# The Stringency Index Heatmap
# ----------------------------

# For maximum flexibility we use a separate axis to plot the heatmap's 
# colour bar (horizontally) as the SI legend.
cbar_ax = fig.add_axes([.15, .17, .38, 3/len(stringency_for_country_by_date)])

# The heatmap itself is straightfoward with one caveat: after much fiddling I had to
# set its xticklabels parameter to the date interval we are using.
sns.heatmap(stringency_for_country_by_date.loc[use_countries], ax=ax, 
            linewidths=2, cmap=stringency_cmap, cbar=True, xticklabels=date_interval, zorder=10, 
            cbar_ax=cbar_ax, cbar_kws=dict(orientation='horizontal', ticks=[])
           )


# ----------------------------
# The First Cases Heatmap
# ----------------------------

# The first cases plot doesn't look like a heatmap. It looks like a variation of a
# line graph, but this doesn't work. Notice that the first case markers for each country 
# are not regular matplotlib markers, they are vertical lines that align and match with the
# the SI cells.

bx = ax.twinx()  # We need a duplicate axis

# The first cases heatmap
sns.heatmap(first_cases_for_country_by_date.loc[use_countries], ax=ax, 
            linewidths=.15, cmap=['k'], cbar=False, xticklabels=14, zorder=10)


# ----------------------------
# Axes, labels &  grid-lines
# ----------------------------

ax.set_xticklabels(date_labels)

# We want a duplicate x axis on the top too.
ax2 = ax.twiny()
ax2.set_xticks(ax.get_xticks())
ax2.set_xticklabels(ax.get_xticklabels())

# Remove axes ticks
ax.tick_params(axis='both', length = 0)
ax2.tick_params(axis='both', length = 0)

# Draw the vertical gridlines
ax.grid(axis='x', lw=2)

# We dont need labels for the x axes.
ax.set_xlabel('')
ax.set_ylabel('')

# Shift the y axis labels to the right-hand side.
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontweight='bold')
ax.yaxis.tick_right()

# We don't need the y-axis ticks/labels for teh second y-axis.
bx.set_yticks([])
bx.set_yticklabels([])

ax.set_xlim(14)
bx.set_xlim(14)

# Remove the frame around the plot
sns.despine(left=True, bottom=True, right=True)

# A title for the SI legend.
bx.annotate('Stringency Index', xy=(.04, .1), xycoords='axes fraction', fontweight='bold')

# The SI legend category labels.
for (x, label) in zip(np.arange(0, 1, .25), ['Low', 'Moderate', 'High', 'Very High']):
    cbar_ax.annotate(
        label, xy=(x+.01, .3), 
        xycoords='axes fraction', 
        fontsize=15, fontweight='bold', color='white'
    )


# A title for the graph.
ax.set_title('Countries in Lockdown (2020)\n', fontweight='bold', loc='left')
fig.savefig('bbc_stringency_index.png', format='png', dpi=200)


df.to_pickle('covid_'+today)
