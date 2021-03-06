import re
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.model_selection import StratifiedKFold
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.layers import Dense, Input, LSTM, Embedding, Dropout
from keras.layers.core import Lambda
from keras.layers.merge import concatenate, add, multiply
from keras.models import Model
from keras.layers.normalization import BatchNormalization
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.layers.noise import GaussianNoise
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import stopwords


from nltk import word_tokenize
import re
import nltk
# nltk.download('punkt')
import chardet
import itertools
import logging
import unicodedata
import string
import os
import sys
import inflect

tkz = nltk.data.load('tokenizers/punkt/english.pickle')
p = inflect.engine()
punctuation = set(string.punctuation)
punctuation.update(["``", "`", "..."])


np.random.seed(0)
WNL = WordNetLemmatizer()
STOP_WORDS = set(stopwords.words('english'))
MAX_SEQUENCE_LENGTH = 30
MIN_WORD_OCCURRENCE = 100
REPLACE_WORD = "memento"
EMBEDDING_DIM = 300
NUM_FOLDS = 10
BATCH_SIZE = 1025
EMBEDDING_FILE = "glove.840B.300d.txt"


# def cutter(word):
#     if len(word) < 4:
#         return word
#     return WNL.lemmatize(WNL.lemmatize(word, "n"), "v")


# def preprocess(string):
#     string = string.lower().replace(",000,000", "m").replace(",000", "k").replace("′", "'").replace("’", "'") \
#         .replace("won't", "will not").replace("cannot", "can not").replace("can't", "can not") \
#         .replace("n't", " not").replace("what's", "what is").replace("it's", "it is") \
#         .replace("'ve", " have").replace("i'm", "i am").replace("'re", " are") \
#         .replace("he's", "he is").replace("she's", "she is").replace("'s", " own") \
#         .replace("%", " percent ").replace("₹", " rupee ").replace("$", " dollar ") \
#         .replace("€", " euro ").replace("'ll", " will").replace("=", " equal ").replace("+", " plus ")
#     string = re.sub('[“”\(\'…\)\!\^\"\.;:,\-\?？\{\}\[\]\\/\*@]', ' ', string)
#     string = re.sub(r"([0-9]+)000000", r"\1m", string)
#     string = re.sub(r"([0-9]+)000", r"\1k", string)
#     string = ' '.join([cutter(w) for w in string.split()])
#     return string

def to_singular(word, p):
    if (nltk.pos_tag([word])[0][1] == 'PRP') or (word == 'his'): return word
    x = p.singular_noun(word)
    if x==False: return word
    return x


def strip_accents_unicode(s):
    try:
        s = unicode(s, 'utf-8')
    except:  # unicode is a default on python 3
        pass
    s = unicodedata.normalize('NFD', s)
    s = s.encode('ascii', 'ignore')
    s = s.decode("utf-8")
    return str(s)

