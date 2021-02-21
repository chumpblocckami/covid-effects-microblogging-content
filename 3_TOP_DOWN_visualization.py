import pandas as pd
import matplotlib.pyplot as plt
import sys
sys.path.insert(0,"./utils/")
import utils
import sanitize
from wordcloud import WordCloud
from sklearn.feature_extraction.text import CountVectorizer
from nltk.stem import PorterStemmer

stopwords = utils._STOPWORDS_
topic1_list = [x.strip() for x in open("./../topic_list/1.txt").readlines()]
topic2_list = [x.strip() for x in open("./../topic_list/2.txt").readlines()]
topic3_list = [x.strip() for x in open("./../topic_list/3.txt").readlines()]
stopwords = set(list(stopwords) + topic1_list + topic2_list + topic3_list)
ps = PorterStemmer
#sentiment
def barchart_sentiment_graph_bydate(df, topic, topic_name,sentiment):
    stacked = df[["day", sentiment]].groupby(["day", sentiment]).size().unstack()
    stacked.index = pd.to_datetime(stacked.index).day
    #stacked = stacked.reset_index().set_index("day")
    stacked.plot(kind='bar', stacked=True, fontsize=5, figsize=(7, 5),
                 title=topic_name+" "+sentiment, cmap="prism", rot=0)
    plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/"+topic+"/"+topic+"_"+sentiment+"_barplot")
    plt.show()

def barchart_sentiment_community_bydate(df,topic,topic_name,sentiment):
    fig, axes = plt.subplots(5, 1, figsize=(3, 10), sharex=True, sharey=True, dpi=250, )
    fig.suptitle(str(topic)+": "+topic_name)
    communities = df["Community"].value_counts().sort_values().iloc[-5:].index.tolist()
    for community, ax in enumerate(axes.flatten()):
        subset = df.loc[df["Community"] == communities[community]]
        print(community,subset.shape)
        fig.add_subplot(ax,title="Community "+str(community)+" "+sentiment)
        stacked = subset[["day", sentiment]].groupby(["day", sentiment]).size().unstack()
        stacked = stacked.reset_index().set_index("day")
        stacked.plot(kind='bar', stacked=True, fontsize=10, figsize=(7, 5), cmap="prism",ax=ax, legend=False )
        plt.gca().set_title('Community ' + str(communities[community]), fontdict=dict(size=8))
        plt.gca().axis('off')
    plt.subplots_adjust(wspace=0, hspace=0)
    plt.ylabel("Count")
    plt.margins(x=0, y=0)
    plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/"+topic+"/"+ topic+"_"+sentiment+"_community_sentiment_date.png")
    plt.show()

def barchart_sentiment_community(df,topic,topic_name,sentiment):
    #df_report = df.drop(columns=["Community"])
    fig, axes = plt.subplots(1, 5, figsize=(10, 3), sharex=True, sharey=True, dpi=250, )
    fig.suptitle(topic_name + ":\n" + sentiment)
    communities = df["Community"].value_counts().sort_values().iloc[-5:].index.tolist()
    df = df.loc[df["Community"].isin(communities)]
    hmax = 100
    for community, ax in enumerate(axes.flatten()):
        fig.add_subplot(ax)
        plt.gca().set_title('Community ' + str(communities[community]), fontdict=dict(size=8))
        subset = df.loc[df["Community"]==communities[community]]
        (subset[sentiment].value_counts()/subset.shape[0]*100).sort_index().plot(kind="bar",
                                                                                 color=["red", "gray", "green"],
                                                                                 fontsize=10,
                                                                                 figsize=(7, 5),
                                                                                 ax=ax)
        plt.gca().tick_params(labelrotation=0, labelsize=3)
        plt.gca().set_ylim([0,hmax])
        plt.subplots_adjust(wspace=0, hspace=0)
    plt.margins(x=0, y=0)
    #plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/"+topic+"/"+ topic+"_"+sentiment+"_community_sentiment.png")
    plt.show()

def barchart_sentiment_graph(df,topic,topic_name,sentiment):
    (df[sentiment].value_counts()/df.shape[0]*100).sort_index().plot(kind="bar",
                                                                     color=["red", "gray", "green"],
                                                                     fontsize=10,
                                                                     figsize=(7,5),
                                                                     ax=plt.gca(),
                                                                     rot=0,
                                                                     title= topic_name+"\n"+sentiment+" sentiment")
    plt.tight_layout()
    plt.ylim([0,100])
    plt.savefig("./../data/TOP_DOWN/"+topic+"/"+topic+"_"+sentiment+"_graph_sentiment")
    plt.show()

