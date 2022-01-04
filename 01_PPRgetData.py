# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
#Useful links https://tomaugspurger.github.io/modern-7-timeseries.html

import pandas as pd
import numpy as np
import os 
import requests, zipfile, io
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import re
plt.style.use('ggplot')

sns.set(style='ticks', context='talk')

if int(os.environ.get("MODERN_PANDAS_EPUB", 0)):
    import prep # noqa

# set working dir
path = "/Users/shanemccarthy/Google Drive/Personal/ProjectM/buyer_dashboard/data"
os.chdir(path)
os.getcwd()


# downlaod PPR data
zip_file_url='https://www.propertypriceregister.ie/website/npsra/ppr/npsra-ppr.nsf/Downloads/PPR-ALL.zip/$FILE/PPR-ALL.zip'
r = requests.get(zip_file_url,verify=False)
z = zipfile.ZipFile(io.BytesIO(r.content))
z.extractall()

# read in as pandas object 
path = 'PPR-ALL.csv'
df = pd.read_csv(path,encoding='latin1')
df.columns = ['sale_date_dt','address','post_code','county','price','full_market','vat_excl','property_desc','size_desc']

#convert saledate to datetime
df['sale_date'] =pd.to_datetime(df['sale_date_dt'],dayfirst=True)
del df['sale_date_dt']

#calculate week number 
df['week_number']=df['sale_date'].dt.week


#only keep date part of the datetime
df['sale_date']= df['sale_date'].dt.date

# extract month and year from date - creating month_year
df['year'] = pd.DatetimeIndex(df['sale_date']).year
df['month'] = pd.DatetimeIndex(df['sale_date']).month
df['month_year'] = pd.to_datetime(df['sale_date']).dt.to_period('M')

 
# tidy up price field 
df['price_string'] =df['price'].str[1:]
df['price_string'] =df['price_string'].str.replace(',', '')
df['price']= pd.to_numeric(df['price_string'])
del  df['price_string']


# create a row id 
df["id"] = df.index + 1


# check the shape of the file
print (df.dtypes)
df.shape
df.head(5)


def check_freq(var):
    prop1 =var.value_counts()
    prop2 = var.value_counts()/len(df)
    return prop1, prop2

check_freq(df.full_market)
check_freq(df.property_desc)
check_freq(df.vat_excl)

#add logic to add vat to price




# tidy up dirty data 
df['post_code'] = df['post_code'].str.replace('Baile Átha Cliath', 'Dublin')
df['post_code'] = df['post_code'].str.replace('BAILE ÁTHA CLIATH', 'DUBLIN')
df['post_code']=df['post_code'].fillna('OTHER')


df['address']=df['address'].apply(lambda x: x.upper())
df['post_code']=df['post_code'].apply(lambda x: x.upper())
df['county']=df['county'].apply(lambda x: x.upper())


df['property_desc'] = df['property_desc'].str.replace('Second-Hand Dwelling house /Apartment', 'SECOND-HAND')
df['property_desc'] = df['property_desc'].str.replace('New Dwelling house /Apartment', 'NEW')
df['property_desc'] = df['property_desc'].str.replace('Teach/Árasán Cónaithe Atháimhe', 'SECOND-HAND')
df['property_desc'] = df['property_desc'].str.replace('Teach/Árasán Cónaithe Nua', 'NEW')
df['property_desc'] = df['property_desc'].str.replace('Teach/?ras?n C?naithe Nua', 'NEW')

# list dublin postcodes 
dub_pc =('DUBLIN 24', 'DUBLIN 23', 'DUBLIN 22', 'DUBLIN 21', 'DUBLIN 20', 'DUBLIN 19', 'DUBLIN 18', 'DUBLIN 17', 
         'DUBLIN 16', 'DUBLIN 15', 'DUBLIN 14', 'DUBLIN 13', 'DUBLIN 12', 'DUBLIN 11', 'DUBLIN 10', 'DUBLIN 9', 
         'DUBLIN 8', 'DUBLIN 7', 'DUBLIN 6', 'DUBLIN 6W','DUBLIN 5', 'DUBLIN 4', 'DUBLIN 3', 'DUBLIN 2', 'DUBLIN 1') 


# list dublin postcodes 
north =( 'DUBLIN 23','DUBLIN 21','DUBLIN 19','DUBLIN 17','DUBLIN 15','DUBLIN 13','DUBLIN 11','DUBLIN 9','DUBLIN 7','DUBLIN 5','DUBLIN 3','DUBLIN 1') 

# list dublin postcodes 
south =('DUBLIN 24','DUBLIN 22','DUBLIN 20','DUBLIN 18','DUBLIN 16','DUBLIN 14','DUBLIN 12','DUBLIN 10','DUBLIN 8','DUBLIN 6','DUBLIN 6W','DUBLIN 4','DUBLIN 2') 



# serach for dublin postcodes in address string
pattern = '|'.join(dub_pc)


def pattern_searcher(search_str:str, search_list:str):

    search_obj = re.search(search_list, search_str)
    if search_obj :
        return_str = search_str[search_obj.start(): search_obj.end()]
    else:
        return_str = 'NA'
    return return_str

df['matched_str'] = df['address'].apply(lambda x: pattern_searcher(search_str=x, search_list=pattern))


# where a postcode can be found in the address field take this and impute 
def imputer(row):
    if row['post_code'] == 'OTHER' and row['matched_str'] != 'NA':
        val = row['matched_str']
        
    elif row['post_code'] != 'OTHER':
        val = row['post_code']
    else:
        val = 'OTHER'
    return val

df['postcode'] = df.apply(imputer, axis=1)

# drop intrium fields
del df['post_code']
del df['matched_str']


# group postcodes into north south and other
def sider(row):
    if row['postcode'] in north:
        val = 'NORTH'
        
    elif row['postcode'] in south:
        val = 'SOUTH'
    else:
        val = 'OTHER'
    return val
df['postcode_group'] = df.apply(sider, axis=1)


#check postcode freq
df.postcode.value_counts()
# 339987 non dublin
df['postcode'] = df['postcode'].str.replace('NÍ BHAINEANN ', 'OTHER')
df['postcode'] = df['postcode'].str.replace('BAILE ?THA CLIATH 17 ', 'DUBLIN 17')


#plot grouping 

def pg(row):
    if row['postcode'] != 'OTHER':
        val = row['postcode'] 
        
    elif row['postcode'] == 'OTHER':
        val = row['county']

    return val
df['plot_group'] = df.apply(pg, axis=1)

df.plot_group.value_counts()

# now lets do some plots 


pgs = set(list(df['plot_group']))
pgs.remove('NÍ BHAINEANN')
pgs.remove('DUBLIN 23')
pgs.remove('DUBLIN 21')
pgs.remove('BAILE ?THA CLIATH 17')

#plot grouping 

def dubornot(row):
    if row['postcode'] != 'OTHER':
        val = 'DUBLIN'
        
    elif row['postcode'] == 'OTHER':
        val = 'OUTSIDE_DUBLIN'

    return val
df['dublin_ind'] = df.apply(dubornot, axis=1)
check_freq(df.dublin_ind)

mdate =max(df.sale_date).strftime('%Y-%m-%d')

df.to_csv('ppr_%s.csv' %mdate)