import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler


class Poll:

    def __init__(self, title: str, alive_players_list, asked_player):
        self.asked_player = asked_player
        self.alive_players_list = alive_players_list
        self.title = title
        self.keyboard = []
        self.init_keyboard()

    def send_poll(self, context: telegram.ext.CallbackContext):
        context.bot.send_message(chat_id=self.asked_player.user_id, text=self.title,
                                 reply_markup=self.reply_markup)

    def reset(self):
        self.asked_player = None
        self.title = None
        self.keyboard = []
        self.reply_markup = None

    def set_asked_player(self, asked_player):
        self.asked_player = asked_player

    def set_title(self, title):
        self.title = title

    def init_keyboard(self):
        for player in self.alive_players_list:
            self.keyboard.append([InlineKeyboardButton('@'+player.user_name, callback_data=player.user_name)])
            self.reply_markup = InlineKeyboardMarkup(self.keyboard)