#vulnerability
def barplot_vulnerability_graph(df,topic,topic_name):
    stacked = df.groupby("day")["anger anx sad sexual risk death stress".split(" ")].sum()
    stacked.index = pd.to_datetime(stacked.index).day
    stacked.plot(kind='bar', stacked=True, fontsize=5, figsize=(7, 5),
                 title= topic_name+"\ngraph vulnerability", cmap="Dark2",rot=0)
    plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/"+topic+"/"+topic+"_"+"vulnerability"+"_barplot")
    plt.show()

def lineplot_vulnerability_graph(df,topic,topic_name):
    line = df.groupby("day")["mood_weigh"].sum()
    line.plot(fontsize=10, figsize=(7, 5),
                 title= topic_name+"\ngraph vulnerability", color="blue",)
    plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/"+topic+"/"+topic+"_"+"vulnerability"+"_lineplot.png")
    plt.show()

def lineplot_vulnerability_community(df,topic,topic_name):
    communities = df["Community"].value_counts().sort_values().iloc[-5:].index.tolist()
    df = df.loc[df["Community"].isin(communities)]

    df.groupby(["day", "Community"])["mood_weigh"].sum().unstack().plot(fontsize=5, figsize=(7, 5),
                 title= topic_name+"community:\n per community vulnerability", cmap="Dark2")
    plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/"+topic+"/"+topic+"_"+"_lineplot_communtiy.png")
    plt.show()

def barchart_vulnerability_community(df,topic,topic_name):
    #df_report = df.drop(columns=["Community"])
    fig, axes = plt.subplots(1, 5, figsize=(10, 3), sharex=True, sharey=True, dpi=250, )
    fig.suptitle(topic_name + "community:\n Vulnerability")
    communities = df["Community"].value_counts().sort_values().iloc[-5:].index.tolist()
    df = df.loc[df["Community"].isin(communities)]
    hmax = df.groupby("Community")["anger anx sad sexual risk death stress".split()].sum().max().max()
    for community, ax in enumerate(axes.flatten()):
        fig.add_subplot(ax)
        plt.gca().set_title('Community ' + str(communities[community]), fontdict=dict(size=8))
        subset = df.loc[df["Community"]==communities[community]]
        cat = subset.groupby("Community")["anger anx sad sexual risk death stress".split()].sum()/subset.groupby("Community")["anger anx sad sexual risk death stress".split()].sum().sum()#/subset.shape[0]

        cat.plot(kind="bar",color="black",ax=plt.gca(),legend=False)

        plt.gca().tick_params(labelrotation=0, labelsize=3)
        plt.gca().set_ylim([0,hmax])
        plt.subplots_adjust(wspace=0, hspace=0)
    plt.margins(x=0, y=0)

    plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/"+topic+"/"+topic+"_count_words.png")
    plt.show()

def barchart_stacked_vulnerability(df,topic,topic_name):
    communities = df["Community"].value_counts().sort_values().iloc[-5:].index.tolist()
    df = df.loc[df["Community"].isin(communities)]
    stacked = df.groupby("Community")["anger anx sad sexual risk death stress".split()].sum()
    #stacked.index = pd.to_datetime(stacked.index).day
    stacked.plot(kind="bar",stacked=True,
                 cmap="Dark2", rot=0,
                 fontsize=10, figsize=(7, 5),
                 title=topic_name + "\nVulnerability count per community").legend(loc='center left',bbox_to_anchor=(1.0, 0.5))
    plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/"+topic+"/"+topic+"_stacked_vulnerability.png")
    plt.show()

def barchart_vulnerability(df,topic,topic_name):
    df.groupby("Community")["anger anx sad sexual risk death stress".split()].sum().plot(kind="bar",
                                                                                                         cmap="Dark2",
                                                                                                         rot=0,
                                                                                                         fontsize=10,
                                                                                                         figsize=(7, 5),
                                                                                                         title=topic_name + "\nVulnerability count per community").legend(loc='center left',bbox_to_anchor=(1.0, 0.5))
    plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/"+topic+"/"+topic+"_"+"barchart_vulnerability.png")
    plt.show()

def barchart_vulnerability_total_weighted(df,topic,topic_name):
    weights = df.groupby("Community")["mood_weigh"].sum().sort_index()
    lenghts = df["Community"].value_counts().sort_index()
    (weights / lenghts).plot(kind="bar", color="black", rot=0, title=topic_name + "\nweighted total vulnerability",
                             fontsize=10, figsize=(7, 5))#.legend(loc='center left',bbox_to_anchor=(1.0, 0.5))
    plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/"+topic+"/"+topic+"_barchart_vulnerability_total_weighted")
    plt.show()

