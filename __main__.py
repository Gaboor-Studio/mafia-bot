import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler

updater = Updater(token='1212931959:AAHH9ViQhhhVRJBsEs9EwBv2pfkg8BMDFS4', use_context=True)


class Player:
    def __init__(self, user_id):
        self.id = user_id


class Game:
    players = []

    @staticmethod
    def join_game(update: telegram.Update, context: telegram.ext.CallbackContext):
        user = update.message.from_user
        k = 0
        for i in Game.players:
            if i.id == user['username']:
                k = 1
        if k == 0:
            player = Player(user['username'])
            Game.players.append(player)
            player_names = ""
            for i in Game.players:
                player_names = player_names + '@' + i.id + '\n'
            update.message.reply_text(player_names)

        else:
            update.message.reply_text('@' + user['username'] + " you already joined to game")

    @staticmethod
    def leave_game(update: telegram.Update, context: telegram.ext.CallbackContext):
        user = update.message.from_user
        k = 0
        for i in Game.players:
            if i.id == user['username']:
                Game.players.remove(i)
                k = 1
                update.message.reply_text('@' + i.id + " successfully leave from the game")
        if k == 0:
            update.message.reply_text("You didnt join to the game")


def new_game(update, context):
    update.message.reply_text("New game started")
    game = Game
    dispatcher.add_handler(CommandHandler('join', game.join_game))
    dispatcher.add_handler(CommandHandler('leave', game.leave_game))


def start(update: telegram.Update):
    update.message.reply_text("bisharaf")


dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler("new", new_game))
updater.start_polling()
