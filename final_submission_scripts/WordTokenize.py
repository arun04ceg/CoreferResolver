import text_chunker.load

class WordTokenize():
    def __init__(self):
        self.chunker = text_chunker.load.load_chunker()
        
    def parse(self, tagged_sentence):
        return self.chunker.parse(tagged_sentence)
