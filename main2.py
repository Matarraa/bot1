import telebot
from telebot import types
import re
import gensim
import logging
import nltk.data
import urllib.request
from gensim.models import word2vec, KeyedVectors
import nltk
import random
import warnings
warnings.filterwarnings('ignore')
from pymorphy2 import MorphAnalyzer
morph = MorphAnalyzer()
from pymystem3 import Mystem
m = Mystem()
import shelve
import functions
import os
import flask

TOKEN = os.environ["TOKEN"]

bot = telebot.TeleBot(TOKEN, threaded=False)


bot.remove_webhook()
bot.set_webhook(url="https://vast-retreat-92848.herokuapp.com/bot")

app = flask.Flask(__name__)


results = {}
idstickers = ['CAACAgQAAxkBAAECdZpg0mXj90WDJ9Gq_-EnciCALnM72wACgQAD_MTgF3tFEHaI8aNuHwQ',\
              'CAACAgQAAxkBAAECdZhg0mXdQ8MbVgABloD96ZKonNIhAlIAAnoAA_zE4Bcx4eldeJekfx8E',\
              'CAACAgQAAxkBAAECdZZg0mXAhuSs-YtzRAkvbE72aam5sQACbgAD_MTgFzX0sAt2v-1THwQ',\
              'CAACAgQAAxkBAAECdZJg0mWYDjPnUwABPS9wXiJaravZ6WgAAoUAA_zE4BdcjB5JYBPzJh8E',\
              'CAACAgQAAxkBAAECdZBg0mV1Ncll9qWU-HzOaOtff8JotgACewAD_MTgF_MfXhnhMQ98HwQ',\
              'CAACAgQAAxkBAAECdY5g0mVwFZb56mAh-AwAAXBI8kYYltgAAnEAA_zE4BfCQIqfgL_1_R8E',\
              'CAACAgQAAxkBAAECdZRg0mW46cnb4BtKac9UpGy1TPL9jQACdQAD_MTgF3agR1UnwrRSHwQ']

right_answers = ['Правильно!', 'Верно!', 'Ты прав!', 'Угадал!']
wrong_answers = ['Не угадал!', 'А вот и нет!', 'Неверно!', 'Неправильно!']
who = ['Булгаков', 'Компьютер']
filename = 'bulgakov_text.txt'
sentences = functions.sentences_list(filename)

keyboard = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=3)
btn1 = types.KeyboardButton('Играть')
keyboard.add(btn1)

keyboard1 = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=3)
btn3 = types.KeyboardButton('Компьютер')
btn4 = types.KeyboardButton('Булгаков')
btn7 = types.KeyboardButton('Закончить игру')
keyboard1.add(btn3, btn4, btn7)

keyboard2 = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=3)
btn5 = types.KeyboardButton('Всё ясно, погнали')
keyboard2.add(btn5)

keyboard3 = types.ReplyKeyboardMarkup(one_time_keyboard=True, row_width=3)
btn6 = types.KeyboardButton('Играть еще раз!')
keyboard3.add(btn6)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.send_message(message.chat.id, "Привет! Хорошо ли ты знаком с творчеством Булгакова? "
                                      "Давай сыграем в игру. Я буду прислыать тебе предложение, "
                                      "а тебе нужно будет угадать, кто его написал Булгаков или компьютер.", reply_markup=keyboard)
    sticker_id = random.choice(idstickers)
    bot.send_sticker(message.chat.id, sticker_id)

@bot.message_handler(regexp='Играть')
def game(message):
    results[message.chat.id] = [0, 0]
    bot.send_message(message.chat.id, '*Кто написал это предложение?*', parse_mode='MarkdownV2')
    author = random.choice(who)
    bot.send_message(message.chat.id, functions.change_sentence(sentences, author), reply_markup=keyboard1)
    functions.set_user_game(message.chat.id, author)

@bot.message_handler(func=lambda message: True, content_types=['text'])
def check_answer(message):
    if message.text == 'Закончить игру':
        your_results = ['*Количество правильных ответов: *', str(results[message.chat.id][0]),'\n', '*Количество неправильных ответов: *', str(results[message.chat.id][1])]
        bot.send_message(message.chat.id, ''.join(your_results), reply_markup=keyboard3, parse_mode='MarkdownV2')
        results[message.chat.id] = [0, 0]
        bot.register_next_step_handler(message, game)
    else:
        answer = functions.get_answer_for_user(message.chat.id)
        if not answer:
            bot.send_message(message.chat.id, 'Чтобы начать игру, нажмите "Играть"', reply_markup=keyboard)
        else:
            keyboard_hider = types.ReplyKeyboardRemove()
            if message.text == answer:
                bot.send_message(message.chat.id, random.choice(right_answers), reply_markup=keyboard_hider)
                results[message.chat.id][0] += 1
                functions.finish_user_game(message.chat.id)
            else:
                bot.send_message(message.chat.id, random.choice(wrong_answers), reply_markup=keyboard_hider)
                results[message.chat.id][1] += 1
                functions.finish_user_game(message.chat.id)
            bot.send_message(message.chat.id, '*Кто написал это предложение?*', parse_mode='MarkdownV2')
            author = random.choice(who)
            functions.set_user_game(message.chat.id, author)
            bot.send_message(message.chat.id, functions.change_sentence(sentences, author), reply_markup=keyboard1)

@app.route("/", methods=['GET', 'HEAD'])
def index():
    return 'ok'

# страница для нашего бота
@app.route("/bot", methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)
    
if __name__ == '__main__':
    import os
    app.debug = True
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
