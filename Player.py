import telegram
from Poll import Poll
from telegram.ext import CommandHandler
import time


class Player:
    def __init__(self, name, user_name, user_id, user_data):
        self.rule = "citizen"
        self.name = name
        self.user_name = user_name
        self.user_id = user_id
        self.user_data = user_data
        self.is_alive = True

    def talk(self, group_chat_id, context: telegram.ext.CallbackContext):
        context.bot.send_message(chat_id=group_chat_id,
                                 text='@' + self.user_name + " turn to talk")
        time.sleep(5)