def preprocess(text, remove_sw = False, stem_words=True):
    text = re.sub(r"€", " euro ", text)
    text = re.sub(r"₹", " rupee ", text)
    text = strip_accents_unicode(text.lower())
    text = re.sub(r",000,000", "m", text)
    text = re.sub(r",000", "k", text)
    text = re.sub(r".000.000", "m", text)
    text = re.sub(r".000", "k", text)
    text = re.sub(r"000 ", "k ", text)
    text = re.sub(r"000000 ", "m ", text)
    text = re.sub(r"′", "'", text)
    text = re.sub(r"’", "'", text)
    text = re.sub(r'agaist', 'against', text)
    text = re.sub(r"what's", "what is", text)
    text = re.sub(r"\'ve ", " have ", text)
    text = re.sub(r"can't", "can not ", text)
    text = re.sub(r"won't", "will not ", text)
    text = re.sub(r" cannot ", " can not ", text)
    text = re.sub(r"n't", " not ", text)
    text = re.sub(r"i'm", "i am", text)
    text = re.sub(r" m ", " am ", text)
    text = re.sub(r"it's ", "it is ", text)
    text = re.sub(r"he's ", "he is ", text)
    text = re.sub(r"she's ", "she is ", text)
    text = re.sub(r"\'re ", " are ", text)
    text = re.sub(r"\'d ", " would ", text)
    text = re.sub(r"\'ll ", " will ", text)
    text = re.sub(r" e g ", " eg ", text)
    text = re.sub(r" b g ", " bg ", text)
    text = re.sub(r"\0s", "0", text)
    text = re.sub(r" 9 11 ", " 911 ", text)
    text = re.sub(r" 9/11 ", " 911 ", text)
    text = re.sub(r" 9-11 ", " 911 ", text)
    text = re.sub(r" e-mail ", " email ", text)
    text = re.sub(r"quikly", "quickly", text)
    text = re.sub(r" usa ", " america ", text)
    text = re.sub(r" u s ", " america ", text)
    text = re.sub(r" uk ", " england ", text)
    text = re.sub(r"imrovement", "improvement", text)
    text = re.sub(r"intially", "initially", text)
    text = re.sub(r"qoura", "quora", text)
    text = re.sub(r" dms ", "direct messages ", text)  
    text = re.sub(r"demonitization", "demonetization", text) 
    text = re.sub(r"actived", "active", text)
    text = re.sub(r" kms ", " kilometers ", text)
    text = re.sub(r" cs ", " computer science ", text) 
    text = re.sub(r" upvotes ", " up votes ", text)
    text = re.sub(r" upvote ", " up vote ", text)
    text = re.sub(r" downvotes ", " down votes ", text)
    text = re.sub(r" downvote ", " down vote ", text)
    text = re.sub(r"calender", "calendar", text)
    text = re.sub(r"ios", "operating system", text)
    text = re.sub(r"programing", "programming", text)
    text = re.sub(r"bestfriend", "best friend", text)
    text = re.sub(r" bf ", " best friend ", text)
    text = re.sub(r" iii ", " 3 ", text) 
    text = re.sub(r" ii ", " 2 ", text)
    text = re.sub(r"gta v ", "gta 5 ", text) 
    text = re.sub(r" the united states of america ", " america ", text)
    text = re.sub(r" the united states ", " america ", text)
    text = re.sub(r" j k ", " jk ", text)
    text = re.sub(r"%", " percent ", text)
    text = re.sub(r"rupees ", " rupee ", text)
    text = re.sub(r" rs", " rupee ", text)
    text = re.sub(r"\$", " dollar ", text)
    text = re.sub(r"emoticon", " emoji ", text)
    text = re.sub(r"emoticons", " emoji ", text)
    text = re.sub(r"smileys", " emoji ", text)
    text = re.sub(r"smiley", " emoji ", text)
    text = re.sub(r"emojis", " emoji ", text)
    text = re.sub(r"[^A-Za-z0-9]", " ", text)
    text = re.sub('[“”\(\'…\)\!\^\"\.;:,\-\?？\{\}\[\]\\/\*@]', ' ', text)


    # Remove punctuation from text
    text = ''.join([c for c in text if c not in punctuation])
    # Optionally, remove stop words
    if remove_sw:
        text = text.split()
        text = [w for w in text if not w in stop_words]
        text = " ".join(text)
    
    # Optionally, shorten words to their stems
    if stem_words:
        text = word_tokenize(text)
        verbs_stemmer = WordNetLemmatizer()
        #temmed_words = [verbs_stemmer.lemmatize(verbs_stemmer.lemmatize(word.lower(),'n'), 'v') for word in text]
        stemmed_words = [to_singular(verbs_stemmer.lemmatize(word.lower(), 'v'), p) for word in text]
        text = " ".join(stemmed_words)
    
    # Return a list of words
    return text


