from nltk import sent_tokenize

class SentenceTokenize:
    def __init__(self, text):
        self.sentences = sent_tokenize(text)

    def get_sentences(self):
        return self.sentences 
