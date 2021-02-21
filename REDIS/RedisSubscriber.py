#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import time 
import datetime
from datetime import timedelta
import json
import redis 
import bz2
import requests
import json
from threading import Thread
import pymongo
import sys
import urllib3

#no warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

#auth Redis
RedisSubscriber = redis.Redis(host='localhost', port=6379,db=0)
RedisSubscriber.flushdb()
redis_key = 0.0

#auth Twitter
consumer_key,consumer_secret = open('files/keys.txt','r').readlines()
consumer_key = consumer_key[:-1]


# In[ ]:


def get_bearer_token(key, secret):
    response = requests.post(
        'https://api.twitter.com/oauth2/token',
        auth=(key, secret),
        data={'grant_type': 'client_credentials'},
        headers={'User-Agent': 'mmazzola'})

    if response.status_code != 200:
        raise Exception(f'Cannot get a Bearer token (HTTP %d): %s' % (response.status_code, response.text))
    body = response.json()
    return body['access_token']

def save2redis(item):
    global redis_key
    RedisSubscriber.set(redis_key,bz2.compress(item.encode("utf-8")))
    redis_key+=0.01
    
def preprocess(response_line):
    json_ = json.loads(response_line)
    dicts = {}
    attrs = ['id','in_reply_to_user_id','in_reply_to_status_id','lang','created_at']
    for i in attrs:
        dicts[i] = json_[i]
    #USER
    dicts['user'] = json_['user']['id']
    dicts['verified'] = json_['user']['verified']
    try:
        dicts['user_location'] = json_['user']['location']
    except:
        dicts['user_location'] = None
    try:
        dicts['timezone'] = json_['user']['timezone']
    except:
        dicts['timezone'] = None

    if(json_['truncated'] == True):
        if ("retweeted_status" in json_.keys()):
            if json_['retweeted_status']['truncated']==True:
                dicts['text'] = json_['retweeted_status']['extended_tweet']['full_text']
            else:
                dicts['text'] = json_['retweeted_status']['text']
        else:
            dicts['text'] = json_['extended_tweet']['full_text']
    else:
        dicts['text'] = json_['text']

    #RETWEETED
    if("retweeted_status" in json_.keys()):
        dicts['retweeted_id'] = json_['retweeted_status']['id']
        dicts['retweeted_user'] = json_['retweeted_status']['user']['id']
        dicts["retweeted"] = True
    else:
        dicts['retweeted'] = None

    #QUOTED
    if (json_["is_quote_status"] == True):
        dicts["quoted_status_id"] = json_["quoted_status_id"]
        dicts["quoted_status_user"] = json_["quoted_status"]["user"]["id"]
        if json_["quoted_status"]["truncated"] == True:
            dicts["quoted_status_text"] = json_["quoted_status"]["extended_tweet"]["full_text"]
        else:
            dicts["quoted_status_text"] = json_["quoted_status"]["text"]
    else:
        dicts["quoted_status_id"] = None
        dicts["quoted_status_user"] = None
        dicts["quoted_status_text"] = None

    #LOCATION 23.09.2020
    try:
        dicts["geo"] = json_['geo']
        dicts['coordinates'] = json_['coordinates']
        dicts["place"] = json_['place']
    except:
        dicts["geo"] = None
        dicts['coordinates'] = None
        dicts["place"] = None
    try:
        dicts['links'] = [json_['entities']['urls'][x]['expanded_url'] for x in range(len(json_['entities']['urls']))]
    except:
        dicts['links'] = json_['entities']['urls']

    return json.dumps(dicts) #returns a string

