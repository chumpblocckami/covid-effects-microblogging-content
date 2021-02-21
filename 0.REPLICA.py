import pymongo
import pandas as pd
from pymongo import TEXT
from datetime import datetime
import re
import os

import sys
sys.path.append("./utils/")
import utils

import pickle
pickle.HIGHEST_PROTOCOL = 4

import warnings
warnings.filterwarnings('ignore')

from tqdm import tqdm
tqdm.pandas()

class MongoDB():
    def __init__(self,collections,topic):

        self.cluster = pymongo.MongoClient('mongodb://localhost:50082/', unicode_decode_error_handler='ignore')
        self.db = self.cluster.COVID2020

        if collections == "v2":
            self.collections_tweet = self.db.COVID2020_v2
        if collections == "v3":
            self.collections_tweet = self.db.COVID2020_v3
        if collections == "v4":
            self.collections_tweet = self.db.COVID2020_v4
        if collections == "v5":
            self.collections_tweet = self.db.COVID2020_v5
        if topic == "1":
            self.topic = [x.strip() for x in open("./../topic_list/1.txt", "r").readlines()]
        if topic =="2":
            self.topic = [x.strip() for x in open("./../topic_list/2.txt", "r").readlines()]
        if topic == "3":
            self.topic = [x.strip() for x in open("./../topic_list/3.txt", "r").readlines()]
        if topic == "depression":
            self.topic = [x.strip() for x in open("./../depression_list/depression_list.txt", "r").readlines()]

        self.stopwords = utils.load_stopwords()
        folder = input("Which database? depression or topic?: ")
        self.path = "./../data/database/"+str(folder)+"/"

    def list_affinity(self,text):
        return len(re.findall(re.compile('|'.join(self.topic)), text.lower()))

    def retrieve_documents(self,):
        chunk = 100_000
        skipper = 1
        for skip in range(0,self.collections_tweet.estimated_document_count(),chunk):
            self.collections_tweet.create_index([("text", TEXT)], name="text_search", default_language="english")
            if topic+"_"+collections+"_"+str(skipper)+".h5" in os.listdir(self.path):
                print(str(skipper)+"_topic"+topic+".h5","alredy processed,skipping")
                skipper = skipper + 1
                continue
            cursor = self.collections_tweet.find({"lang": "en", "$text": {"$search": " ".join(self.topic)}},).skip(skip).limit(chunk)
            try:
                print("\ncreating dataframe for chunk",skip)
                data = pd.DataFrame(cursor)[["date","id_tweet","text","user_id","user_name","user_location","user_verified",
                                            "in_reply_to_user_name","retweeted","RT_user_name","quoted","QT_user_name"]]
                print("filtering")
                data["processed_text"] = data["text"].progress_apply(utils.preprocess_tweet)
                print("processing")
                data["depression_markers"] = data["processed_text"].progress_apply(self.list_affinity)
                data = data.loc[data["depression_markers"] > 1]
                print("saving",data.shape[0],"tweets to depression")
                #data.to_pickle(self.path+"/"+collections+"/"+str(skipper)+"_topic"+topic+"_.pkl")
                data.to_hdf(self.path+topic+"_"+collections+"_"+str(skipper)+".h5", 'data')
            except Exception as e:
                print(e)
                cursor.close()
                continue
            cursor.close()
            skipper = skipper+1

if __name__ == "__main__":
    past = datetime.now()
    collections = sys.argv[1]
    topic = sys.argv[2]
    print("---LETS RETRIEVE!---")
    print("arguments",collections,topic)
    mongodb = MongoDB(collections,topic)
    mongodb.retrieve_documents()
    future = datetime.now()
    print("Query to {} with topic {} finished after {} minutes".format(collections,topic,(future - past).seconds/60))