from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import tensorflow as tf
import pandas as pd
from tqdm import tqdm
import os
import dask
from dask.distributed import Client
import pickle
tqdm.pandas()

class BertSentiment():
    def __init__(self,):
        self.model = TFAutoModelForSequenceClassification.from_pretrained( 'C:/Users/TwitterCovid-19/ANACONDA_WORKBENCH/SENTIMENT ANALYSIS/CT-BERT_FineTuned')
        self.tokenizer = AutoTokenizer.from_pretrained('digitalepidemiologylab/covid-twitter-bert-v2', add_special_tokens=True)
        print("CT-BERT model and tokenizer initialized")

    def pipe(self,text):
        try:
            input_ids = tf.constant(self.tokenizer.encode(text, add_special_tokens=True))[None, :]
            preds_encoded = self.model(input_ids)
            preds = tf.nn.softmax(preds_encoded[0], axis=1).numpy()[0]
            if preds[0] > preds[1] and preds[0] > preds[2]:
                return "NEGATIVE"
            elif preds[1] > preds[2] and preds[1] > preds[0]:
                return "NEUTRAL"
            elif preds[2] > preds[0] and preds[2] > preds[1]:
                return "POSITIVE"
            else:
                return "ERROR"
        except:
            return "ERROR"

    def pipe_(self,array):
        output = []
        for text in array:
            try:
                input_ids = tf.constant(self.tokenizer.encode(text, add_special_tokens=True))[None, :]
                preds_encoded = self.model(input_ids)
                preds = tf.nn.softmax(preds_encoded[0], axis=1).numpy()[0]
                if preds[0] > preds[1] and preds[0] > preds[2]:
                    output.append("NEGATIVE")
                elif preds[1] > preds[2] and preds[1] > preds[0]:
                    output.append("NEUTRAL")
                elif preds[2] > preds[0] and preds[2] > preds[1]:
                    output.append("POSITIVE")
                else:
                    output.append("ERROR")
            except:
                print("ERROR",text)
        return output


if __name__ == "__main__":
     BertSentiment().pipe("I've been tested positive to covid")