def preprocess_v2(response_line):
    tweet = json.loads(response_line)
    dict = {}

    # TWEET
    dict["date"] = tweet["created_at"]
    dict["id_tweet"] = tweet["id"]
    dict["lang"] = tweet["lang"]

    if ("retweeted_status" in tweet.keys()):
        if tweet["retweeted_status"]["truncated"] == True:
            dict["text"] = tweet["retweeted_status"]["extended_tweet"]["full_text"]
        else:
            dict["text"] = tweet["retweeted_status"]["text"]
        #try:
        #    dict["text"] = tweet["retweeted_status"]["extended_tweet"]["full_text"]
        #except:
        #    dict["text"] = tweet["retweeted_status"]["text"]

    elif (tweet["truncated"] == True and "retweeted_status" not in tweet.keys()):
        dict["text"] = tweet["extended_tweet"]["full_text"]
    else:
        dict["text"] = tweet["text"]

    # USER
    dict["user_id"] = tweet["user"]["id"]
    dict["user_name"] = tweet["user"]["screen_name"]
    dict["user_location"] = tweet["user"]["location"]
    dict['user_timezone'] = tweet['user']['time_zone']
    dict["user_verified"] = tweet["user"]["verified"]

    # LOCATION
    dict["geo"] = tweet["geo"]
    dict["place"] = tweet["place"]
    dict["coordinates"] = tweet["coordinates"]

    # REPLY
    dict["in_reply_to_user_id"] = tweet["in_reply_to_user_id"]
    dict["in_reply_to_status_id"] = tweet["in_reply_to_status_id"]
    dict["in_reply_to_user_name"] = tweet["in_reply_to_screen_name"]

    # RETWEETED
    if "retweeted_status" in tweet.keys():
        dict["retweeted"] = True
        dict["RT_tweet_id"] = tweet["retweeted_status"]["id"]
        dict["RT_user_id"] = tweet["retweeted_status"]["user"]["id"]
        dict["RT_user_name"] = tweet["retweeted_status"]["user"]["screen_name"]
    else:
        dict["retweeted"] = False
        dict["RT_tweet_id"] = None
        dict["RT_user_id"] = None
        dict["RT_user_name"] = None

    # QUOTED
    try:
        if tweet["is_quote_status"] == True:
            dict["quoted"] = True
            dict["QT_tweet_id"] = tweet["quoted_status"]["id"]
            dict["QT_user_id"] = tweet["quoted_status"]["user"]["id"]
            dict["QT_user_name"] = tweet["quoted_status"]["user"]["screen_name"]
            if tweet["quoted_status"]["truncated"] == True:
                dict["QT_tweet_text"] = tweet["quoted_status"]["extended_tweet"]["full_text"]
            else:
                dict["QT_tweet_text"] = tweet["quoted_status"]["text"]
        else:
            dict["quoted"] = False
            dict["QT_tweet_id"] = None
            dict["QT_user_id"] = None
            dict["QT_user_name"] = None
            dict["QT_tweet_text"] = None
    except:
        dict["quoted"] = False
        dict["QT_tweet_id"] = None
        dict["QT_user_id"] = None
        dict["QT_user_name"] = None
        dict["QT_tweet_text"] = None

    # ADDON
    dict["entities_user"] = tweet["entities"]["user_mentions"]
    dict["entities_urls"] = tweet["entities"]["urls"]
    dict["entities_hash"] = tweet["entities"]["hashtags"]

    if "possibly_sensitive" in tweet.keys():
        dict["possibly_sensitive"] = tweet["possibly_sensitive"]
    else:
        dict["possibily_sensitive"] = None

    return json.dumps(dict) #returns a string

def stream_connect(partition,all_=False):
    response = requests.get('https://api.twitter.com/labs/1/tweets/stream/covid19?partition={}'.format(partition),
                            headers={'User-Agent': 'mmazzola',
                                     'Authorization': 'Bearer {}'.format(get_bearer_token(consumer_key, consumer_secret))},
                            stream=True,verify=False)
    
    for response_line in response.iter_lines():
        if response_line:
            if all_==True:
                #get everything
                if json.loads(response_line)["lang"] in ["it", "en"]:
                    save2redis(json.dumps(json.loads(response_line)))
                else:
                    pass
            else:
                try:
                    #get only relevant feature (save memory)
                    if json.loads(response_line)["lang"] in ["it","en"]:
                        dicts_preprocessed = preprocess_v2(response_line)
                        save2redis(dicts_preprocessed)
                    else:
                        pass
                except:
                    #if problems, get everything
                    print(datetime.datetime.now())
                    print("Connection capped!")
                    print(json.dumps(json.loads(response_line)))
                    time.sleep(900)
def main():
    print('### BEGINNING ###')
    while(True):
        try:#prova a connettersi
            for partition in range(1, 5):
                x = Thread(target=stream_connect, args=(partition,)).start()
            time.sleep(10) #qua 10 secondi ma è da rivedere documentazione
        except: #se non si connette, riprova tenendo in considerazione heartbeat
            for partition in range(1, 5):
                x = Thread(target=stream_connect, args=(partition,)).start()
            time.sleep(20)

    print(open("files/the_end.txt","r",encoding="utf-8").read())
    
if __name__ == '__main__':
    main()

