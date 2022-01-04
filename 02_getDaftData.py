#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jan 26 14:33:26 2021

@author: shanemccarthy
"""
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

    # options = [
    #     LocationsOption(location),
    #     PriceOption(min_price, max_price),
    #     BedOption(min_beds, max_beds),
    #     PropertyTypesOption(property_type),
    #     AdStateOption(ad_state),
    #     FacilitiesOption(facility),
    #     MediaTypesOption(media_type),
    #     SortOption(sort),
    #     FurnishingOption(furnishing),
    #     LeaseLengthOption(min_lease, max_lease),
    ]

https://github.com/TheJokersThief/daft-scraper/

/Applications/anaconda3/envs/py37_daft/lib/python3.7/site-packages/daft_scraper


@author: shanemccarthy
"""
import numpy as np
import pandas as pd
from pandas import ExcelWriter
from datetime import date, datetime, timedelta
import os
from math import radians, cos, sin, asin, sqrt

#project name   
path="DUBLIN_15_DUBLIN_base_v2.xlsx"

#Over-ride base table
over_ride=True;

#Update with lat long of B's work

b_work =[53.37506,-6.36319]

def Haversine(lat1,lon1,lat2,lon2, **kwarg):
    """
    This uses the ‘haversine’ formula to calculate the great-circle distance between two points – that is, 
    the shortest distance over the earth’s surface – giving an ‘as-the-crow-flies’ distance between the points 
    (ignoring any hills they fly over, of course!).
    Haversine
    formula:    a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
    c = 2 ⋅ atan2( √a, √(1−a) )
    d = R ⋅ c
    where   φ is latitude, λ is longitude, R is earth’s radius (mean radius = 6,371km);
    note that angles need to be in radians to pass to trig functions!
    """
    R = 6371.0088
    lat1,lon1,lat2,lon2 = map(np.radians, [lat1,lon1,lat2,lon2])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2) **2
    c = 2 * np.arctan2(a**0.5, (1-a)**0.5)
    d = R * c
    return round(d,1)


from daft_scraper.search import DaftSearch, SearchType
from daft_scraper.search.options import (
    PropertyType, PropertyTypesOption, Facility, FacilitiesOption,
    PriceOption, BedOption, LeaseLengthOption,Furnishing
)
from daft_scraper.search.options_location import LocationsOption, Location

options = [
    PropertyTypesOption([PropertyType.ALL]),
    LeaseLengthOption(1,12),
    
    #FacilitiesOption([Facility.PARKING]),
    LocationsOption([Location.NORTH_CO_DUBLIN_DUBLIN]),
    PriceOption(1800, 2400),
    BedOption(2, 3),
    #Furnishing =='furnished'
]

api = DaftSearch(SearchType.RENT)
listings = api.search(options)

print("Records scraped from daft.ie",len(listings))


id=[]
price=[] 
ber=[]
title=[]
lat=[]
long=[]
propertyType=[]
numBedrooms=[]
numBathrooms=[]
url=[]
seller_branch=[]
seller_name=[]
seller_phone=[]
featuredLevel=[]
publishDate=[]
views=[]
description=[]
        

    
for listing in listings:

        x=(getattr(listing, 'ber',{'rating': 'MISSING'}))
        sell=(getattr(listing, 'seller'))
        y=getattr(listing, 'point')
        latlong=y['coordinates']
    
        id.append(getattr(listing, 'id'))
        price.append(getattr(listing, 'price'))
        ber.append(x['rating'])
        title.append(getattr(listing, 'title'))
        lat.append(latlong[1])
        long.append(latlong[0])
        propertyType.append(getattr(listing, 'propertyType'))
        numBedrooms.append(getattr(listing, 'numBedrooms'))
        #numBathrooms.append(getattr(listing, 'numBathrooms'))
        url.append(getattr(listing, 'url'))
        #seller_branch.append(sell['branch'])
        seller_name.append(sell['name'])
        #seller_phone.append(sell['phone'])
        featuredLevel.append(getattr(listing,'featuredLevel'))
        publishDate.append(getattr(listing,'publishDate'))
        views.append(getattr(listing,'views'))
        description.append(getattr(listing,'description'))
        


cols=['id','price','ber','title','lat','long','propertyType','numBedrooms','url','seller_name','featuredLevel','publishDate', 'views','description']    
           

tuple_out=list(zip(id,price,ber,title,lat,long,propertyType,numBedrooms,url,seller_name,featuredLevel,publishDate,views,description))        
output=pd.DataFrame(tuple_out,columns=cols)     
output=output.drop_duplicates()
        
#calculate the distance to B's work
output['dist_to_bwork']=Haversine(output.lat, output.long, b_work[0],b_work[1])   


if os.path.isfile(path) and os.access(path, os.R_OK) and over_ride==False:
    
    print("Base file exists and is readable")
    base = pd.read_excel(open('DUBLIN_15_DUBLIN_base_v2.xlsx','rb'),index_col=None , sheet_name='base')
    base = base.drop('Unnamed: 0', 1)
    #base = base.drop('status', 1)
    print("%d historic records have been ingested" % len(base))
    
    # merge latest scrape    
    merged = pd.merge(base,output, on=['id','price','title','propertyType','url'], how='outer', indicator=True)
    
    #provide feedback on the new number of records being added 
    
    print( "adding %d new records..." % len(merged[merged._merge =='right_only']))
    
    # if there are new records - mark with today's date
    merged['status']=''
    merged.loc[merged._merge =='right_only', 'first_seen_date']= date.today().strftime('%Y-%m-%d')
    merged.loc[merged._merge =='right_only', 'status']= 'new'
    merged.loc[merged._merge =='both', 'status']= 'existing'
    merged.loc[merged._merge =='left_only', 'status']= 'gone'
    #date.today() + timedelta(days=1)).strftime('%Y-%m-%d')

    # drop the merge indicator
    merged = merged.drop('_merge', 1)
    
    # sort by first seen date and price
    merged=merged.sort_values(['first_seen_date', 'dist_to_bwork'], ascending=[False, True])
    
    # overwrite the orginal database 
    writer=pd.ExcelWriter(r"DUBLIN_15_DUBLIN_base_v2.xlsx")
    merged.to_excel(writer,sheet_name= "base")
    writer.save()        

    
else:
    print("base file is missing or over-rise is set to True! - creating new base")   
    
    output['first_seen_date']= date.today().strftime('%Y-%m-%d')
    
    output=output.sort_values(['first_seen_date', 'dist_to_bwork'], ascending=[False, True])
    
    writer=pd.ExcelWriter(path)
    output.to_excel(writer,sheet_name= "base")
    writer.save()     
    



        



