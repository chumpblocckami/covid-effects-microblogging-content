from datetime import datetime
from datetime import timedelta
import pymongo
import urllib
from cleantext import clean
from tqdm import tqdm
import matplotlib.pyplot as plt
import logging
import os
import sys
import pandas as pd
import gensim
from nltk.tokenize import TweetTokenizer
from gensim import corpora, models
from gensim.models import LdaModel
from gensim.models import LdaMulticore
from gensim.models.coherencemodel import CoherenceModel
from wordcloud import WordCloud
import pickle
import json
import sys
sys.path.append("./utils/")
import utils
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

class LDA():
    def __init__(self,path,MONGO=False):
        self.path = path
        self.start_time = datetime.now()

        if MONGO:
            self.cluster = pymongo.MongoClient('mongodb://localhost:50082/',unicode_decode_error_handler='ignore')
            self.db = self.cluster.COVID2020
            self.collections_tweet = self.db.COVID2020_v2

        self.corpus = []
        self.stopwords = utils._STOPWORDS_
        self.dictionary = None
        self.lda_models = dict()

    def getDates(self):

        with open("./data/collections_mapping.txt") as json_file:
            mapping = json.load(json_file)

        dtimes = []
        now = datetime(2020, 10, 10, 0, 0, 0)
        for i in range(11):  # giorni in covid2020_v2
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(hours=+(24 * i))
            dtimes.append(day_end)
        date_p = [datetime.strftime(datetime.strptime(str(d), '%Y-%m-%d %H:%M:%S'),
                                        '%a %b %d %H:%M:%S +0000 %Y')[:10]
                  for d in dtimes]
        return date_p

    def getCollectionByDates(self,collection_name):

        if collection_name == "v2":
            self.collections_tweet = self.db.COVID2020_v2
            print("Querying collections: v2")
        elif collection_name == "v3":
            self.collections_tweet = self.db.COVID2020_v3
            print("Querying collections: v3")
        elif collection_name == "v4":
            self.collections_tweet = self.db.COVID2020_v4
            print("Querying collections: v4")
        elif collection_name == "v5":
            self.collections_tweet = self.db.COVID2020_v5
            print("Querying collections: v5")
        else:
            print("no collection name")
            return

        with open("./data/collections_mapping.txt") as json_file:
            mapping = json.load(json_file)
        day = mapping[collection_name]["day"]
        month = mapping[collection_name]["month"]
        days =  mapping[collection_name]["days"]

        dtimes = []
        now = datetime(2020, month, day, 0, 0, 0)
        for i in range(days):
            day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(hours=+(24 * i))
            dtimes.append(day_end)
        date_p = [datetime.strftime(datetime.strptime(str(d), '%Y-%m-%d %H:%M:%S'),
                                    '%a %b %d %H:%M:%S +0000 %Y')[:10]
                  for d in dtimes]

        return date_p

    def getText(self):
    #prendiamo 250k da ogni collections
        for coll in tqdm(["v2","v3","v4","v5"]):
            days = self.getCollectionByDates(coll)
            start = datetime.now()
            for day in days:
                pipeline = [{"$match": {"date": {"$regex": day + " *"}}},
                        {"$match": {"lang": "en"}},#]
                        {"$sample":{"size":50_000}}]

                cursor = self.collections_tweet.aggregate(pipeline, allowDiskUse=True)
                self.corpus.extend([x["text"] for x in cursor])
                cursor.close()

        print("Query time:", (datetime.now()-start).seconds/60)
        print("Texts in corpus:", len(self.corpus))
        print("Size in memory:", sys.getsizeof(self.corpus))
        with open(self.path+"/log.txt","w") as file:
            file.write("QUERY TIME:"+str((datetime.now()-start).seconds/60)+"\nLEN:"+str(len(self.corpus))+"\nSIZE"+str(sys.getsizeof(self.corpus)))
        file.close()
        return

    def getTextFile(self):
        start = datetime.now()
        if "corpus_no_preprocessing.pkl" in os.listdir(self.path):
            print("loading corpus")
            with open(self.path+"/corpus_no_preprocessing.pkl", "rb") as file:
                self.corpus = pickle.load(file )
        else:
            #with open("./data/database/golden_truth.txt","r") as file:
            #    csvs = [x.strip() for x in file.readlines()]
            #file.close()
            csvs = os.listdir("./../data/database/depression/")
            n_rows = round(5_000_000 / len(csvs))
            for csv in tqdm(csvs):
                #tweet_texts = pd.read_csv("./data/database/topic_csv/"+csv,
                #              delimiter="\t",
                #              usecols=["text"],
                #              dtype={"text":object}).sample(n_rows, random_state=126)
                tmp = pd.read_hdf("./../data/database/depression/"+csv)
                if "text_processed" in tmp.columns:
                    tweet_texts = tmp["text_processed"].sample(n_rows, random_state=126)#["text_processed"]
                else:
                    tweet_texts = tmp["processed_text"].sample(n_rows, random_state=126)#["processed_text"]
                del tmp
                self.corpus.extend([x for x in tweet_texts])
            print("TOTAL TWEETS LOADED: ",len(self.corpus))
            with open(self.path+"/log.txt","w") as file:
                file.write("QUERY TIME:"+str((datetime.now()-start).seconds/60)+"\nLEN:"+str(len(self.corpus))+"\nSIZE:"+str(sys.getsizeof(self.corpus)))
            file.close()
            with open(self.path+"/corpus_no_preprocessing.pkl","wb") as file:
                pickle.dump(self.corpus,file)
            file.close()

    def getStopwords(self):
        stopwords_location = "https://raw.githubusercontent.com/aiforpeople-git/First-AI4People-Workshop/master/NLP_AI/stopwords.txt"
        stopwords_data = urllib.request.urlopen(stopwords_location)
        stopwords = set([stopword.decode("utf-8").strip() for stopword in stopwords_data])

        stopwords.update(
            ["covid19", "coronavirus", "ncov2019", "2019nco", "ncov", "ncov2019", "2019ncov", "covid", "covid-",
             "covid_","covid2020" , "corona","mask","masks","virus","mask"])
        return stopwords

    def getPreprocessing(self):
        if "preprocessed_corpus.pkl" in os.listdir(self.path):
            print("loading preprocessed corpus")
            with open(self.path + "/preprocessed_corpus.pkl", "rb") as file:
                self.corpus = pickle.load(file)
        else:
            corpus_preprocessed = []
            tweet_tokenizer = TweetTokenizer()
            for text in tqdm(self.corpus):
                text = utils.remove_stopwords(text)
                #text = clean(text,fix_unicode=True, to_ascii=True,lower=True,
                #                 no_line_breaks=False, no_urls=True,no_emails=True,
                #                 no_phone_numbers=True, no_numbers=False, no_digits=False,
                #                 no_currency_symbols=True, no_punct=False,
                #                 replace_with_url="<URL>",replace_with_email="<EMAIL>",
                #                 replace_with_phone_number="<PHONE>",replace_with_number="<NUMBER>",
                #                 replace_with_digit="0",replace_with_currency_symbol="<CUR>",
                #                 lang="en")
                #text_normalized = []
                #for token in gensim.utils.simple_preprocess(text):
                #    if token not in gensim.parsing.preprocessing.STOPWORDS and len(token) > 3 and token not in self.stopwords:
                #        text_normalized.append(token)
                #corpus_preprocessed.append(tweet_tokenizer.tokenize(" ".join(text_normalized)))
                corpus_preprocessed.append(text.split(" "))
            with open(self.path+"/preprocessed_corpus.pkl","wb") as file:
                pickle.dump(corpus_preprocessed,file)
            self.corpus = corpus_preprocessed
            del corpus_preprocessed
        print("Size in memory:", sys.getsizeof(self.corpus))
        return

    def getLDA(self):
        logging.info("Creating bag of words for LDA model")
        self.dictionary = gensim.corpora.Dictionary(self.corpus)
        self.dictionary.filter_extremes(no_below=2, no_above=0.1)
        self.bow_corpus = [self.dictionary.doc2bow(doc) for doc in self.corpus]
        del self.corpus
        lda_models_coherence_cV = []

        for num_topics in tqdm(range(3, 13)):
            model_lda = LdaMulticore(corpus = self.bow_corpus,
                                 num_topics=num_topics,
                                 id2word=self.dictionary,
                                 workers=8)

            #coherencemodel = CoherenceModel(model=model_lda,
            #                                texts=self.corpus,
            #                                dictionary=self.dictionary,
            #                                coherence='c_v')

            #coherence_value = coherencemodel.get_coherence()
            #lda_models_coherence_cV.append(coherence_value)
            if "topic" not in os.listdir(self.path):
                os.mkdir(self.path+"/topic")
            model_lda.save(self.path+"/topic/lda_"+str(num_topics)+".model")
            #coherencemodel.save(self.path+"/topic/coherence_" + str(num_topics) + ".model")
            self.lda_models[num_topics] = model_lda

        return

    def saveResults(self):
        #use pickle
        logging.info("Saving corpus and dictionary in LDA folder for later use")
        pickle.dump(self.bow_corpus, open(self.path+"/bow_corpus.pkl", 'wb'))
        pickle.dump(self.dictionary, open(self.path+"/Ldictionary.pkl", 'wb'))

    def getVisualization(self,):
        for topic in range(3,13):
            cloud = WordCloud(stopwords=self.stopwords,
                              background_color='#515151',
                              width=2500,
                              height=1800,
                              max_words=50,
                              colormap='ocean',
                              prefer_horizontal=1.0)
            if self.lda_models == {}:
                topics = LdaModel.load(self.path+"/topic/lda_"+str(topic)+".model").show_topics(num_topics=topic, num_words=50, formatted=False)
            else:
                topics = self.lda_models[topic].show_topics(num_topics=topic, num_words=50, formatted=False)
            for i in range(0,len(topics)):
                topic_words = dict(topics[i][1])
                cloud.generate_from_frequencies(topic_words, max_font_size=300)
                plt.gca().imshow(cloud)
                plt.gca().set_title('LDA con '+str(topic)+' topic:\n topic' + str(i + 1), fontdict=dict(size=12))
                plt.gca().axis('off')
                plt.margins(x=0, y=0)
                plt.tight_layout()
                if "lda_"+str(topic) not in os.listdir(self.path+"/topic_wordcloud/"):
                    os.mkdir(self.path+"/topic_wordcloud/lda_" + str(topic))
                plt.savefig(self.path+"/topic_wordcloud/lda_" + str(topic) + "/"+str(i)+"_topic_wordcloud.png")
                plt.show()

    def saveWordsList(self):
        topics = {}
        logging.info("Load and save words from LDA Models")
        lda_models = [x for x in os.listdir(self.path) if "state" not in x and "id2word" not in x and ".npy" not in x and "coherence" not in x]
        for lda_name in lda_models:
            try:
                lda = LdaModel.load(path+"/"+lda_name)
                obj = {}
                for n in range(0, lda.num_topics):
                    obj.update({n:[x[0] for x in lda.show_topic(n,topn=50)]})
                topics[lda_name] = obj
            except Exception as e:
                print(lda_name, e)

        f = open(self.path+"/topic_list.pkl", 'wb')
        pickle.dump(topics, f)
        f.close()
        return

if __name__ == '__main__':
    path = "./../data/BOTTOM_UP/LDA/"
    lda_processor = LDA(path=path)
    past = datetime.now()
    #lda_processor.getText()
    lda_processor.getTextFile()
    lda_processor.getPreprocessing()
    lda_processor.getLDA()
    lda_processor.saveResults()
    future = datetime.now()
    print("Ore impiegate per preprocessing + LDA",(future - past).seconds / 60 / 60)

    lda_processor.saveWordsList()
    future = datetime.now()
    logging.info("Ore impiegate per preprocessing + LDA + salvataggio "+str((future - past).seconds / 60 / 60))


    #lda_processor.getVisualization()
    #future = datetime.now()

    #with open(path+'/topic_list.pkl', 'rb') as handle:
    #    b = pickle.load(handle)
    #handle.close()
    #for key, values in b.items():
    #    data = pd.DataFrame(values)
    #    data.columns = ["TOPIC" + str(x) for x in data.columns]
    #    data.to_csv(path+"/" + str(key) + ".csv")

    #logging.info("Ore impiegate per preprocessing + LDA + salvataggio "+str((future - past).seconds / 60 / 60))

