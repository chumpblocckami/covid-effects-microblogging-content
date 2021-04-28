import pandas as pd
from nltk.tokenize import TweetTokenizer
from cleantext import clean
from tqdm import tqdm
import gensim
from gensim import corpora, models
from gensim.models import LdaMulticore
from gensim.models.coherencemodel import CoherenceModel
import os
import pickle

class LDA():
    def __init__(self,path):
        self.path = path
        self.corpus = None
        self.stopwords = self.get_stopwords()
        self.dictionary = None
        self.bow_corpus = None
        self.lda_models = dict()

    def get_stopwords(self):
        with open("../utils/stopwords.txt", "r") as file:
                stopwords = [x.strip() for x in file.readlines()]
        file.close()
        stopwords = set(stopwords)
        stopwords.update(gensim.parsing.preprocessing.STOPWORDS)
        return stopwords

    def load_texts(self,path):
        data = pd.read_csv(path,usecols=["text"])
        data = data.sample(n = 1_000_000)
        return data["text"].to_list()

    def get_preprocessing(self,save=True):
        if self.corpus == None:
            return "No data to preprocess: breaking"
        corpus_preprocessed = []
        tweet_tokenizer = TweetTokenizer()
        for text in tqdm(self.corpus, desc="Preprocessing data"):
            text = gensim.utils.simple_preprocess(text)
            text = [x for x in text if x not in self.stopwords and len(x) > 2]
            text = " ".join(text)
            text = clean(text, fix_unicode=True, to_ascii=True,lower=True,
                                     no_line_breaks=False, no_urls=True,no_emails=True,
                                     no_phone_numbers=True, no_numbers=False, no_digits=False,
                                     no_currency_symbols=True, no_punct=False,
                                     replace_with_url="<URL>",replace_with_email="<EMAIL>",
                                     replace_with_phone_number="<PHONE>",replace_with_number="<NUMBER>",
                                     replace_with_digit="0",replace_with_currency_symbol="<CUR>",
                                     lang="en")
            corpus_preprocessed.append(tweet_tokenizer.tokenize(text))
        if save:
            with open(self.path + "/data/corpus_no_preprocessing.pkl", "wb") as file:
                pickle.dump(corpus_preprocessed, file)
            file.close()
        return corpus_preprocessed

    def update_folder(self):
        if "topic" not in os.listdir(self.path):
            os.mkdir(self.path+"/topic")
        if "data" not in os.listdir(self.path):
            os.mkdir(self.path + "/data")

    def get_lda(self, lower_bound, higher_bound, read_corpus=None, save=True):
        if read_corpus!=None:
            with open(self.path + read_corpus, "rb") as file:
                corpus = pickle.load(file)
            file.close()
            self.corpus = corpus
            del corpus

        self.dictionary = gensim.corpora.Dictionary(self.corpus)
        self.dictionary.filter_extremes(no_below=2, no_above=0.1)
        self.bow_corpus = [self.dictionary.doc2bow(doc) for doc in self.corpus]
        del self.corpus
        lda_models = {}
        lda_models_coherence_cV = []
        for num_topics in tqdm(range(lower_bound, higher_bound),desc="Training LDAs"):
            model_lda = LdaMulticore(corpus = self.bow_corpus,
                                    num_topics=num_topics,
                                    id2word=self.dictionary,
                                    workers=8)

            coherencemodel = CoherenceModel(model=model_lda,
                                            texts=self.bow_corpus,
                                            dictionary=self.dictionary,
                                            coherence='c_v')

            coherence_value = coherencemodel.get_coherence()
            lda_models_coherence_cV.append(coherence_value)
            model_lda.save(self.path+"/topic/lda_"+str(num_topics)+".model")
            coherencemodel.save(self.path+"/topic/coherence_" + str(num_topics) + ".model")
            lda_models[num_topics] = model_lda
        if save:
            pickle.dump(self.bow_corpus, open(self.path + "/data/bow_corpus.pkl", 'wb'))
            pickle.dump(self.dictionary, open(self.path + "/data/Ldictionary.pkl", 'wb'))
            pickle.dump(self.lda_models, open(self.path + "/data/models.pkl", 'wb'))
        return lda_models

    def fit(self,path):
        self.update_folder()
        self.corpus = self.load_texts(path=path)
        self.corpus = self.get_preprocessing()

    def transform(self,corpus):
        self.lda = self.get_lda(lower_bound=2,higher_bound=51,read_corpus=corpus)

if __name__ == "__main__":
    path_2_data = "C:\\Users\\matteo.mazzola\\Desktop\\tweets\\depression_tweets.csv"
    lda = LDA("C:\\Users\\matteo.mazzola\Desktop\\tweets")
    #lda.fit(path=path_2_data)
    lda.transform(corpus="/data/corpus_no_preprocessing.pkl")
    print("FINISH!!!")