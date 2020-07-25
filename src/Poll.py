import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler


class Poll:

    def __init__(self, title: str, votes_list, sent_id):
        self.sent_id = sent_id
        self.votes_list = votes_list
        self.title = title
        self.keyboard = []
        self.init_keyboard()

    def send_poll(self, context: telegram.ext.CallbackContext):
        context.bot.send_message(chat_id=self.sent_id, text=self.title,
                                 reply_markup=self.reply_markup)

    def reset(self):
        self.sent_id = None
        self.title = None
        self.keyboard = []
        self.reply_markup = None

    def set_asked_player(self, sent_id):
        self.sent_id = sent_id

    def set_title(self, title):
        self.title = title

    def init_keyboard(self):
        for vote in self.votes_list:
            self.keyboard.append([InlineKeyboardButton(vote, callback_data=vote)])
        self.reply_markup = InlineKeyboardMarkup(self.keyboard)
    def sicktir_poll(self,context: telegram.ext.CallbackContext):
        context.bot.edit_message_text()