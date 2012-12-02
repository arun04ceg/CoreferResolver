import sys
import re
from np_chunker import fetch_np_chunks

coref_pattern = re.compile('<COREF ID="(?P<ref_id>.*?)">(?P<text>.*?)</COREF>', re.DOTALL)

apostrope_pattern = re.compile("(?P<word>[^ ]*?)'s")

def parse_input(filename):
    in_file = open(filename)
    text = in_file.read()
    in_file.close()
    
    actual_text = text
    text = text.replace("<TXT>", "")
    text = text.replace("</TXT>", "")
 
    coref_list = coref_pattern.findall(text)
    text = re.sub(coref_pattern, replace_function, text)
    np_chunks, np_chunks_words, appositives_map, sentences = fetch_np_chunks(text, filename)

    apostroped_nps = apostrope_pattern.findall(text)

    coref_np_list, inverse_coref_dict, max_coref, id_to_np = get_ref_dict(coref_list)
    return coref_np_list, inverse_coref_dict, id_to_np, np_chunks, np_chunks_words, actual_text, max_coref, apostroped_nps, sentences

def get_pronouns(filename):
    pronouns = set()
    in_file = open(filename)
    for line in in_file:
        line = line.strip()
        pronouns.add(line.lower())
    in_file.close()
    return pronouns

def replace_function(match_obj):
    return match_obj.group("text")

def get_ref_dict(coref_list):
    coref_np_list, inverse_coref_dict = [], {}
    id_to_np = {}
    np_to_coref = {}
    max_coref = "-1"
    for coref_id, text in coref_list:
        coref_np_list.append((coref_id, set([text])))
        id_to_np[coref_id] = text
        coref_id_list = inverse_coref_dict.setdefault(text, [])
        coref_id_list.append(coref_id)
        coref_id_list.sort(key = lambda x : sort_function(x))
        if int(coref_id) > int(max_coref):
            max_coref = coref_id
    return coref_np_list, inverse_coref_dict, max_coref, id_to_np

def sort_function(string):
    new_str = ""
    for ii in range(len(string) - 1, -1, -1):
        try:
           int(string[ii])
           new_str = string[ii] + new_str
        except:
           break
    if new_str:
        return int(new_str)
    return string

if __name__ == "__main__":
    parse_input(sys.argv[1])