def barchart_vulnerability_community_weighted(df,topic,topic_name):
    weights = df.groupby("Community")["anger anx sad sexual risk death stress".split()].sum()
    lenghts = df["Community"].value_counts().sort_index()
    weights.divide(lenghts, axis=0).plot(kind="bar", cmap="Dark2", rot=0, title=topic_name + "\nvulnerability per community",
                                         fontsize=10, figsize=(7, 5)).legend(loc='center left',bbox_to_anchor=(1.0, 0.5))
    plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/"+topic+"/"+topic+"barchart_vulnerability_community_weighted.png")
    plt.show()

#wordcloud
def wordcloud_community(topic, df,topic_name):
    def color_function(*args, **kwargs):
        return '#000000'
    cloud = WordCloud(stopwords=stopwords.update(["covid","coronavirus"]),
                          background_color='white',
                          width=2500,
                          height=1800,
                          max_words=50,
                          color_func=color_function,
                          prefer_horizontal=1.0)

    fig, axes = plt.subplots(1, 5, figsize=(10, 3), sharex=True, sharey=True, dpi=250, )
    fig.suptitle(topic_name+"\n Wordcloud per community",color="red")
    communities = df["Community"].value_counts().sort_values().iloc[-5:].index.tolist()
    for community, ax in enumerate(axes.flatten()):
        subset = df.loc[df["Community"] == communities[community]]
        print("Plotting community" + str(community), "texts", subset["processed_text"].shape[0])
        fig.add_subplot(ax,title="Community "+str(community))

        vectorizer = CountVectorizer()
        bag_of_words = vectorizer.fit_transform(subset["stemmed_text"].dropna())
        sum_words = bag_of_words.sum(axis=0)
        words_freq = [(word, sum_words[0, idx]) for word, idx in vectorizer.vocabulary_.items()]
        words_freq = dict(sorted(words_freq, key=lambda x: x[1], reverse=True))
        del words_freq["covid"]
        del words_freq["coronaviru"]
        cloud.generate_from_frequencies(dict(words_freq))

        plt.gca().imshow(cloud)
        plt.gca().set_title('Community ' + str(communities[community]), fontdict=dict(size=12))
        plt.gca().axis('off')
    plt.subplots_adjust(wspace=0, hspace=0)
    plt.axis('off')
    plt.margins(x=0, y=0)
    plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/"+topic+"/"+ topic+"_wordcloud_community.png")
    plt.show()

def wordcloud_graph(topic, df,topic_name):
    def color_function(*args, **kwargs):
        return '#000000'
    cloud = WordCloud(stopwords=stopwords.update(["covid","coronavirus"]),
                          background_color='white',
                          width=2500,
                          height=1800,
                          max_words=50,
                          color_func=color_function,
                          prefer_horizontal=1.0)

    vectorizer = CountVectorizer()
    bag_of_words = vectorizer.fit_transform(df["stemmed_text"].dropna())
    sum_words = bag_of_words.sum(axis=0)
    words_freq = [(word, sum_words[0, idx]) for word, idx in vectorizer.vocabulary_.items()]
    words_freq = dict(sorted(words_freq, key=lambda x: x[1], reverse=True))
    del words_freq["covid"]
    del words_freq["coronaviru"]
    cloud.generate_from_frequencies(words_freq)

    plt.title(topic_name+"\nWordcloud", color="red",fontdict=dict(size=(24)))
    plt.savefig("./../data/TOP_DOWN/" + topic + "/" + topic + "_wordcloud_graph.png")
    plt.imshow(cloud)
    plt.axis('off')
    plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/" + topic + "/" + topic + "_wordcloud_graph.png")
    plt.show()

