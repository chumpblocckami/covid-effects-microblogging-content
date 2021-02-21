import re
import emoji
import cleantext
import pandas as pd
import gensim
from collections import Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from nltk import PorterStemmer
stemmer = PorterStemmer()
sentiment_analyzer = SentimentIntensityAnalyzer()

print("RICORDATI FIX FOR REGEX SE USI RE.SEARCH ALL")
#PREPROCESSING
def load_stopwords():
    with open("./utils/stopwords.txt", "r") as file:
        stopwords = [x.strip() for x in file.readlines()]
    file.close()
    stopwords = set(stopwords)
    stopwords.update(gensim.parsing.preprocessing.STOPWORDS)
    return stopwords
_STOPWORDS_ = load_stopwords()

def preprocess_tweet_fast(text):
    text = cleantext.clean(text, fix_unicode=True, to_ascii=True, lower=True)
    return text

def preprocess_tweet_no_stopwords(text,stopwords=_STOPWORDS_):
    text = re.sub("@[A-Za-z0-9]+", "", text).strip()
    text = cleantext.clean(text, fix_unicode=True, to_ascii=True, lower=True,
                 no_line_breaks=True,
                 lang="en",
                 no_urls=True,
                 no_punct=True,
                 no_numbers=True,
                 replace_with_url="",
                 replace_with_digit="",
                 replace_with_number="")
    text = emoji.demojize(text, language="en")
    text = gensim.utils.simple_preprocess(text)
    text = [x for x in text if x not in stopwords and len(x)>2]
    text = " ".join(text)
    return text

def preprocess_tweet(text):
    text = re.sub("@[A-Za-z0-9]+", "", text).strip()
    text = cleantext.clean(text, fix_unicode=True, to_ascii=True, lower=True,
                 no_line_breaks=True,
                 lang="en",
                 no_urls=True,
                 no_punct=True,
                 no_numbers=True,
                 replace_with_url="",
                 replace_with_digit="",
                 replace_with_number="")
    text = emoji.demojize(text, language="en")
    return text

def fix_4_regex(list):
    _list = []
    for i in list:
        if "*" in i:
            _list.append(r"\b"+i+ r"\b")
        else:
            _list.append(r"\b" + i + r"\b")
    return _list

def remove_stopwords(text,stopwords=_STOPWORDS_,augment_stopwords = True):
    text = gensim.utils.simple_preprocess(text)
    text = [x for x in text if x not in stopwords and len(x)>2]
    text = " ".join(text)
    return text

def stem_text(text):
    return " ".join([stemmer.stem(x) for x in text.split(" ")])

_COLUMNS_ = ['date', 'id_tweet', 'text', 'user_id', 'user_name', 'user_location', 'user_verified', 'in_reply_to_user_name',
 'RT_user_name', 'QT_user_name', 'Topic1', 'Topic2', 'Topic3', 'VADER', 'processed_text','CT_BERT','total','total_terms', 'anger', 'anger_terms',
 'anx', 'anx_terms', 'sad', 'sad_terms', 'sexual', 'sexual_terms', 'negemo', 'negemo_terms',
'risk', 'risk_terms', 'death', 'death_terms', 'medicine', 'medicine_terms', 'stress', 'stress_terms',
             'mood_weigh',"stemmed_text"]

_COLUMNSD_ = ['date', 'id_tweet', 'text', 'user_id', 'user_name', 'user_location',
       'user_verified', 'in_reply_to_user_name', 'retweeted', 'RT_user_name',
       'quoted', 'QT_user_name', 'processed_text', 'depression_markers',
       'Topic','VADER', 'CT_BERT', 'depression', 'depression_terms', 'anger',
       'anger_terms', 'anx', 'anx_terms', 'sad', 'sad_terms', 'sexual',
       'sexual_terms', 'negemo', 'negemo_terms', 'risk', 'risk_terms', 'death',
       'death_terms', 'medicine', 'medicine_terms', 'stress', 'stress_terms',
       'mood_weigh', 'stemmed_text']

#SENTIMENT ANALYSIS
def assign_VADER_from_tweet(tweet):
    res = sentiment_analyzer.polarity_scores(tweet["text"])["compound"]
    tweet["POSITIVE"] = 0
    tweet["NEGATIVE"] = 0
    tweet["NEUTRAL"] = 0

    if res > 0.05:
        score = 'POSITIVE'
        tweet["POSITIVE"] = 1
    if res < -0.05:
        score = "NEGATIVE"
        tweet["NEGATIVE"] = 1
    if res <= 0.05 and res >= -0.05:
        score = "NEUTRAL"
        tweet["NEUTRAL"] = 1
    tweet["SENTIMENT_LABEL"] = score
    return tweet

def assign_VADER(text):
    res = sentiment_analyzer.polarity_scores(text)["compound"]
    if res > 0.05:
        score = 'POSITIVE'
    if res < -0.05:
        score = "NEGATIVE"
    if res <= 0.05 and res >= -0.05:
        score = "NEUTRAL"
    return score

#TERMS FINDER
def get_terms(text,list):
    values =  " ".join(re.findall(re.compile('|'.join(list)), text))
    if values == None:
        value = " "
    return values

def get_affinity(text,list):
    return len(re.findall(re.compile('|'.join(list)), text))

