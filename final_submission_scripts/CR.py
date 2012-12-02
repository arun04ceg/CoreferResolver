import os
import re
import copy
from parse_input import parse_input, apostrope_pattern, sort_function
from nltk.corpus import wordnet

class CR:
    def __init__(self, input_file):
        self.coref_np_list, self.inverse_coref_dict, self.id_to_np, self.np_chunks, self.np_chunks_words, self.text, self.max_coref, self.apostophed_nps, self.sentences = parse_input(input_file)
        self.orig_inverse_coref_dict = copy.copy(self.inverse_coref_dict)
        self.ref_dict = {}
        self.method_list = [
                            self.handle_alises,
                            #self.appositives,
                            self.handle_dates,
                            self.match_head_nouns,
                            self.handle_hyphens,
                            #self.special_case_appositives,
                            self.anonymous_shuffling,
                            self.np_preceded_by_article,
                            self.synonym_match,
                            self.plain_string_match_on_NPs,
                            self.plain_string_match,
                            self.get_title_based_matches,
                           ]
        self.articles = ["A", "An", "The"]
        self.remove_articles_from_phrase_pattern = re.compile('(a|an|the)\s+(?P<phrase>.*)$')
        self.suffices = ["Corp.", "Co."]
        self.titles = ["Mr." , "Mrs." , "Ms." , "Dr."]
        self.out_filename = os.path.splitext(os.path.basename(input_file))[0] + os.path.extsep + "response"
        self.tag_format = '<COREF ID="(?P<coref_id>%s)">(?P<np>%s)</COREF>'
        self.new_coref_ids = set()
        self.additional_synonyms = {"aircraft" : "plane", "plane" : "aircraft"}
        self.number_words = set(["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"])
        self.date_format = re.compile("(?P<date>[0-9][0-9]) (?P<month>jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec) (?P<year>[0-9][0-9][0-9][0-9])")
        self.date_format_1 = re.compile("(?P<month>[0-9][0-9])-(?P<date>[0-9][0-9])-(?P<year>[0-9][0-9])")
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.month_map = {1 : ("Jan", "January"), 2 : ("Feb", "February"), 3 : ("Mar", "March"), 4 : ("Apr", "April"), 5 : ("May", "May"), 6 : ("Jun", "June"), 7 : ("Jul", "July"), 8 : ("Aug", "August"), 9 : ("Sep", "September"), 10 : ("Oct", "October"), 11: ("Nov", "November"), 12 : ("Dec", "December")}
        
    def plain_string_match(self,  coref_id,np):
        np = np.replace("'", "").replace("`", "")
        for each_sentence in self.np_chunks_words:
            for each_np in each_sentence: 
                each_np = each_np.replace("'", "").replace("`", "")
                if  np.lower() in each_np.lower():
                    return each_np 
        else:
            return False

    def handle_dates(self, coref_id, np):
        if self.date_format_1.match(np.lower()):
            match_obj = self.date_format_1.match(np.lower())
            month, date, year = match_obj.group("month"), match_obj.group("date"), match_obj.group("year")
            format = re.compile("(?P<date>\s+%s-%s\s+)" %(month, date))
            for each_sentence in self.sentences:
                list = format.findall(each_sentence)
                if list:
                    return "%s-%s" %(month, date)


        if self.date_format.match(np.lower()):
            format = re.compile("(?P<day>Mon|Tue|Wed|Thu|Fri|Sat|Sun) +%s" % np)
            for each_sentence in self.sentences:
                match_obj = format.findall(each_sentence)
                if match_obj:
                    return match_obj[0]

            format = re.compile("(?P<day>[Mm]onday|[Tt]uesday|[Ww]ednesday|[Tt]hursday|[Ff]riday|[Ss]aturday|[Ss]unday) ([Mm]orning|[Aa]fternoon|[Ee]vening|[nN]ight) +%s" % np)
            for each_sentence in self.sentences:
                match_obj = format.findall(each_sentence)
                if match_obj:
                    return match_obj[0][0]

        time_set = set(["eve"])
        for each_item in time_set:
           if each_item in np.lower():
               format = re.compile("(?P<day>[Mm]onday|[Tt]uesday|[Ww]ednesday|[Tt]hursday|[Ff]riday|[Ss]aturday|[Ss]unday)\s+(is|was)\s+%s" % np)
               for each_sentence in self.sentences:
                   each_sentence = vtv_compress_space(each_sentence)
                   match_obj = format.findall(each_sentence)
                   if match_obj:
                       return match_obj[0][0]

        return False 

    def handle_alises(self, coref_id, np):
        alias_names = ["looked like", "also known as"]
        for index, sentence in enumerate(self.sentences):
            if np.lower() not in sentence.lower():
                continue
            for each_item in alias_names:
                format = re.compile("%s\s+%s" %(each_item, np.lower()))
                if format.findall(sentence.lower()):
                    np_chunks = self.np_chunks_words[index]
                    prev_chunk = ""
                    for each_np_chunk in np_chunks:
                        if each_np_chunk.lower() in np.lower():
                            if prev_chunk:
                                return prev_chunk
                        if each_np_chunk in ["", "amp", "MD"]:
                            prev_chunk = prev_chunk
                            continue
                        prev_chunk = each_np_chunk
        else:
            return False    


    def post_process_dates(self):
        for np, coref_id_list in self.inverse_coref_dict.iteritems():
            match_obj = self.date_format_1.match(np.lower())
            variant_set = set()
            if match_obj:
                month, date, year = match_obj.group("month"), match_obj.group("date"), match_obj.group("year")
                month_text = self.month_map.get(int(month))
                if month_text:
                    variant = "%s. %s" %(month_text[0], date)
                    variant_set.add(variant)
                    variant = "%s %s" %(month_text[1], date)
                    variant_set.add(variant)
                

            for each_np, coref_id_list in self.inverse_coref_dict.iteritems():
                 if each_np == np:
                     continue
                 if each_np in variant_set:
                     coref_id_list = self.inverse_coref_dict.get(each_np)
                     if coref_id_list:
                         new_id_list = self.inverse_coref_dict.get(np)
                         if new_id_list:
                             coref_id_list.extend(new_id_list)
                             self.inverse_coref_dict[np] = coref_id_list
        return False
    
    def appositives(self, coref_id, np):
        format = re.compile("(?P<prefix>.*?), *%s" %vtv_compress_space(np).lower())
        for index, each_sentence in enumerate(self.sentences):
            if vtv_compress_space(np).lower() in vtv_compress_space(each_sentence).lower():
                match_obj = format.match(vtv_compress_space(each_sentence).lower())
                if match_obj:
                    prefix = match_obj.group("prefix")
                    np_chunks = self.np_chunks_words[index]
                    for index,  each_np_chunk in enumerate(np_chunks):
                        if each_np_chunk.lower() in np.lower():
                            if index != 0:
                                print self.ref_dict.get(coref_id)
                                print coref_id, np, np_chunks[index - 1]
                                return np_chunks[index - 1]
                            
                        '''
                        if each_np_chunk.lower() in prefix.lower():
                            return each_np_chunk
                        '''
        else:
            return False  

    '''
    def special_case_appositives(self, coref_id, np):
        format = re.compile("(?P<prefix>.*?), *.*?%s," % re.escape(np))
        for index, each_sentence in enumerate(self.sentences):
            if vtv_compress_space(np).lower() in vtv_compress_space(each_sentence).lower():
                 match_obj = format.match(each_sentence)
                 if match_obj:
                     return match_obj.group("prefix")
        else:
            return False
    '''

    '''
    def appositives(self, coref_id, np):
        #import pdb; pdb.set_trace();
        #print np
        for each_sentence in self.np_chunks_words:
            for each_np in each_sentence:
                if np.lower() in each_np and np.lower() in self.text:
                    if(each_sentence[each_sentence.index(each_np) - 1]) in self.text and each_np in self.text:
                        nptindex = self.text.index(each_np)
                        if self.text[nptindex - 2] == ',':
                            #return each_np
                            return each_sentence[each_sentence.index(each_np) -1]

        else:
            return False
    '''

    def handle_hyphens(self, coref_id, np):
        if "-" not in np:
            return False
        variant_set = set()
        orig_np = np
        np = np.replace("-", " ")
        variant_set.add(np.lower())
        np = orig_np.replace("-", "")
        variant_set.add(np.lower())
        for each_sentence in self.np_chunks_words:
            for each_np in each_sentence:
                if each_np.lower() in variant_set:
                    return each_np
        else:
            return False 
        

    def np_preceded_by_article(self,  coref_id,np):
        np = np.replace("'", "").replace("`", "")
        for each_sentence in self.np_chunks_words:
            for each_np in each_sentence:
                    each_np = each_np.replace("'", "").replace("`", "")
                    cmp_each_np = self.remove_articles(each_np)
                    cmp_np = self.remove_articles(np)
                    if cmp_each_np.lower() == cmp_np.lower():
                        return each_np
        else:
            return False

    def match_head_nouns(self,  coref_id,np):
        #TODO: FILTER WRONG CASES
        np = np.replace("'", "").replace("`", "")
        words = np.split(" ")
        if len(words) < 2:
            return False
        head_noun = words[-1]
        for each_sentence in self.np_chunks_words:
            for each_np in each_sentence:
                each_np = each_np.replace("'", "").replace("`", "")
                if not each_np:
                    continue
                syn_set = set([each_np.split(" ")[-1]])
                syn_set.update(self.get_synonym_variants(coref_id, each_np.split(" ")[-1].lower()))
                if head_noun.lower() in syn_set:
                    return each_np.replace("'", "").replace("`", "")
        else:
            return False

    def plain_string_match_on_NPs(self,  coref_id,np):
        np = np.replace("'", "").replace("`", "")
        for each_sentence in self.np_chunks:
            for each_np in each_sentence:
                for each_n, tag in each_np:
                    each_n = each_n.replace("'", "").replace("`", "")
                    if tag not in ["NN", "NNP", "NNS"]:
                        continue
                    if each_n.lower() == np.lower():
                        return each_n
        else:
            return False

    def get_synonym_variants(self, coref_id, np):
        synonyms = set()
        syn_sets = wordnet.synsets(np)
        for syn_set in syn_sets:
            for each_synonym in syn_set.lemma_names:
                synonyms.add(each_synonym.lower())
        for each_word, synonym in self.additional_synonyms.iteritems():
            if each_word == np.lower():
                synonyms.add(synonym)
        return synonyms

    def post_process(self):
        self.process_abbreviations()
        self.handle_case()
        self.handle_articles()
        self.handle_plural()
        self.handle_email()
        self.post_process_dates()
        return

    def handle_case(self):
        case_dict = {}
        for phrase, coref_id_list in self.inverse_coref_dict.iteritems():
            phrase_list = case_dict.setdefault(cleanString(phrase.lower()), [])
            phrase_list.append(phrase)
        
        for phrase, actual_phrase_list  in case_dict.iteritems():
            if len(actual_phrase_list) <= 1:
                continue
            id_set = set()
            for each_actual_phrase in actual_phrase_list:
                id_list = self.inverse_coref_dict.get(each_actual_phrase, [])
                id_set.update(id_list)
            for each_actual_phrase in actual_phrase_list:
                self.inverse_coref_dict[each_actual_phrase] = list(id_set)

    def handle_email(self):
        mail_ext_list = [".com", ".org", ".net", ".net"]
        mail_phrases = []
        mail_ids = []
        for phrase, coref_id_list in self.inverse_coref_dict.iteritems():
            if "@" in phrase.lower():
                for each_ext in mail_ext_list:
                    if each_ext.lower() in phrase.lower():
                        mail_ids.append(phrase)
                continue
            if "mail" in phrase.lower():
                mail_phrases.append(phrase)
        if len(mail_ids) == len(mail_phrases):
            if len(mail_ids) == 1 and len(mail_phrases) == 1:
                coref_id_list = self.inverse_coref_dict.get(mail_ids[0])
                if coref_id_list:
                    new_id_list = self.inverse_coref_dict.get(mail_phrases[0])
                    if new_id_list:
                        coref_id_list.extend(new_id_list)
                        self.inverse_coref_dict[mail_phrases[0]] = coref_id_list

    def handle_articles(self):
        case_dict = {}
        for phrase, coref_id_list in self.inverse_coref_dict.iteritems():
            actual_phrase = self.remove_articles(phrase)
            if len(actual_phrase.split(" ")) > 1:
                actual_phrase = actual_phrase.split(" ")[-1]
            phrase_list = case_dict.setdefault(self.remove_articles(actual_phrase), [])
            phrase_list.append(phrase)
            '''
            for each_phrase in self.get_synonym_variants("Dummy", actual_phrase):
                phrase_list = case_dict.setdefault(self.remove_articles(each_phrase), [])
                phrase_list.append(phrase)
            '''

        for phrase, actual_phrase_list  in case_dict.iteritems():
            if len(actual_phrase_list) <= 1:
                continue
            id_set = set()
            for each_actual_phrase in actual_phrase_list:
                id_list = self.inverse_coref_dict.get(each_actual_phrase, [])
                id_set.update(id_list)
            for each_actual_phrase in actual_phrase_list:
                self.inverse_coref_dict[each_actual_phrase] = list(id_set)

    def handle_plural(self):
        case_dict = {}
        for phrase, coref_id_list in self.inverse_coref_dict.iteritems():
            actual_phrase = phrase
            if len(phrase) < 3:
                continue
            if phrase.endswith("s"):
                phrase = phrase[:-1]
            phrase_list = case_dict.setdefault(phrase, [])
            phrase_list.append(actual_phrase)

        for phrase, actual_phrase_list  in case_dict.iteritems():
            if len(actual_phrase_list) <= 1:
                continue
            id_set = set()
            for each_actual_phrase in actual_phrase_list:
                id_list = self.inverse_coref_dict.get(each_actual_phrase, [])
                id_set.update(id_list)
            for each_actual_phrase in actual_phrase_list:
                self.inverse_coref_dict[each_actual_phrase] = list(id_set)

    def process_abbreviations(self):
        abbr_map = {}
        abbr_pool = set()
        potential_phrases = set()
        for phrase, coref_id_list in self.inverse_coref_dict.iteritems():
            if phrase.isupper() and len(phrase.split(" ")) == 1:
                abbr_pool.add(phrase)
        
        for phrase, coref_id_list in self.inverse_coref_dict.iteritems():
            abbr = ""
            words = phrase.split(" ")
            if len(words) < 2:
                continue
            for each_word in words:
                if not each_word:
                    continue
                if each_word[0]:
                    abbr += each_word[0]
                else:
                    break
            else:
                if abbr.upper() in abbr_pool:
                    abbr_coref_id_list = self.inverse_coref_dict.get(abbr.upper(), [])
                    for each_id in abbr_coref_id_list:
                        if each_id not in coref_id_list:
                            coref_id_list.append(each_id)
                    self.inverse_coref_dict[abbr.upper()] = coref_id_list 

    def get_title_based_matches(self,  coref_id,np):
        for each_sentence in self.np_chunks_words:
            for each_np in each_sentence:
                variants = self.get_title_based_variants(coref_id, each_np)
                if np in variants:
                    return each_np
        else:
            return False

    def get_title_based_variants(self,  coref_id,np):
        variants = set()
        for each_title in self.titles:
            variants.add("%s %s" %(each_title, np))
            for each_name in np.split(" "):
                variants.add("%s %s" %(each_title, each_name))
        return variants

    def synonym_match(self, coref_id, np):
        np = self.remove_articles(np)
        syn_sets = wordnet.synsets(np)
        for syn_set in syn_sets:
            for each_synonym in syn_set.lemma_names:
                if each_synonym == np or np.startswith(each_synonym):
                    continue
                for each_sentence in self.np_chunks_words:
                    for each_np in each_sentence:
                        new_np = self.remove_articles(each_np)
                        if new_np.lower() == each_synonym.lower():
                            return each_np
        else:
            return False

    def get_synonym_variants(self, coref_id, np):
        synonyms = set()
        syn_sets = wordnet.synsets(np)
        for syn_set in syn_sets:
            for each_synonym in syn_set.lemma_names:
                synonyms.add(each_synonym.lower())
        for each_word, synonym in self.additional_synonyms.iteritems():
            if each_word == np.lower():
                synonyms.add(synonym)
        return synonyms

    def handle_apostrophe(self, np):
        actual_phrase = np.split("'s")[-1].strip()
        real_phrase = ""
        for sentence in self.sentences:
            index = sentence.find("'s %s" % actual_phrase)
            if index == -1:
                continue
            for ii in range(index -1, 0, -1):
                if sentence[ii] == " ":
                    break
                real_phrase = sentence[ii] + real_phrase
            return real_phrase
        else:
            return False

    def anonymous_shuffling(self, coref_id, np):
        words = np.replace("-", " ").split(" ")
        if len(words) < 2:
            return False
        num_word = ""
        other_words = set()
        for each_word in words:
            if each_word in self.number_words:
                num_word = each_word
            else:
                other_words.add(each_word.lower())
        if not num_word:
            return False
        for each_sentence in self.np_chunks_words:
            for each_np in each_sentence:
                words = each_np.replace("-", " ").split(" ")
                if len(words) < 2:
                    continue
                new_other_words = set()
                match = False
                for each_word in words:
                    if each_word.lower() == num_word.lower():
                        match = True
                    else:
                        new_other_words.add(each_word.lower())
                if match:
                    return each_np
        else:
            return False

    def apply_rules(self):
        done = False
        for coref_id, np_set in self.coref_np_list:
            for method in self.method_list:
                for np in np_set:
                    match_np = method(coref_id,np)
                    if match_np:
                        self.add_coref_new(coref_id, match_np, np, np_set)
                        done = True
                        break
                if done and method:
                    done = False
                    break
      
     
    def do_appositives(self):
        #Appositives
        self.final_ref_dict()
        for coref_id, np_set in self.coref_np_list:
            if coref_id in self.ref_dict:
                continue
            for np in np_set:
                match_np = self.appositives(coref_id,np)
                if match_np:
                     self.add_coref_new(coref_id, match_np, np, np_set)
                     self.reorgnize()

    def add_coref_new(self, coref_id, match_np, np, np_set):
        #Check if it already exists
        coref_id_list = self.inverse_coref_dict.get(match_np, [])
        if np != match_np:
            if coref_id_list:
                id_in_question = coref_id_list[0]
            else:
                id_in_question = self.gen_new_id()
                self.id_to_np[id_in_question] = match_np
        else:
            count_occur = self.text.count("%s" % match_np)
            if count_occur > len(coref_id_list) and len(match_np) > 1:
                id_in_question = self.gen_new_id()
                self.id_to_np[id_in_question] = match_np
            else:
                return
        
        np_in_question = self.id_to_np.get(coref_id)
        if not np_in_question:
            print "There is a problem. 1"
        coref_id_list = self.inverse_coref_dict.get(np_in_question)
        if not coref_id_list:
            print "There is a problem. 2"
        coref_id_list.append(id_in_question)

        new_coref_id_list = self.inverse_coref_dict.get(match_np, [])
        for each_element in coref_id_list:
            if each_element not in new_coref_id_list:
                new_coref_id_list.append(each_element)

        self.inverse_coref_dict[np_in_question] = new_coref_id_list
        if id_in_question not in coref_id_list:
            coref_id_list.append(id_in_question)
   
        #np_set.add(match_np)


    def final_ref_dict(self):
        for np, coref_id_list in self.inverse_coref_dict.iteritems():
            coref_id_list.sort(key = lambda x: sort_function(x))
            for each_coref_id in coref_id_list[1:]:
                self.ref_dict[each_coref_id] = coref_id_list[0]

    def add_coref(self, coref_id, match_np, np, np_set):
        coref_id_list = self.inverse_coref_dict.setdefault(match_np, [])
        if np != match_np: 
            alter_coref_id_list = self.inverse_coref_dict.setdefault(np, [])
            if alter_coref_id_list and coref_id_list:
                competing_coref = alter_coref_id_list[0]
                if int(competing_coref) < int(coref_id_list[0]):
                    coref_id_list.append(competing_coref)
                    coref_id_list.sort(key = lambda x: sort_function(x))
                for each_coref_id in coref_id_list[1:]:
                    self.ref_dict[each_coref_id] = coref_id_list[0]
        if coref_id_list:
            if coref_id != coref_id_list[0]:
                self.ref_dict[coref_id] = coref_id_list[0]
        else:
            new_id = self.gen_new_id()
            coref_id_list.append(new_id)
            self.ref_dict[coref_id] = new_id
            coref_id_list.sort(key = lambda x : sort_function(x))
            for each_coref_id in coref_id_list[1:]:
                self.ref_dict[each_coref_id] = coref_id_list[0]
        np_set.add(np)

    def reorgnize(self):
        done_nps = set()
        for np, coref_id_list in self.inverse_coref_dict.iteritems():
            for coref_id in coref_id_list:
                if coref_id in self.new_coref_ids:
                    if coref_id in done_nps:
                        continue
                    done_nps.add(coref_id)
                    if not cleanString(self.id_to_np[coref_id]):
                        continue
                    ref_id = self.ref_dict.get(coref_id)
                    if ref_id:
                        del self.ref_dict[coref_id]
                        self.ref_dict[ref_id] = coref_id

 
    def gen_new_id(self):
        self.max_coref = str(int(self.max_coref) + 1)
        self.new_coref_ids.add(self.max_coref)
        return self.max_coref

    def write_output(self, responsedir):
        self.post_process()
        #self.reorgnize()
        #self.do_appositives()
        self.final_ref_dict()
        #print self.inverse_coref_dict
        #Decoy
        for np, coref_id_list in self.orig_inverse_coref_dict.iteritems(): 
            for coref_id in coref_id_list:
                try:
                    self.text, num_subs = re.subn('<COREF ID="%s">%s</COREF>' %(coref_id, np), '<COREF ID="%s">%s</COREF>' %(coref_id, np[::-1]), self.text)
                except:
                    pass   

        self.seen_set = set()
        out_file = open(os.path.join(responsedir, self.out_filename), "w")
        self.new_coref_ids_to_be_ignored = set()
        done_nps = set()
        for np, coref_id_list in self.inverse_coref_dict.iteritems():
            for coref_id in coref_id_list:
                if coref_id in self.new_coref_ids:
                    if coref_id in done_nps:
                        continue
                    done_nps.add(coref_id)
                    try:
                        if not cleanString(self.id_to_np[coref_id]):
                            continue
                        self.text, num_subs = re.subn(self.id_to_np[coref_id], '<COREF ID="%s">%s</COREF>' %(coref_id, self.id_to_np[coref_id]), self.text, count = 1)
                        ref_id = self.ref_dict.get(coref_id)
                        if ref_id:
                            del self.ref_dict[coref_id]
                            self.ref_dict[ref_id] = coref_id
                    except:
                        pass
                    if not num_subs:
                        self.new_coref_ids_to_be_ignored.add(coref_id)

        #Undecoy
        for np, coref_id_list in self.orig_inverse_coref_dict.iteritems():
            for coref_id in coref_id_list:
                try:
                    self.text, num_subs = re.subn('<COREF ID="%s">%s</COREF>' %(coref_id, np[::-1]), '<COREF ID="%s">%s</COREF>' %(coref_id, np), self.text)
                except:
                    pass


        for np, coref_id_list in self.inverse_coref_dict.iteritems():
            for coref_id in coref_id_list:
                try:
                    self.text = re.sub(re.compile(self.tag_format % (coref_id, self.id_to_np[coref_id])), self.replace_fn, self.text, count = 1)
                except:
                    pass
        
        out_file.write(self.text)
        out_file.close()
        #print self.ref_dict
    
    def replace_fn(self, match_obj):
        coref_id = match_obj.group("coref_id") 
        ref_id = self.ref_dict.get(coref_id, -1)
        self.seen_set.add(coref_id)
        if ref_id != -1 and ref_id not in self.new_coref_ids_to_be_ignored:
            return '<COREF ID="%s" REF="%s">%s</COREF>' %(coref_id, ref_id, match_obj.group("np"))
        else:
            return '<COREF ID="%s">%s</COREF>' %(coref_id, match_obj.group("np"))

    def remove_articles(self, phrase):
        match_obj = self.remove_articles_from_phrase_pattern.match(phrase.lower()) 
        if match_obj:
            return match_obj.group('phrase')
        return phrase

def vtv_compress_space(s):
    s = s.strip()
    return re.sub('\s+',' ',s)

def cleanString(s, make_lower=True):
    if make_lower:
        s = s.lower()
    s = s.replace("'s ", " ")
    s = s.replace("`s ", " ")
    s = s.replace("'", "")
    s = s.replace('"', "")
    s = s.replace("`", "")
    s = s.replace(' & ',' and ')
    s = s.replace(' w/ ', ' with ')
    s = str(s).strip()
    s = vtv_compress_space(s)
    return s