if __name__ == "__main__":
    topic = "Topic3" #"Topic2" "Topic1" #"Topic3"
    topic_name = "Symptoms&Hospitalization" #"Vaccines","Social distancing" #"Symptoms&Hospitalization"
    df = pd.read_pickle("./../data/TOP_DOWN/"+topic+"_tweets.pkl")
    #community = pd.read_csv("./../data/TOP_DOWN/" + topic + "/" + topic + "_community.csv")[["Id", "modularity_class"]]
    #community = community.rename(columns={"Id":"user_name","modularity_class":"Community"})

    #df = sanitize.sanitize_tweets_database(df)
    #df = df.merge(community, on="user_name")
    print("DETTAGLIO", topic)
    print("Vulnerabilità totale", df["mood_weigh"].sum())
    print("Vulnerabilità pesata tweet", df["mood_weigh"].sum() / df["mood_weigh"].shape[0])
    print("Vulnerabilità pesata user", df["mood_weigh"].sum() / df["user_name"].unique().shape[0])

    communities = df["Community"].value_counts().sort_values().iloc[-5:].index.tolist()
    #df.columns = utils._COLUMNS_+["day","Community"]
    df = df.loc[df["Community"].isin(communities)]

    barchart_vulnerability_community_weighted(df,topic,topic_name)



    print(df.groupby("Community")["VADER"].count())
    print(df.head())
    print(df.shape)
    print("TOTAL VALUES SENTIMENT")
    print((df["VADER"].value_counts() / df["VADER"].shape[0]).sort_index())
    print((df["CT_BERT"].value_counts() / df["VADER"].shape[0]).sort_index())

    print("VADER ON COMMUNITY")
    for i in df["Community"].unique().tolist():
        subset = df.loc[df["Community"] == i]["VADER"]
        print("community", i)
        print((subset.value_counts() / subset.shape[0]).sort_index())

    print("CT_BERT ON COMMUNITY")
    for i in df["Community"].unique().tolist():
        subset = df.loc[df["Community"] == i]["CT_BERT"]
        print("community", i)
        print((subset.value_counts() / subset.shape[0]).sort_index())

    #sentiment
    def getSentiment():
        #barchart_sentiment_community_bydate(df=df,topic=topic,topic_name=topic_name, sentiment="VADER")
        #barchart_sentiment_community_bydate(df=df,topic=topic,topic_name=topic_name, sentiment="CT_BERT")

        barchart_sentiment_graph_bydate(df=df,topic=topic,topic_name=topic_name, sentiment="VADER")
        barchart_sentiment_graph_bydate(df=df,topic=topic,topic_name=topic_name, sentiment="CT_BERT")

        barchart_sentiment_graph(df=df,topic=topic,topic_name=topic_name, sentiment="VADER")
        barchart_sentiment_graph(df=df,topic=topic,topic_name=topic_name, sentiment="CT_BERT")

        barchart_sentiment_community(df=df,topic=topic,topic_name=topic_name, sentiment="VADER")
        barchart_sentiment_community(df=df,topic=topic,topic_name=topic_name, sentiment="CT_BERT")
    getSentiment()

    #vulnerability
    def getVulnerability():
        lineplot_vulnerability_graph(df=df,topic=topic,topic_name=topic_name,)
        lineplot_vulnerability_community(df=df,topic=topic,topic_name=topic_name,)

        barplot_vulnerability_graph(df=df,topic=topic,topic_name=topic_name,)
        barchart_vulnerability(df=df,topic=topic,topic_name=topic_name,)
        barchart_stacked_vulnerability(df=df,topic=topic,topic_name=topic_name,)
        barchart_vulnerability_community(df=df,topic=topic,topic_name=topic_name,)

        barchart_vulnerability_total_weighted(df, topic, topic_name)
        barchart_vulnerability_community_weighted(df, topic, topic_name)

    getVulnerability()

    stacked = df.groupby("Community")["anger anx sad sexual risk death stress".split()].sum()
    #stacked.index = pd.to_datetime(stacked.index).day
    stacked.plot(kind="bar",stacked=True,
                 cmap="Dark2", rot=0,
                 fontsize=10, figsize=(7, 5),
                 title=topic_name + "\nVulnerability count per community").legend(loc='center left',bbox_to_anchor=(1.0, 0.5))
    plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/"+topic+"/"+topic+"_stacked_vulnerability.png")
    plt.show()

    #wordcloud
    print("BEGIN WoRDCloUD")
    wordcloud_graph(df=df,topic=topic,topic_name=topic_name)
    wordcloud_community(df=df, topic=topic, topic_name=topic_name)
    print("END WoRDCloUD")

    #top k words for every category
    from collections import Counter
    terms = df[[x for x in df.columns if "terms" in x]]
    for term in terms.columns:
        terms_counter = Counter(" ".join(terms[term].dropna().ravel()).split(" ")).most_common(25)
        freq = pd.DataFrame(terms_counter, columns=["term", "count"])
        freq.to_csv("./../data/TOP_DOWN/"+topic+"/terms/"+topic+"_"+term+".csv",index=False)

    #BARPLOT FOR SINGLES CATEGORY
    fig, ax = plt.subplots(1, 3, figsize=(100, 50))
    fig.suptitle('Categories for risk scenario', color="#d62d20", )
    x = 0
    color_map = ["#008744", "#0057e7", "#ffa700"]
    for topic, topic_name in zip(["Topic1", "Topic2", "Topic3"],
                                 ["Social distancing", "Vaccines", "Symptoms&Hospitalization"]):
        df = pd.read_pickle("./../data/TOP_DOWN/" + topic + "_tweets.pkl")
        stacked = df["anger anx sad sexual risk death stress".split()].sum() / df["anger anx sad sexual risk death stress".split()].sum().sum()
        stacked.plot(kind="bar", stacked=True,
                     color=color_map[x], rot=0,
                     fontsize=5, figsize=(7, 5),
                     title=topic_name, ax=ax[x])
        x = x + 1
    for ax in fig.get_axes():
        ax.label_outer()
        ax.set_ylim([0, 0.6])
    plt.tight_layout()
    plt.savefig("./../data/TOP_DOWN/top_down_categories.png")
    plt.show()