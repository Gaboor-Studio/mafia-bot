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
