import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
from pandas.core.common import SettingWithCopyWarning
from pandas.errors import DtypeWarning
warnings.simplefilter(action='ignore', category=SettingWithCopyWarning)
warnings.simplefilter(action='ignore', category=DtypeWarning)

import pandas as pd
import os
from datetime import datetime
import shutil

from tqdm import tqdm
tqdm.pandas()

import sys
sys.path.append("./utils/")
sys.path.append("./CODE/")

import utils
import sanitize
from CT_BERT import BertSentiment

class myScheduler():

    def __init__(self,target_path,topic):
        self.target_path = target_path
        self.topic = topic

        self.to_be_analyzed = os.listdir(self.target_path)
        self.analyzed = [x.strip() for x in open("./../data/TOP_DOWN/"+self.topic+"_processed_tweets.txt","r").readlines()]
        self.moods = [utils.fix_4_regex(x) for x in utils.get_moods()]
        self.community = self.load_communities()

        #self.user = pd.read_csv("./../data/TOP_DOWN/"+self.topic+"/"+self.topic+"_nodes.csv")["0"]
        #self.user = self.infer_user_in_community()
        self.user = self.load_communities()["user_name"].tolist()
        self.BERT = BertSentiment()
        self.output_dataframe = pd.DataFrame()

    def infer_user_in_community(self):
        community = pd.read_csv("./../data/TOP_DOWN/" + topic + "/" + topic + "_community.csv")[["Id", "modularity_class"]]
        print(community["modularity_class"].value_counts().sort_values()[-5:])
        idx = community["modularity_class"].value_counts().sort_values()[-5:].index.to_list()
        users = community.loc[community["modularity_class"].isin(idx)]["Id"].to_list()
        return users

    def load_communities(self):
        community = pd.read_csv("./../data/TOP_DOWN/" + topic + "/" + topic + "_community.csv")[["Id", "modularity_class"]]
        community = community.rename(columns={"Id": "user_name", "modularity_class": "Community"})
        return community

    def check_new_elements(self):
        total_elements = os.listdir(self.target_path)
        new_elements = set(total_elements).symmetric_difference(set(self.to_be_analyzed))
        self.to_be_analyzed.extend(list(new_elements))
        self.to_be_analyzed = list(set(self.to_be_analyzed).symmetric_difference(set(self.analyzed)))
        return

    def check_done_elements(self,elements):
        self.analyzed.append(elements)
        with open("./../data/TOP_DOWN/"+self.topic+"_processed_tweets.txt","w") as file:
            file.write(self.topic+"\n"+"\n".join(self.analyzed))
        file.close()
        return

    def schedule(self):
        print(str(datetime.now()),": BEGIN SCHEDULING")
        c = 0
        for data in self.to_be_analyzed:
            c = c+1
            print(str(datetime.now()),": Analyzing",data)
            if data.endswith(".csv")==True:
                tmp = pd.read_csv(self.target_path+data,delimiter="\t")
            elif data.endswith(".h5")==True:
                tmp = pd.read_hdf(self.target_path+data)
            else:
                print("FORMATO NON SUPPORTATO",data)
                continue
            #in topic
            tmp = tmp.loc[tmp[self.topic]==True]
            #in graph
            tmp = tmp.loc[tmp["user_name"].isin(self.user)]

            tmp = sanitize.sanitize_df(tmp)
            #tmp = utils.process_dataframe(tmp)

            if "processed_text" not in tmp.columns:
                print(str(datetime.now()), "PREPROCESSING TEXT")
                tmp["processed_text"] = tmp["text"].apply(utils.preprocess_tweet)

            if "SENTIMENT_LABEL" not in tmp.columns:
                print(str(datetime.now()),"COMPUTING VADER")
                tmp["SENTIMENT_LABEL"] = tmp["text"].apply(utils.assign_VADER)
            tmp = tmp.rename(columns={'SENTIMENT_LABEL': 'VADER'})

            print(str(datetime.now()), "COMPUTING SENTIMENT")
            tmp["VADER"] = tmp["text"].apply(utils.assign_VADER)
            tmp["CT_BERT"] = self.BERT.pipe_(tmp["processed_text"])

            print(str(datetime.now()),"REMOVING STOPWORDS")
            tmp["processed_text"] = tmp["processed_text"].apply(utils.remove_stopwords)

            print(str(datetime.now()),"COMPUTING CATEGORIES")

            for mood,mood_list in zip(["depression","anger","anx","sad","sexual","negemo","risk","death","medicine","stress"],self.moods):
                tmp[mood] = tmp["processed_text"].apply(utils.get_affinity,args=([mood_list]))
                tmp[mood+"_terms"] = tmp["processed_text"].apply(utils.get_terms, args=([mood_list]))

            print(str(datetime.now()), "COMPUTING MOOD WEIGHT")
            tmp["mood_weigh"] = tmp["processed_text"].apply(utils.get_weigh_greedy)
            print(str(datetime.now()),"USER VERIFIED")
            tmp["user_verified"] = tmp["user_verified"].apply(utils.check_user_verified)

            #tmp = tmp.merge(self.community, on="user_name")

            #added
            tmp["stemmed_text"] = tmp["processed_text"].apply(utils.stem_text)

            self.check_done_elements(data)
            #self.check_new_elements()
            print(str(datetime.now()), tmp.shape[0], "TWEET PROCESSED", data,len(self.to_be_analyzed)-c,"DAYS TO FINISH")
            tmp = tmp.drop(columns=["NEUTRAL","POSITIVE","NEGATIVE","retweeted","quoted"])
            tmp.to_csv("./../data/TOP_DOWN/"+self.topic+"/"+self.topic+"_tweets.csv",mode="a",index=False,header=False)

        total = pd.read_csv("./../data/TOP_DOWN/"+self.topic+"/"+self.topic+"_tweets.csv")
        total = sanitize.sanitize_tweets_database(total)
        total = total.merge(self.community, on="user_name")
        total.to_pickle("./../data/TOP_DOWN/"+self.topic+"_tweets.pkl")
        os.remove("./../data/TOP_DOWN/"+self.topic+"/"+self.topic+"_tweets.csv")
        print("NO MORE FILES TO PROCESS")
        return

if __name__ == "__main__":
    #topic = "Topic1"
    print("Scheduling is active")
    #q = input("Insert folder to schedule")
    q = "./../data/database/topic_csv/"
    #scheduler = myScheduler(q, topic=topic)
    #scheduler.schedule()
    for topic in ["Topic1","Topic2","Topic3"]:
        print("DOING",topic)
        scheduler = myScheduler(q,topic=topic)
        scheduler.schedule()
        print("_"*20)