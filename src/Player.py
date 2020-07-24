import telegram
from Poll import Poll
from telegram.ext import CommandHandler
import time
import enum


class Rules(enum.Enum):
    GodFather = 0
    Mafia = 1
    Citizen = 2
    Doctor = 3
    Detective = 4
    Sniper = 5


class Player:
    """Attributes:
        active_game: player's active game
        name: player's profile name
        user_name: player's username
        user_id: player's chat id
        user_data: player's telegram data
        is_alive: is player alive or not
        emoji: player's emoji
    """

    def __init__(self, name, user_name, user_id, user_data, active_game):
        self.active_game = active_game
        self.name = name
        self.user_name = user_name
        self.user_id = user_id
        self.user_data = user_data
        self.is_alive = True
        self.emoji = None
        self.sticker = None
        self.rule = None

    def equals(self, player):
        return self.user_name == player.user_name

    def talk(self, group_chat_id, context: telegram.ext.CallbackContext):
        context.bot.send_message(chat_id=group_chat_id,
                                 text='@' + self.user_name + " turn to talk")

    def send_rule(self, context: telegram.ext.CallbackContext):
        if self.rule == Rules.Citizen:
            context.bot.send_sticker(chat_id=self.user_id,
                                     sticker="CAACAgQAAxkBAAEBEVVfE0jFjzsHhOI_TcxxIG2wktMrxwACHAAD1ul3KxBZtykr9BZTGgQ")
        elif self.rule == Rules.GodFather:
            context.bot.send_sticker(chat_id=self.user_id,
                                     sticker="CAACAgQAAxkBAAEBEU1fE0eH9cuSbcnfD4DR2x7R2dk4pwACGgAD1ul3K6tFV61NP-r5GgQ")
        elif self.rule == Rules.Mafia:
            context.bot.send_sticker(chat_id=self.user_id,
                                     sticker="CAACAgQAAxkBAAEBEUtfE0dFaAz9MUL8D5wg6Na2-YnQwwACHQAD1ul3K-J4YMXfsX4oGgQ")
        elif self.rule == Rules.Detective:
            context.bot.send_sticker(chat_id=self.user_id,
                                     sticker="CAACAgQAAxkBAAEBEVFfE0h-Tv7X7WsBAmqTaDiggvB7zAACGwAD1ul3K1Bufqtn71YzGgQ")
        elif self.rule == Rules.Doctor:
            context.bot.send_sticker(chat_id=self.user_id,
                                     sticker="CAACAgQAAxkBAAEBEU9fE0go967QwvK8s_sqY4js15WHWgACHgAD1ul3K_mMfTHPD6mEGgQ")
        elif self.rule == Rules.Sniper:
            context.bot.send_sticker(chat_id=self.user_id,
                                     sticker="CAACAgQAAxkBAAEBEVNfE0iiRs6BL7yucCAoP5bH6wLv4QACHwAD1ul3K_8BpWyNZM2OGgQ")
        context.bot.send_message(chat_id=self.user_id, text=self.rule.name)
