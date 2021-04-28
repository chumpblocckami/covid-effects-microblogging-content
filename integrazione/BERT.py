from transformers import AutoTokenizer, TFAutoModelForSequenceClassification
import tensorflow as tf
from tqdm import tqdm
tqdm.pandas()
import pickle
import pandas as pd

class BertSentiment():
    def __init__(self,):
        #self.model = TFAutoModelForSequenceClassification.from_pretrained( 'C:/Users/TwitterCovid-19/ANACONDA_WORKBENCH/SENTIMENT ANALYSIS/CT-BERT_FineTuned')
        #self.tokenizer = AutoTokenizer.from_pretrained('digitalepidemiologylab/covid-twitter-bert-v2', add_special_tokens=True)
        print("CT-BERT model and tokenizer initialized")

        self.fmodel = pickle.load(open("./models/BERT_fake_model.pkl","rb"))
        self.ftokenizer = pickle.load(open("./models/BERT_fake_tokenizer.pkl", "rb"))

    def ftokenize(self,text):
        tok,features = self.ftokenizer
        if isinstance(text, str):
            input_id = features.transform(tok.transform([text]))
        else:
            input_id = features.transform(tok.transform(text))
        return input_id

    def fpipe(self,text):
        input_ids = self.ftokenize(text)
        preds = self.fmodel.predict(input_ids)
        if preds == 0:
            return "NEGATIVE"
        elif preds == 1:
            return "POSITIVE"
        else:
            return "NEUTRAL"

    def fpipe_list(self,list):
        input_ids = self.ftokenize(list)
        preds = self.fmodel.predict(input_ids)
        output = []
        for pred in tqdm(preds,desc="predicting"):
            if pred == 0:
                output.append("NEGATIVE")
            elif pred == 1:
                output.append("POSITIVE")
            else:
                output.append("NEUTRAL")
        return output

if __name__ == "__main__":
    bort = BertSentiment()
    bottom_up_data = pd.read_data("C:\\Users\\matteo.mazzola\\Desktop\\tweets\\depression_tweets.csv",
                                  usecols="text").sample(0.3)["text"].tolist()
    top_down_data = pd.read_data("C:\\Users\\matteo.mazzola\\Desktop\\tweets\\depression_tweets.csv",
                                 usecols="text").sample(0.3)["text"].tolist()
    bottom_up_preds = bort.fpipe_list(bottom_up_data)
    top_down_preds = bort.fpipe_list(top_down_data)