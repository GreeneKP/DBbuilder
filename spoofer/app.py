"""
start local demo with...
conda activate
Streamlit
streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
from requests import get, Session, post
import time
from datetime import datetime, timedelta
from io import StringIO
import statistics as stats
import scipy.stats as scistats


uriBase                = "https://www.space-track.org"
requestLogin           = "/ajaxauth/login"



siteCred = {'identity': "space.state@aol.com", 'password': "123SSptaactee123!"}


# use requests package to drive the RESTful session with space-track.org
with Session() as session:
    # run the session in a with block to force session to close if we exit

    # need to log in first. note that we get a 200 to say the web site got the data, not that we are logged in
    resp = session.post(uriBase + requestLogin, data = siteCred)
    if resp.status_code != 200:
        raise MyError(resp, "POST fail on login")
    
    print(resp.headers)

    seshcook = resp.headers['Set-Cookie']
    seshcook = seshcook.split(' ')[0][:-1]

spacetrackheaders = {"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
"accept-encoding": "gzip, deflate, br, zstd",
"accept-language": "en-US,en;q=0.9,es;q=0.8",
"cache-control": "max-age=0",
"cookie": f"spacetrack_csrf_cookie=pc9o9c6722kl32quis48b594gl2cmp5c; {seshcook}",
"priority": "u=0, i",
"sec-ch-ua": '"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
"sec-ch-ua-mobile": "?1",
"sec-ch-ua-platform": '"Android"',
"sec-fetch-dest": "document",
"sec-fetch-mode": "navigate",
"sec-fetch-site": "none",
"sec-fetch-user": "?1",
"upgrade-insecure-requests": "1",
"user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"}

hdrs2 = {"accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
'Authorization': 'TOK:space.state@aol.com',
'accept-encoding':'gzip, deflate, br, zstd',
'accept-language':'en-US,en;q=0.9,es;q=0.8',
'cache-control':'max-age=0',
'cookie':f'spacetrack_csrf_cookie=8u4fvh6rr0rr9bm68ovuf6h2l2v728r2; {seshcook}',
'priority':'u=0, i',
'referer':'https://www.space-track.org/auth/login',
'sec-ch-ua':'"Chromium";v="130", "Google Chrome";v="130", "Not?A_Brand";v="99"',
'sec-ch-ua-mobile':'?1',
'sec-ch-ua-platform':'"Android"',
'sec-fetch-dest':'document',
'sec-fetch-mode':'navigate',
'sec-fetch-site':'same-origin',
'sec-fetch-user':'?1',
'upgrade-insecure-requests':'1',
'user-agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"'}



if datetime.now()-st.session_state['Timestamp']>timedelta(minutes=30):
        st.session_state['Timestamp'] = datetime.now()

#if local, use these, otherwise...
#satcat_time = pd.read_csv("data/satcat.csv")['Timestamp'].iloc[0][:19]
#date_format = '%Y-%m-%d %H:%M:%S'
#new_time = datetime.strptime(satcat_time, date_format)

new_time = st.session_state['Timestamp']

timestamp_difference = datetime.now() - new_time
if timestamp_difference > timedelta(hours=3):
    satcat = pd.read_csv("https://celestrak.org/pub/satcat.csv")
    satcat['Timestamp'] = datetime.now()
    satcat.to_csv('data/satcat.csv',header=True,sep=',')
else: satcat = pd.read_csv("data/satcat.csv")


#The following code parses a ton of satellites out of the database so the user can only 
#select satellites with enough pertinent information to actually let the tool function properly...
#It's worth noting that the satellite catalog is a complete catalogue of everything that has EVER
#been in space to include every individual piece of debris, deorbited sats, sputnik, etc. so it must
#be parsed thoroughly so that the only available satellites to select are those that could reasonably
#benefit from a prediction... No need to predict Sputniks Orbit or maneuvers afterall!

#Sats must be considered functional and on orbit
satcat = satcat[satcat['OPS_STATUS_CODE'] == "+"]

#Sats must not be labelled as debris or rocket bodies (neither of which maneuver!)
satcat = satcat[satcat['OBJECT_TYPE'] != "DEB"]
satcat = satcat[satcat['OBJECT_TYPE'] != "R/B"]

#Sats must have complete data, without random gaps across different observations
satcat = satcat[satcat['DATA_STATUS_CODE'] != "NEA"]
satcat = satcat[satcat['DATA_STATUS_CODE'] != "NCE"]
satcat = satcat[satcat['DATA_STATUS_CODE'] != "NIE"]

#Sats must be orbitting the Earth
satcat = satcat[satcat['ORBIT_CENTER'] == "EA"]

satcat = satcat[satcat['Period'] < 15]


#Title of the app
st.title("GEO Database Builder")

#Here we create the form the user completes to select a satellite of the available options.
#I wanted to ensure no user imput errors were possible so, as such both available search criteria,
#Name and satcat number, are in drop-down menus. 
sat_selection_form = st.form("SCC selector")
number_search = sat_selection_form.selectbox('Select NORAD SATCAT Number of a specific Satellite you want in GEO: ',satcat['NORAD_CAT_ID'])
selection_criteria = sat_selection_form.radio('Select Number of Additional Satellites to put in GEO: ', options=['0','10','20','30','40','50'])


#I've come to find that once interacted with, 'submission' is set to 'True',
#hence, the rest of the file will be in an if statement... 
submission = sat_selection_form.form_submit_button("Build Database")

today = datetime.today()
today=str(today)
today=today[:10]

onelist = []

tenlist = [37810, 42814, 39476, 37749, 45920, 27718, 41589, 38991, 34111, 32487]

twentylist = [40732, 37810, 40364, 42814, 36101, 39476, 39498, 37749, 37933, 45920, 39216, 27718, 42741, 41589, 33278, 38991, 37602, 34111, 33055, 32487]

thirtylist = [44334, 54048, 37810, 43700, 47306, 42814, 38245, 39034, 39476, 38098, 41552, 37749, 39460, 42951, 45920, 36744, 40940, 27718, 32252, 37834, 41589, 28446, 39688, 38991, 42432, 40874, 34111, 43039, 37816, 32487]

fortylist = [32299, 40732, 36582, 37810, 39215, 40364, 41384, 42814, 43632, 36101, 43698, 39476, 41747, 39498, 40880, 37749, 41028, 37933, 32019, 45920, 38331, 39216, 41836, 27718, 35756, 42741, 28187, 41589, 28252, 33278, 37809, 38991, 49055, 37602, 38867, 34111, 37264, 33055, 36830, 32487]

fiftylist = [38652, 41310, 28946, 44479, 37810, 32294, 29526, 41186, 29270, 42814, 49333, 44035, 37393, 42698, 39476, 38740, 41793, 39508, 45026, 37749, 42815, 35696, 46112, 41903, 45920, 42917, 41034, 43611, 28899, 27718, 25924, 43633, 40882, 26580, 41589, 39127, 36516, 28702, 33373, 38991, 40733, 43562, 38749, 43175, 34111, 28945, 42950, 40875, 32794, 32487]

satlist = []
if submission:
    if selection_criteria == '0':
        satlist = onelist
    elif selection_criteria == '10':
        satlist = tenlist
    elif selection_criteria == '20':
        satlist = twentylist
    elif selection_criteria == '30':
        satlist = thirtylist
    elif selection_criteria == '40':
        satlist = fortylist
    elif selection_criteria == '50':
        satlist = fiftylist
    
pickedscc = number_search

satlist = satlist.append(pickedscc)


for sat_num in satlist:
    zr = get(f"https://www.space-track.org/basicspacedata/query/class/gp_history/NORAD_CAT_ID/{sat_num}/orderby/TLE_LINE1%20ASC/EPOCH/2000-01-01--{today}/format/tle",headers=hdrs2)
    oneline = zr.text
    tlesraw = oneline.split('\r\n1')

for i in range(len(tlesraw)):
   tlesraw[i] = tlesraw[i].replace('\r\n','|')

for i in range(len(tlesraw)):
    tlesraw[i] = tlesraw[i].replace(' ','|')
    tlesraw[i] = tlesraw[i].split('|')

tle_df = pd.DataFrame(tlesraw)
tle_df['Output']=''

def get_daytime(index_num):
    jday = tle_df.iloc[index_num][5]

    jday = float(jday)

    date, time = divmod(jday, 1.0)

    date = str(int(date))
    #
    #
    #Next convert the fractional day into seconds:
    #

    timedelta(days=time)
    #and add the two together:
    #
    output = datetime.strptime(date, '%y%j') + timedelta(time)

    return output.strftime("TLE,%b %d %Y %H:%M:%S.%f,1 ")

for i in range(len(tle_df[0])):
    tle_df[0].iloc[i] = get_daytime(i)

tle_df = tle_df.map(lambda x: str(x) if type(x) != type(str) else x)
tle_df = tle_df.map(lambda x: '' if x == 'None' else x)
tle_df = tle_df.map(lambda x: x + ' ' if type(x) == str and len(x)>1 else x)

for h in range(28):
    for col in tle_df.columns[:-2]:
        for i in range(len(tle_df[col])):
            if tle_df[col].iloc[i] == '' and tle_df[col].iloc[i] != tle_df[col+1].iloc[i]:
                tle_df[col].iloc[i] = tle_df[col+1].iloc[i] 
                tle_df[col+1].iloc[i] = ''

for col in tle_df.columns[:-1]:
    if tle_df[col].iloc[0] == tle_df[col].iloc[len(tle_df)-1] and tle_df[col].iloc[0] == '':
        tle_df = tle_df.drop(columns=col)

tle_df[3] = '  ' + tle_df[3]
tle_df[8] = ''
tle_df[9] = '   1,2'
tle_df[10] = ' ' + tle_df[10] + '  '
tle_df[14] = ' ' + tle_df[14] + ' '

tle_df['Output']=tle_df.sum(axis=1,skipna=True)
tle_df['Output'] = tle_df['Output'] + '\n'

tle_df['JDATE']=None
for i in range(len(tle_df)):
    tle_df['JDATE'].iloc[i] = tle_df[3].iloc[i]
    tle_df['JDATE'].iloc[i] = tle_df['JDATE'].iloc[i][2:7]

import os


for i in range(len(tle_df)):
    jate = tle_df['JDATE'].iloc[i]
    filepath = f'DATABASE/StateProcessing/StateDatabase/{jate}_Database_States.txt'

    if os.path.exists(filepath):
        with open(filepath, 'a') as file:
            file.write(tle_df['Output'].iloc[i])
            file.close
    else:
        with open(filepath, 'w') as file:
            file.write(tle_df['Output'].iloc[i])
            file.close
    

for i in range(len(tle_df)):
    tle_df[i] = tle_df[i].split(' ')