#RICORDATI DI USARE FIX FOR REGEX SE USATO DENTRO RE.SEARCHALL
def get_moods():
    with open("./../depression_list/depression_list.txt", "r") as d_list:
        depression_list = set([x.strip() for x in d_list.readlines()])
    with open("./../depression_list/Anger.txt", "r") as d_list:
        anger_list = set([x.strip() for x in d_list.readlines()])
    with open("./../depression_list/Anx.txt", "r") as d_list:
        anx_list = set([x.strip() for x in d_list.readlines()])
    with open("./../depression_list/Sad.txt", "r") as d_list:
        sad_list = set([x.strip() for x in d_list.readlines()])
    with open("./../depression_list/Sexual.txt", "r") as d_list:
        sexual_list = set([x.strip() for x in d_list.readlines()])
    with open("./../depression_list/Negemo.txt", "r") as d_list:
        negemo_list = set([x.strip() for x in d_list.readlines()])
    with open("./../depression_list/Risk.txt", "r") as d_list:
        risk_list = set([x.strip() for x in d_list.readlines()])
    with open("./../depression_list/Death.txt", "r") as d_list:
        death_list = set([x.strip() for x in d_list.readlines()])
    with open("./../depression_list/depression_medicine.txt", "r") as d_list:
        medicine_list = set([x.strip() for x in d_list.readlines()])
    with open("./../depression_list/Stress.txt", "r") as d_list:
        stress_list = set([x.strip() for x in d_list.readlines()])

    return depression_list,anger_list,anx_list,sad_list,sexual_list,negemo_list,risk_list,death_list,medicine_list,stress_list

try:
    LIWC_WEIGH = pd.read_csv("./../data/DistilLIWC_weigh.csv")
except:
    LIWC_WEIGH = pd.read_csv("./data/DistilLIWC_weigh.csv")

def get_weigh(text,weigh=LIWC_WEIGH):
    #provare con starts with + altro controllo
    words_target = re.findall(re.compile("|".join(fix_4_regex(weigh["word"].tolist()))), text)
    total = sum([len(re.findall(re.compile("".join(fix_4_regex([word]))), " ".join(words_target)))*weigh.loc[weigh["word"]==word]["frequence"].values[0] for word in set(weigh["word"].tolist())])
    return round(total,5)

def get_weigh_greedy(text,weigh=LIWC_WEIGH):
    tot = re.findall(re.compile("|".join(fix_4_regex(weigh["word"].tolist()))), text)
    total = 0.0
    for words,freq in Counter(tot).items():
        total = total + sum([freq* weigh.loc[weigh["word_processed"]==x]["frequence"].values for x in set(weigh["word_processed"].str.replace("*",""))  if words.startswith(x)])
    if type(total)==float:
        return round(float(total), 5)
    return round(float(sum(total)),5)


#PREPROCESS DATABASE
def check_user_verified(marker):
    if marker == True:
        return True
    elif marker == False:
        return False
    elif marker == "False":
        return False
    elif marker == "True":
        return True
    else:
        return None

def user_in_graph_(df,user):
        df_output = pd.DataFrame()
        #print("\ntotal dataframe", df.shape)
        df["in_graph"] = df["user_name"].isin(user).tolist()
        df = df.loc[df["in_graph"] == True].drop(columns=["in_graph"])
        #print("in graph users", df.shape)
        if df.shape[0] == 0:
            return df
        #QUESTA LOGICA NON MI CONVINCE PARTICOLARMENTE, DA ANALIZZARE UN'ALTRA VOLTA E VALUTARE
        #PERCHE' RIPENSANDOCI SECONDO ME BASTA SOLO ANDARE A VEDERE SE UN UTENTE è NEL GRAFO OPPURE NO.
        tmp_rt = df.loc[(df["RT_user_name"].isin(user)) | (pd.isna(df["RT_user_name"]))]
        df_output = df_output.append(tmp_rt)
        del tmp_rt

        tmp_ry = df.loc[(df["in_reply_to_user_name"].isin(user)) | (pd.isna(df["in_reply_to_user_name"]))]
        df_output = df_output.append(tmp_ry)
        del tmp_ry

        tmp_qt = df.loc[(df["QT_user_name"].isin(user)) | (pd.isna(df["QT_user_name"]))]
        df_output = df_output.append(tmp_qt)
        del tmp_qt

        tmp_usr = df.loc[(df["user_name"].isin(user)) | (pd.isna(df["QT_user_name"])) | (pd.isna(df["RT_user_name"])) | (pd.isna(df["in_reply_to_user_name"]))]
        df_output = df_output.append(tmp_usr)
        del tmp_usr
        #print("with duplicates", df_output.shape)
        df_output = df_output.drop_duplicates()
        #print("without duplicates", df_output.shape)
        del df
        return df_output

def user_in_graph(df, user):
    df["in_graph"] = df["user_name"].isin(user).tolist()
    df = df.loc[df["in_graph"] == True].drop(columns=["in_graph"])
    return df

def safe_and_sund(df):
    import pandas as pd
    import sanitize
    import utils
    topic = "Topic1"
    xx = pd.read_csv("./data/TOP_DOWN/" + topic + "/" + topic + "_tweets.csv")
    xx.columns = utils._COLUMNS_
    community = pd.read_csv("./data/TOP_DOWN/" + topic + "/" + topic + "_community.csv")[["Id", "modularity_class"]]
    community = community.rename(columns={"Id": "user_name", "modularity_class": "Community"})
    xx = sanitize.sanitize_tweets_database(xx)
    xx = xx.merge(community, on="user_name")
    xx.to_pickle("./data/TOP_DOWN/" + topic + "_tweets.pkl")