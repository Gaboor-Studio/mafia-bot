import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class Poll:

    def __init__(self, title: str, alive_players_list, asked_player):
        self.asked_player = asked_player
        self.alive_players_list = alive_players_list
        self.title = title
        self.keyboard = []
        self.init_keyboard(self.asked_player)

    def send_poll(self, context: telegram.ext.CallbackContext):
        context.bot.send_message(chat_id=self.asked_player.user_id, text='You want to kill:',
                                 reply_markup=self.reply_markup)

    def reset(self):
        self.asked_player = None
        self.title = None
        self.keyboard = []
        self.reply_markup = None

    def set_asked_player(self, asked_player):
        self.asked_player = asked_player;

    def set_title(self, asked_player):
        self.asked_player = asked_player;

    def init_keyboard(self, asked_player):
        for player in self.alive_players_list:
            if player != self.asked_player:
                self.keyboard.append(InlineKeyboardButton('@'+player.user_name, callback_data=player))
        self.reply_markup = InlineKeyboardMarkup(self.keyboard)
