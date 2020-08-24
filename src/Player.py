import telegram
from Poll import Poll
from telegram.ext import CommandHandler
import time
import enum
import codecs
import os


class Roles(enum.Enum):
    GodFather = 0
    Mafia = 1
    Citizen = 2
    Doctor = 3
    Detective = 4
    Sniper = 5
    Bulletproof = 6


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
        self.role = None
        self.mafia_rank = 0
        self.shield = False

    def equals(self, player):
        return self.user_name == player.user_name

    def talk(self, group_chat_id, context: telegram.ext.CallbackContext):
        game = self.user_data['active_game']
        lang = game.group_data['lang']
        if lang == 'en':
            context.bot.send_message(chat_id=group_chat_id, text=self.get_markdown_call(
            ) + "'s turn to talk 🗣", parse_mode='Markdown')
        else:
            context.bot.send_message(chat_id=group_chat_id, text="نوبت " +
                                                                 self.get_markdown_call() + " هست که صحبت کنه",
                                     parse_mode='Markdown')

    def get_markdown_call(self):
        return f"[{self.name}](tg://user?id={self.user_id})"

    def send_role(self, context: telegram.ext.CallbackContext):
        game = self.user_data['active_game']
        language = game.group_data['lang']
        if self.role == Roles.Citizen:
            context.bot.send_sticker(chat_id=self.user_id,
                                     sticker="CAACAgQAAxkBAAEBEVVfE0jFjzsHhOI_TcxxIG2wktMrxwACHAAD1ul3KxBZtykr9BZTGgQ")
        elif self.role == Roles.GodFather:
            context.bot.send_sticker(chat_id=self.user_id,
                                     sticker="CAACAgQAAxkBAAEBEU1fE0eH9cuSbcnfD4DR2x7R2dk4pwACGgAD1ul3K6tFV61NP-r5GgQ")
        elif self.role == Roles.Mafia:
            context.bot.send_sticker(chat_id=self.user_id,
                                     sticker="CAACAgQAAxkBAAEBEUtfE0dFaAz9MUL8D5wg6Na2-YnQwwACHQAD1ul3K-J4YMXfsX4oGgQ")
        elif self.role == Roles.Detective:
            context.bot.send_sticker(chat_id=self.user_id,
                                     sticker="CAACAgQAAxkBAAEBEVFfE0h-Tv7X7WsBAmqTaDiggvB7zAACGwAD1ul3K1Bufqtn71YzGgQ")
        elif self.role == Roles.Doctor:
            context.bot.send_sticker(chat_id=self.user_id,
                                     sticker="CAACAgQAAxkBAAEBEU9fE0go967QwvK8s_sqY4js15WHWgACHgAD1ul3K_mMfTHPD6mEGgQ")
        elif self.role == Roles.Sniper:
            context.bot.send_sticker(chat_id=self.user_id,
                                     sticker="CAACAgQAAxkBAAEBEVNfE0iiRs6BL7yucCAoP5bH6wLv4QACHwAD1ul3K_8BpWyNZM2OGgQ")
        elif self.role == Roles.Bulletproof:
            context.bot.send_sticker(chat_id=self.user_id,
                                     sticker="CAACAgQAAxkBAAEBN-BfPBhwBqNMe7_Ux36oWZh5AqVjAANKAAPW6XcrCCyNXGC3bJUaBA")
        with codecs.open(os.path.join("Lang", language, self.role.name), 'r', encoding='utf8') as file:
            context.bot.send_message(chat_id=self.user_id, text=file.read(), parse_mode="MarkDown")
        if self.role == Roles.Mafia or self.role == Roles.GodFather:
            with codecs.open(os.path.join("Lang", language, "MafiaRank"), 'r', encoding='utf8') as file:
                context.bot.send_message(
                    chat_id=self.user_id, text=file.read() + str(self.mafia_rank), parse_mode="MarkDown")
