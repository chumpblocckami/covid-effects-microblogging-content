import pandas as pd
import os
import utils
from tqdm import tqdm
tqdm.pandas()

def sanitize_df(df,verbose=False):
    #df = pd.read_csv("./data/database/topic_csv/Fri_Nov_20_tweets_topic.csv", delimiter="\t")
    if "Unnamed: 0" in df.columns:
        print("Removing Unnamed: 0")
        df.columns = df.columns[1:].tolist() + ["_"]
        df = df.drop(columns=["_"])
    if verbose:
        print("SHAPE", df.shape)
        print(df.columns)
        print(df.dtypes)
        print(df.head())
    df = df[["date", "id_tweet", "text", "user_id", "user_name", "user_location", "user_verified", "in_reply_to_user_name",
             "retweeted", "RT_user_name", "quoted", "QT_user_name", "Topic1","Topic2","Topic3","POSITIVE", "NEGATIVE", "NEUTRAL", "SENTIMENT_LABEL"]]
    for column in ["SENTIMENT_LABEL", "POSITIVE", "NEGATIVE", "NEUTRAL","user_verified","Topic1","Topic2","Topic3"]:
        if verbose:
            print(column, ":", df[column].isna().sum())
        if df[column].isna().sum() > 0:
            if verbose:
                print("Removing na found in ",column)
            df = df.dropna(subset=[column])
    #df["user_verified"] = df["user_verified"].apply(utils.check_user_verified)
    df = df.astype({"SENTIMENT_LABEL": object, "POSITIVE": int,"NEGATIVE":int,"NEUTRAL":int}) #,"user_verified":bool})

    return df

def sanitize_df_graph(df,verbose=False):
    print("SHAPE",df.shape)
    if "Unnamed: 0" in df.columns:
        print("Removing Unnamed: 0")
        df.columns = df.columns[1:].tolist() + ["_"]
        df = df.drop(columns=["_"])
    df = df[["user_name","in_reply_to_user_name", "RT_user_name", "QT_user_name", "Topic1", "Topic2", "Topic3"]]
    df = df.dropna(subset=["Topic1","Topic2","Topic3"])
    print("SHAPE",df.shape)
    return df

def sanitize_path_graph(path, verbose=False):
    df = pd.read_csv(path, delimiter="\t")
    df = sanitize_df_graph(df, verbose=False)
    return df

def sanitize_path(path, verbose=False):
    df = pd.read_csv(path, delimiter="\t")
    df = sanitize_df(df, verbose=False)
    return df

def sanitize_folder(path, verbose=False):
    csvs = os.listdir(path)
    for csv in csvs:
        df = pd.read_csv(path+csv, delimiter="\t")
        df = sanitize_df(df)
        df.to_csv(path+csv,index=False, delimiter="\t")
    return df

def sanitize_tweets_database(df):
    cols = utils._COLUMNS_
    #df = pd.read_pickle(path)
    df['day'] = pd.to_datetime(df['date'], format='%a %b %d %H:%M:%S +0000 %Y').dt.date
    df["processed_text"] = df["processed_text"].fillna("")

    return df