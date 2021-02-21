#!/usr/bin/env python
# coding: utf-8

# In[1]:


import time 
import datetime
from datetime import timedelta
import json
import redis 
import bz2
import pymongo
import os
from cleantext import clean

Consumer = redis.Redis(host='localhost', port=6379,db=0)

cluster = pymongo.MongoClient('mongodb://localhost:50082/')
db = cluster.COVID2020
collections_ = db.COVID2020_v5

def save2mongo(item):
    global cluster,db,collections_

    if(type(item)==list):
        collections_.insert_many(item)
    else:
        collections_.insert_one(item)
    if(str(datetime.datetime.now())[:10]+".txt" in os.listdir(os.path.abspath(os.getcwd()))):
        logs = open(str(datetime.datetime.now())[:10] + ".txt", "a+")
        logs.write(str(datetime.datetime.now())[:19]+" imported "+str(len(item))+" tweets\n")
        logs.close()
    else:
        logs = open(str(datetime.datetime.now())[:10] + ".txt", "w")
        logs.write(str(datetime.datetime.now())[:19]+" imported "+str(len(item))+" tweets\n")
        logs.close()

def preprocess(tweet):
    text = tweet["text"]
    lang = tweet["lang"]
    tweet["text"] = clean(text,
                 fix_unicode=True,  # fix various unicode errors
                 to_ascii=True,  # transliterate to closest ASCII representation
                 lower=True,  # lowercase text
                 no_line_breaks=False,  # fully strip line breaks as opposed to only normalizing them
                 no_urls=True,  # replace all URLs with a special token
                 no_emails=True,  # replace all email addresses with a special token
                 no_phone_numbers=True,  # replace all phone numbers with a special token
                 no_numbers=False,  # replace all numbers with a special token
                 no_digits=False,  # replace all digits with a special token
                 no_currency_symbols=True,  # replace all currency symbols with a special token
                 no_punct=False,  # fully remove punctuation
                 replace_with_url="<URL>",
                 replace_with_email="<EMAIL>",
                 replace_with_phone_number="<PHONE>",
                 replace_with_number="<NUMBER>",
                 replace_with_digit="0",
                 replace_with_currency_symbol="<CUR>",
                 lang=lang)
    return tweet

# In[ ]:


cursor = '0'
while True:
    try:
        cursor, keys = Consumer.scan(cursor=cursor, count=100_000)
        redis_list = Consumer.mget(*keys)
        save2mongo([json.loads(bz2.decompress(x).decode("utf-8")) for x in redis_list])
        with Consumer.pipeline() as pipe:
            for x in keys:
                pipe.expire(x,timedelta(seconds=0))
            pipe.execute()
        time.sleep(5)
    except:
        print(str(datetime.datetime.now())," No data to read, waiting...")
        time.sleep(5)

