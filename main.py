import sqlite3
import telebot
import os
from background import keep_alive #импорт функции для поддержки работоспособности
import csv
import pip
pip.main(['install', 'pytelegrambotapi'])
from random import choice, shuffle
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


class Bot:
    def __init__(self):
        self.data = self.load_capitals(self)
        self.TOKEN = os.environ['TOKEN']
        self.bot = telebot.TeleBot(self.TOKEN)
        self.rand_answ_callback = ["Верно!", "Молодец!", "Превосходно!", "Хорошо!", "Умница!", "Неплохо"]
        self.con = sqlite3.connect("users.db", check_same_thread=False)
        self.cur = self.con.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS Users(
                            id INTEGER,
                            username TEXT NOT NULL,
                            ingame INTEGER,
                            answer TEXT NOT NULL,
                            wins INTEGER
                            )
                            """)


        @self.bot.message_handler(commands=["help", "start"])
        def send_message(message):
            text, options = self.get_answer(message.chat.id)
            keyboard = self.inline_keyboard(options)
            self.bot.send_message(message.chat.id, text,
                                  reply_markup=keyboard,
                                  parse_mode="HTML")
            self.users = self.con.execute("""select *
            from Users
            where id = ?""", (message.chat.id,)).fetchall()

            if  self.users == [] :
                self.base_connect(message.chat.id, message.from_user.first_name, 1, 0, answer=options[-1])
            elif self.users[0][-3] == 1:
                self.base_wins_connect(self.count_answer(message.chat.id), 1, message.chat.id)


        @self.bot.callback_query_handler(func=lambda call : True)
        def callback_query(call):
            if call.data == "end":
                self.bot.delete_message(call.message.chat.id,
                                        call.message.message_id)
                self.base_wins_connect(self.count_answer(call.message.chat.id),0, call.message.chat.id)
                self.bot.send_message(call.message.chat.id,
                                      self.show_result(call.message.chat.id),
                                      parse_mode="HTML",
                                      )
                self.base_wins_connect(0, 0, call.message.chat.id)

            else:
                if call.data == self.answer(call.message.chat.id):
                    self.bot.answer_callback_query(call.id, choice(self.rand_answ_callback))
                    self.count_append(call.message.chat.id)
                    self.base_wins_connect(self.count_answer(call.message.chat.id),1, call.message.chat.id)

                else:
                    self.bot.answer_callback_query(call.id, "НЕверно!")

            text, options = self.get_answer(call.message.chat.id)
            keyboard = self.inline_keyboard(options)
            self.bot.edit_message_text(text,
                                       call.message.chat.id,
                                       call.message.id,
                                       reply_markup=keyboard,
                                       parse_mode="HTML")

    def run(self):
        keep_alive()
        self.bot.polling(non_stop=True)

    @staticmethod
    def inline_keyboard(options):
        keyboard = InlineKeyboardMarkup(row_width=2 )
        buttons = [InlineKeyboardButton(s, callback_data=s) for s in options]
        shuffle(buttons)
        keyboard.add(*buttons)
        keyboard.add(InlineKeyboardButton(' 🛑Закончить игру🛑', callback_data="end"))
        return  keyboard

    @staticmethod
    def load_capitals(self):
        capitals = {}
        try:
            with open("capitals.csv", newline="") as f:
                data = csv.reader(f, delimiter=";")
                for line in data:
                    capitals[line[0]] = line[1]

        except Exception as e:
            print("Ошибка при получении данных из CSV-файла")

        return capitals

    def get_answer(self, id):
        countries, capitals = list(self.data.keys()), list(self.data.values())
        rand_countries = choice(countries)
        answer_capitals = self.data[rand_countries]
        self.cur.execute("""Update Users set answer = ? where id = ?""", (answer_capitals, id,))
        self.con.commit()
        in_answer_capitals = [choice(capitals) for _ in "___"] + [answer_capitals]

        return f'Назовите столицу страны: <b>{rand_countries}</b>?', in_answer_capitals

    def show_result(self, id):
        return f"""Результат игры:\nКоличество правильных ответов: {self.count_answer(id)}\nОтправьте /start чтобы начать заново """


    def base_connect(self, id, username, ingane, wins, answer="answer"):

        self.cur.execute('INSERT INTO Users (id, username, ingame, answer, wins) VALUES (?, ?, ?, ?, ?)',
                       (id, username, ingane,answer, wins))
        self.con.commit()

    def base_wins_connect(self, wins, ingame, id):
        self.cur.execute("""Update Users set wins = ?,  ingame = ? where id = ?""",(wins, ingame, id,))
        self.con.commit()


    def count_append(self, id):
        self.cur.execute("""Update Users set wins = ? where id = ?""", (self.count_answer(id) + 1, id,))
        self.con.commit()


    def count_answer(self, id):
        self.cur.execute("""SELECT * from Users where id=?""",(id,))
        self.con.commit()
        return self.cur.fetchone()[-1]

    def answer(self, id):
        self.cur.execute("""SELECT * from Users where id=?""", (id,))
        self.con.commit()
        return self.cur.fetchone()[-2]
print(os.getenv("MY_SECRET"))
bot = Bot()
bot.run()
