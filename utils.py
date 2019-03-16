import re
import numpy as np
from keras.layers.embeddings import Embedding
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from keras.preprocessing.text import one_hot
from keras.preprocessing.sequence import pad_sequences

def readGloveFile(gloveFile):
    with open(gloveFile, 'r') as f:
        wordToGlove = {}  
        wordToIndex = {} 
        indexToWord = {} 

        for line in f:
            record = line.strip().split()
            token = record[0] 
            wordToGlove[token] = np.array(record[1:], dtype=np.float64) 

        tokens = sorted(wordToGlove.keys())
        for idx, tok in enumerate(tokens):
            kerasIdx = idx + 1  
            wordToIndex[tok] = kerasIdx 
            indexToWord[kerasIdx] = tok 

    return wordToIndex, indexToWord, wordToGlove

def createPretrainedEmbeddingLayer(wordToGlove, wordToIndex, isTrainable):
    vocabLen = len(wordToIndex) + 1  
    embDim = next(iter(wordToGlove.values())).shape[0] 

    embeddingMatrix = np.zeros((vocabLen, embDim))
    for word, index in wordToIndex.items():
        embeddingMatrix[index, :] = wordToGlove[word] 

    embeddingLayer = Embedding(vocabLen, embDim, weights=[embeddingMatrix], trainable=isTrainable)
    return embeddingLayer

def clean_review(review):
    review = review.lower()
    review = re.sub(r'''(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))''', '', review, flags=re.MULTILINE)
    review = re.sub(r'(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)', '', review)
    review = re.sub(r'\b[0-9]+\b\s*', '', review)
    return review

def generate_batch(X, y, batch_size, vocab_length, max_length, no_classes):
    counter = 0
    X = X[0: int(len(X) / batch_size) * batch_size]
    y = y[0: int(len(y) / batch_size) * batch_size]
    
    while True:
        tempIndex = X[counter:counter + batch_size]
        reviews = []    
        for rev in tempIndex:
            with open('dataset/reviewstxt/' + str(rev) + '.txt', 'r') as file:
                review = file.read()
                review = clean_review(review)            
                review = word_tokenize(review)            
                review = [t for t in review if t.isalpha()]
                stop_words = set(stopwords.words('english'))
                review = [t for t in review if not t in stop_words]            
                review = " ".join(review)        
                review_hot = one_hot(review, vocab_length)            
                reviews.append(review_hot)
                
        if len(reviews) <= 0:
          counter = 0
          continue
      
        reviews = pad_sequences(reviews, maxlen=max_length, padding='post')            
        tempStars = y[counter:counter + batch_size]    
        counter = (counter + batch_size) % len(X) 
        
        assert reviews.shape == (batch_size, max_length), "{} is not matching with {}".format(reviews.shape, (batch_size, max_length))
        assert tempStars.shape == (batch_size, no_classes), "{} is not matching with {}".format(tempStars.shape, (batch_size, no_classes))    
        
        yield reviews, tempStars