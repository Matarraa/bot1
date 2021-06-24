import re
import gensim
import shelve
import logging
import nltk.data
import urllib.request
from gensim.models import word2vec
import nltk
import random
import warnings
warnings.filterwarnings('ignore')
from pymorphy2 import MorphAnalyzer
morph = MorphAnalyzer()
from pymystem3 import Mystem
m = Mystem()

model_bulgakov2 = gensim.models.KeyedVectors.load_word2vec_format('bulgakov2.bin', binary=True)
shelve_name = 'shelve.db'

def read_file (filename):
    with open (filename, encoding = 'utf-8') as file:
        text = file.read()
    return text

#Делим текст на предложения, которые будут подаваться как настоящие предложения Булгакова и изменяться компьютером в поддельные предложения.
def bulgakov_sentences(filename):
    mm_text = read_file(filename)
    mm_text = re.sub('Глава [0-9]+', '', mm_text)
    mm_text = re.sub('\n\n\n\n\n', '. ', mm_text)
    mm_text = mm_text.replace('...', ',')
    mm_text = mm_text.replace('..', '')
    mm_text = mm_text.replace('»', '')
    mm_text = mm_text.replace('«', '')
    mm_text = re.sub('(\.)( )([^–])', r'\1\n\3', mm_text)
    mm_text = re.sub('(!)( )([^–])', r'\1\n\3', mm_text)
    mm_text = re.sub('(\?)( )([^–])', r'\1\n\3', mm_text)
    mm_text = re.sub('\n+', '\n', mm_text)
    return mm_text

def sentences_list(filename):
    mm_text = bulgakov_sentences(filename)
    with open('sentences.txt', 'w', encoding='utf-8') as f:
        f.write(mm_text)
    sentences = mm_text.splitlines()
    for sentence in sentences:
        if sentence == '':
            sentences.remove(sentence)
    return sentences

def normal_form_parse (ana, tags):
    if tags.POS in ['VERB', 'INFN', 'PRTF', 'PRTS', 'GRND']:
        for element in ana:
            if element.tag.POS == 'INFN':
                norm = element
                break
            else:
                continue
    elif tags.POS == 'NOUN':
        for element in ana:
            if element.tag.POS == 'NOUN':
                norm = element
                break
            else:
                continue
    elif tags.POS in ['ADJF', 'ADJS']:
        for element in ana:
            if element.tag.POS == 'ADJF':
                norm = element
                break
            else:
                continue
    elif tags.POS == 'ADVB':
        for element in ana:
            if element.tag.POS == 'ADVB':
                norm = element
                break
            else:
                continue
    else:
        norm = ana[0]
    return norm

#Функция, которая изменяет форму слова
def inflect_word(POS, word, tag, token, first_word, lemma):
    if lemma == 'патриарший':
        new_word = morph.parse('бронные')[0].inflect({tag.case}).word
    elif POS == 'NOUN':
        if 'Name' in tag:
            new_word = word.inflect({tag.number, tag.gender, tag.case}).word
        elif 'Surn' in tag:
            new_word = word.inflect({tag.number, tag.gender, tag.case}).word
        elif 'Patr' in tag:
            new_word = word.inflect({tag.number, tag.gender, tag.case}).word
        else:
            new_word = word.inflect({tag.number, tag.case}).word
    elif POS == 'ADJF':
        if tag.POS == 'ADJS':
            if tag.number == 'plur':
                new_word = word.inflect({tag.POS, tag.number}).word
            elif tag.number == 'sing':
                new_word = word.inflect({tag.POS, tag.gender, tag.number}).word
        elif tag.POS == 'ADJF':
            if tag.number == 'plur':
                if 'anim' in tag:
                    new_word = word.inflect({tag.POS, tag.number, tag.animacy, tag.case}).word
                else:
                    new_word = word.inflect({tag.POS, tag.number, tag.case}).word
            elif tag.number == 'sing':
                if 'anim' in tag:
                    new_word = word.inflect({tag.POS, tag.gender, tag.number, tag.animacy, tag.case}).word
                else:
                    new_word = word.inflect({tag.POS, tag.gender, tag.number, tag.case}).word
    elif POS == 'INFN':
        if tag.POS == 'VERB':
            if tag.mood == 'impr':
                new_word = word.inflect({tag.POS, tag.number, tag.mood}).word
            elif tag.mood == 'indc':
                if tag.tense == 'past':
                    if tag.number == 'sing':
                        new_word = word.inflect({tag.POS, tag.gender, tag.number}).word
                    elif tag.number == 'plur':
                        new_word = word.inflect({tag.POS, tag.number}).word
                elif tag.tense == 'pres' or tag.tense == 'futr':
                    new_word = word.inflect({tag.POS, tag.number, tag.person}).word
        elif tag.POS == 'PRTF':
            if tag.number == 'plur':
                new_word = word.inflect({tag.POS, tag.number, tag.case}).word
            elif tag.number == 'sing':
                new_word = word.inflect({tag.POS, tag.number, tag.gender, tag.case}).word
        elif tag.POS == 'PRTS':
            if tag.number == 'plur':
                new_word = word.inflect({tag.POS, tag.number}).word
            elif tag.number == 'sing':
                new_word = word.inflect({tag.POS, tag.gender, tag.number}).word
        elif tag.POS == 'GRND':
            new_word = word.inflect({tag.POS}).word
        elif tag.POS == 'INFN':
            new_word = word.word
    elif POS == 'NUMR':
        new_word = word.inflect({tag.case}).word
    elif POS == 'PREP':
        new_word = first_word
    elif POS == 'NPRO':
        new_word = first_word
    elif first_word == 'и':
        new_word = 'и'
    else:
        new_word = word.word
    if token.istitle():
        new_word = new_word[0].upper() + new_word[1:]
    return new_word

