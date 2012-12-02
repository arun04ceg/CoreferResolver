import sys
import re
from nltk import word_tokenize, pos_tag
from nltk.corpus import conll2000
from SentenceTokenize import SentenceTokenize
from WordTokenize import WordTokenize

def fetch_np_chunks(text, filename):
    S = SentenceTokenize(text)
    sentences = S.get_sentences()

    W = WordTokenize()

    outfile = open("temp_np.txt", "w")
    for index, each_sentence in enumerate(sentences):
        each_sentence = each_sentence.strip()
        text = word_tokenize(each_sentence)
        tagged_sentence = pos_tag(text)
        parsed_data = W.parse(tagged_sentence)
        outfile.write(parsed_data.pprint())
        outfile.write("\n")
    outfile.close()
    np_chunks, np_chunks_words, appositives = get_np_chunks("temp_np.txt")
    return np_chunks, np_chunks_words, appositives, sentences

np_format = re.compile(r'(?P<word>.*?)/(?P<pos>.*?)( |[)]$)')

def get_np_chunks(filename):
    in_file = open(filename)
    np_chunks = []
    np_chunks_words = []
    appositive_map = {}
    comma = False
    prev_np = ""
    for line in in_file:
        line = line.strip()
        if line.startswith("(S"):
            sentence = []
            sentence_words = []
            np_chunks.append(sentence)
            np_chunks_words.append(sentence_words)
        else:
            line = line.strip()
            if line.startswith("(NP"):
                np_chunk = []
                words = [] 
                for match_obj in np_format.finditer(line[4:]):
                    np_chunk.append((match_obj.group("word"), match_obj.group("pos")))
                    words.append(match_obj.group("word"))
                sentence.append(np_chunk)
                sentence_words.append(" ".join(words))
                if comma:
                    comma = False
                if prev_np:
                    appositive_map[prev_np] = " ".join(words)
                    appositive_map[" ".join(words)] = prev_np
                    prev_np = ""
            if line.startswith(",/,"):
                if sentence_words:
                    comma = True
                    prev_np = sentence_words[-1]
    return np_chunks, np_chunks_words, appositive_map
    in_file.close()

def get_pronouns(filename):
    pronouns = set()
    in_file = open(filename)
    for line in in_file:
        line = line.strip()
        pronouns.add(line.lower())
    in_file.close()
    return pronouns


if __name__ == "__main__":
    main(sys.argv[1]) 