def get_embedding():
    embeddings_index = {}
    f = open(EMBEDDING_FILE, encoding='utf8')
    for line in f:
        values = line.split()
        word = values[0]
        if len(values) == EMBEDDING_DIM + 1 and word in top_words:
            coefs = np.asarray(values[1:], dtype="float32")
            embeddings_index[word] = coefs
    f.close()
    return embeddings_index


def is_numeric(s):
    return any(i.isdigit() for i in s)


def prepare(q):
    new_q = []
    surplus_q = []
    numbers_q = []
    new_memento = True
    for w in q.split()[::-1]:
        if w in top_words:
            new_q = [w] + new_q
            new_memento = True
        elif w not in STOP_WORDS:
            if new_memento:
                new_q = ["memento"] + new_q
                new_memento = False
            if is_numeric(w):
                numbers_q = [w] + numbers_q
            else:
                surplus_q = [w] + surplus_q
        else:
            new_memento = True
        if len(new_q) == MAX_SEQUENCE_LENGTH:
            break
    new_q = " ".join(new_q)
    return new_q, set(surplus_q), set(numbers_q)


def extract_features(df):
    q1s = np.array([""] * len(df), dtype=object)
    q2s = np.array([""] * len(df), dtype=object)
    features = np.zeros((len(df), 4))

    for i, (q1, q2) in enumerate(list(zip(df["question1"], df["question2"]))):
        q1s[i], surplus1, numbers1 = prepare(q1)
        q2s[i], surplus2, numbers2 = prepare(q2)
        features[i, 0] = len(surplus1.intersection(surplus2))
        features[i, 1] = len(surplus1.union(surplus2))
        features[i, 2] = len(numbers1.intersection(numbers2))
        features[i, 3] = len(numbers1.union(numbers2))

    return q1s, q2s, features

train = pd.read_csv("data/train.csv")
test = pd.read_csv("data/test.csv")

train["question1"] = train["question1"].fillna("").apply(preprocess)
train["question2"] = train["question2"].fillna("").apply(preprocess)

print("Creating the vocabulary of words occurred more than", MIN_WORD_OCCURRENCE)
all_questions = pd.Series(train["question1"].tolist() + train["question2"].tolist()).unique()
vectorizer = CountVectorizer(lowercase=False, token_pattern="\S+", min_df=MIN_WORD_OCCURRENCE)
vectorizer.fit(all_questions)
top_words = set(vectorizer.vocabulary_.keys())
top_words.add(REPLACE_WORD)

embeddings_index = get_embedding()
print("Words are not found in the embedding:", top_words - embeddings_index.keys())
top_words = embeddings_index.keys()

print("Train questions are being prepared for LSTM...")
q1s_train, q2s_train, train_q_features = extract_features(train)

tokenizer = Tokenizer(filters="")
tokenizer.fit_on_texts(np.append(q1s_train, q2s_train))
word_index = tokenizer.word_index

data_1 = pad_sequences(tokenizer.texts_to_sequences(q1s_train), maxlen=MAX_SEQUENCE_LENGTH)
data_2 = pad_sequences(tokenizer.texts_to_sequences(q2s_train), maxlen=MAX_SEQUENCE_LENGTH)
labels = np.array(train["is_duplicate"])

nb_words = len(word_index) + 1
embedding_matrix = np.zeros((nb_words, EMBEDDING_DIM))

for word, i in word_index.items():
    embedding_vector = embeddings_index.get(word)
    if embedding_vector is not None:
        embedding_matrix[i] = embedding_vector


print("Train features are being merged with NLP and Non-NLP features...")
train_nlp_features = pd.read_csv("data/nlp_features_train.csv")
train_non_nlp_features = pd.read_csv("data/non_nlp_features_train.csv")
features_train = np.hstack((train_q_features, train_nlp_features, train_non_nlp_features))