#Функция, которая изменяет предложение
def change_sentence(sentences, author):
    sentence = random.choice(sentences)
    new_sentence = []
    if author == 'Булгаков':
        return sentence
    else:
        tokens = nltk.word_tokenize(sentence)
        for token in tokens:
            if token.isalpha():
                ana = morph.parse(token) #разбираем слово из предложения
                first = ana[0]
                lemma = first.normal_form #лемма первоначального слова
                tags = first.tag #теги первоначального слова
                parse_lemma = morph.parse(lemma)
                ana_lemma = normal_form_parse(parse_lemma, tags)
                ana_lemma_POS = ana_lemma.tag.POS #часть речи леммы первоначального слова
                try:
                    if lemma in model_bulgakov2.key_to_index: #проверяем есть ли это слово в модели
                        top = model_bulgakov2.most_similar(lemma, topn=30) #берем первые самые близкие слова
                        for word in top: #ищем слово той же части речи
                            lemma_new = word[0] #достаем слово
                            ana1 = morph.parse(lemma_new)#разбираем слово-кандидата
                            new = ana1[0]
                            tags_new = new.tag #достаем теги слова-кандидата
                            if new.tag.POS == ana_lemma_POS: #проверяем одной ли части речи первоначальное слово и слово-кандидат
                                if new.tag.POS == 'NOUN':
                                    if new.tag.animacy == ana_lemma.tag.animacy and new.tag.gender == ana_lemma.tag.gender:
                                        new_word = inflect_word(new.tag.POS, new, first.tag, token, first.word, lemma)
                                        new_sentence.append(new_word)
                                        break
                                    else:
                                        continue
                                else:
                                    new_word = inflect_word(new.tag.POS, new, first.tag, token, first.word, lemma)
                                    new_sentence.append(new_word)
                                    break
                            else: #если нет, то переходим к следующему слову
                                if word == top[-1]:
                                    new_sentence.append(token)
                                else:
                                    continue
                    else:
                        new_sentence.append(token)
                except Exception:
                    change_sentence(sentences, author)
            else:
                new_sentence.append(token)
        comp_sentence = ' '.join(new_sentence)
        comp_sentence = re.sub(r' \.', '.', comp_sentence)
        comp_sentence = re.sub(r' \?', '?', comp_sentence)
        comp_sentence = re.sub(r' !', '!', comp_sentence)
        comp_sentence = re.sub(r' ,', ',', comp_sentence)
        comp_sentence = re.sub(r' :', ':', comp_sentence)
        return comp_sentence

def set_user_game(chat_id, estimated_answer):
    with shelve.open(shelve_name) as storage:
        storage[str(chat_id)] = estimated_answer

def finish_user_game(chat_id):
    with shelve.open(shelve_name) as storage:
        del storage[str(chat_id)]

def get_answer_for_user(chat_id):
    with shelve.open(shelve_name) as storage:
        try:
            answer = storage[str(chat_id)]
            return answer
        except KeyError:
            return None

