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
import pickle
import utils
import sanitize
from CT_BERT import BertSentiment
from gensim.models import LdaModel

class Preprcessing():

    def __init__(self,path_2_file):
        self.path = path_2_file
        self.hdfs = os.listdir(path_2_file)
        self.corpus, self.bow_corpus, self.dictionary = self.load_LDA()
        self.lda = LdaModel.load("./../data/BOTTOM_UP/LDA/topic/lda_9.model")

        self.user = pd.read_csv("./../data/BOTTOM_UP/GRAPH/depression_nodes.csv").rename(columns={"0":"user_name"})["user_name"].tolist()
        self.BERT = BertSentiment()
        self.moods = [utils.fix_4_regex(x) for x in utils.get_moods()]
        self.output_dataframe = pd.DataFrame()
        pd.DataFrame(columns=utils._COLUMNSD_).to_csv("./../data/BOTTOM_UP/depression_tweets.csv",index=False)

    def load_LDA(self):
        print(str(datetime.now()), "Loading LDA")
        with open("./../data/BOTTOM_UP/LDA/preprocessed_corpus.pkl", "rb") as file:
            corpus = pickle.load(file)
        file.close()
        with open("./../data/BOTTOM_UP/LDA/bow_corpus.pkl", "rb") as file:
            bow_corpus = pickle.load(file)
        file.close()
        with open("./../data/BOTTOM_UP/LDA/Ldictionary.pkl", "rb") as file:
            dictionary = pickle.load(file)
        file.close()
        print(str(datetime.now()), "Loaded LDA")
        return corpus, bow_corpus, dictionary

    def infer_topic(self,text):
        bow = self.dictionary.doc2bow(text.split(" "))
        t = self.lda.get_document_topics(bow)
        scores = dict(t)
        max_prob = max(scores.values())
        idx = [x for x in scores.values()].index(max_prob)

        if idx == 2:
            return "Topic1"
        elif idx == 3:
            return "Topic2"
        elif idx == 7:
            return "Topic3"
        else:
            return None

    def preprocess(self):
        for hdf in self.hdfs:
            print(str(datetime.now()), "COMPUTING",hdf)
            tmp = pd.read_hdf(self.path+hdf, "data")
            #tmp = utils.user_in_graph_(tmp, self.user)
            shape_before = tmp.shape[0]
            tmp = tmp.loc[tmp["user_name"].isin(self.user)]
            shape_after = tmp.shape[0]
            print("Riduzione utenti: ",(shape_after/shape_before)*100)

            print(str(datetime.now()),"COMPUTING TOPIC")
            tmp["Topic"] = tmp["processed_text"].apply(self.infer_topic)
            tmp = tmp.dropna(subset=["Topic"])

            print(str(datetime.now()),"COMPUTING SENTIMENT")
            tmp["VADER"] = tmp["text"].apply(utils.assign_VADER)
            tmp["CT_BERT"] = self.BERT.pipe_(tmp["processed_text"])

            print(str(datetime.now()), "PROCESSING TEXT")
            tmp["processed_text"] = tmp["processed_text"].apply(utils.remove_stopwords)

            print(str(datetime.now()),"COMPUTING CATEGORIES")
            for mood,mood_list in zip(["depression","anger","anx","sad","sexual","negemo","risk","death","medicine","stress"],self.moods):
                tmp[mood] = tmp["processed_text"].apply(utils.get_affinity, args=([mood_list]))
                tmp[mood+"_terms"] = tmp["processed_text"].apply(utils.get_terms, args=([mood_list]))

            print(str(datetime.now()), "COMPUTING MOOD WEIGHT")
            tmp["mood_weigh"] = tmp["processed_text"].apply(utils.get_weigh_greedy)

            print(str(datetime.now()),"USER VERIFIED")
            tmp["user_verified"] = tmp["user_verified"].apply(utils.check_user_verified)

            #added:
            tmp["stemmed_text"] = tmp["processed_text"].apply(utils.stem_text)

            print(str(datetime.now()), tmp.shape[0], "TWEET PROCESSED")
            #tmp = tmp.drop(columns=["SENTIMENT_LABEL"])
            #assert tmp.shape[0] == 39
            tmp.to_csv("./../data/BOTTOM_UP/depression_tweets.csv",mode="a",index=False,header=False)

if __name__ == "__main__":
    preprocessor = Preprcessing("./../data/database/depression/")
    preprocessor.preprocess()

    total = pd.read_csv("./../data/BOTTOM_UP/depression_tweets.csv")
    total.columns = utils._COLUMNSD_
    total = sanitize.sanitize_tweets_database(total)
    total.to_pickle("./../data/BOTTOM_UP/depression_tweets.pkl")
    input("Delete .csv files? (check free space).")
    os.remove("./../data/BOTTOM_UP/depression_tweets.csv")