print("Same steps are being applied for test...")
test["question1"] = test["question1"].fillna("").apply(preprocess)
test["question2"] = test["question2"].fillna("").apply(preprocess)
q1s_test, q2s_test, test_q_features = extract_features(test)
test_data_1 = pad_sequences(tokenizer.texts_to_sequences(q1s_test), maxlen=MAX_SEQUENCE_LENGTH)
test_data_2 = pad_sequences(tokenizer.texts_to_sequences(q2s_test), maxlen=MAX_SEQUENCE_LENGTH)
test_nlp_features = pd.read_csv("data/nlp_features_test.csv")
test_non_nlp_features = pd.read_csv("data/non_nlp_features_test.csv")
features_test = np.hstack((test_q_features, test_nlp_features, test_non_nlp_features))


skf = StratifiedKFold(n_splits=NUM_FOLDS, shuffle=True)
model_count = 0

for idx_train, idx_val in skf.split(train["is_duplicate"], train["is_duplicate"]):
    print("MODEL:", model_count)
    data_1_train = data_1[idx_train]
    data_2_train = data_2[idx_train]
    labels_train = labels[idx_train]
    f_train = features_train[idx_train]

    data_1_val = data_1[idx_val]
    data_2_val = data_2[idx_val]
    labels_val = labels[idx_val]
    f_val = features_train[idx_val]

    embedding_layer = Embedding(nb_words,
                                EMBEDDING_DIM,
                                weights=[embedding_matrix],
                                input_length=MAX_SEQUENCE_LENGTH,
                                trainable=False)
    lstm_layer = LSTM(75, recurrent_dropout=0.2)

    sequence_1_input = Input(shape=(MAX_SEQUENCE_LENGTH,), dtype="int32")
    embedded_sequences_1 = embedding_layer(sequence_1_input)
    x1 = lstm_layer(embedded_sequences_1)

    sequence_2_input = Input(shape=(MAX_SEQUENCE_LENGTH,), dtype="int32")
    embedded_sequences_2 = embedding_layer(sequence_2_input)
    y1 = lstm_layer(embedded_sequences_2)

    features_input = Input(shape=(f_train.shape[1],), dtype="float32")
    features_dense = BatchNormalization()(features_input)
    features_dense = Dense(200, activation="relu")(features_dense)
    features_dense = Dropout(0.2)(features_dense)

    addition = concatenate([x1, y1])
    minus_y1 = Lambda(lambda x: -x)(y1)
    merged = add([x1, minus_y1])
    merged = multiply([merged, merged])
    merged = concatenate([merged, addition])
    merged = Dropout(0.4)(merged)

    merged = concatenate([merged, features_dense])
    merged = BatchNormalization()(merged)
    merged = GaussianNoise(0.1)(merged)

    merged = Dense(150, activation="relu")(merged)
    merged = Dropout(0.2)(merged)
    merged = BatchNormalization()(merged)

    out = Dense(1, activation="sigmoid")(merged)

    model = Model(inputs=[sequence_1_input, sequence_2_input, features_input], outputs=out)
    model.compile(loss="binary_crossentropy",
                  optimizer="nadam")
    early_stopping = EarlyStopping(monitor="val_loss", patience=5)
    best_model_path = "best_model" + str(model_count) + ".h5"
    model_checkpoint = ModelCheckpoint(best_model_path, save_best_only=True, save_weights_only=True)

    hist = model.fit([data_1_train, data_2_train, f_train], labels_train,
                     validation_data=([data_1_val, data_2_val, f_val], labels_val),
                     epochs=15, batch_size=BATCH_SIZE, shuffle=True,
                     callbacks=[early_stopping, model_checkpoint], verbose=1)

    model.load_weights(best_model_path)
    print(model_count, "validation loss:", min(hist.history["val_loss"]))

    preds = model.predict([test_data_1, test_data_2, features_test], batch_size=BATCH_SIZE, verbose=1)

    submission = pd.DataFrame({"test_id": test["test_id"], "is_duplicate": preds.ravel()})
    submission.to_csv("lstm_preds" + str(model_count) + ".csv", index=False)

    model_count += 1