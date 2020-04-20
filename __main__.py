import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
from Game import Game

updater = Updater(token='1212931959:AAHH9ViQhhhVRJBsEs9EwBv2pfkg8BMDFS4', use_context=True)


def new_game(update: telegram.Update, context: telegram.ext.CallbackContext):
    global games
    group_id = update.effective_chat.id
    has_active_game = False
    print(group_id)
    for game in games:
        if (game.group_chat_id == group_id):
            has_active_game = True
    if (not has_active_game):
        update.message.reply_text("New game started")
        game = Game(group_id)
        games.append(game)
        context.job_queue.run_once(start_game, 30, context=update.message.chat_id)
    else:
        update.message.reply_text("The game has already started")


def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    update.message.reply_text("Hi!")


def join(update: telegram.Update, context: telegram.ext.CallbackContext):
    global games
    user_info = update.message.from_user
    group_id = update.effective_chat.id
    has_started_game = False
    group_game = None
    for game in games:
        if (game.group_chat_id == group_id):
            has_started_game = True
            group_game = game
    if (has_started_game):
        group_game.join_game(user_info, update)
    else:
        update.message.reply_text("There is no game in this group!")


def leave(update: telegram.Update, context: telegram.ext.CallbackContext):
    global games
    user_info = update.message.from_user
    group_id = update.effective_chat.id
    has_started_game = False
    group_game = None
    for game in games:
        if (game.group_chat_id == group_id):
            has_started_game = True
            group_game = game
    if (has_started_game):
        group_game.leave_game(user_info, update)
    else:
        update.message.reply_text("There is no game in this group!")


def start_game(context: telegram.ext.CallbackContext):
    global games
    context.bot.send_message(chat_id=context.job.context, text='Game has been started!')
    group_id = context.job.context
    for game in games:
        if game.group_chat_id == group_id:
            game.start_game()
            for player in game.players:
                context.bot.send_message(chat_id=player.user_id, text=player.rule)
            break


def end_game(update: telegram.Update):
    global games
    group_id = update.effective_chat.id
    has_active_game = False
    for game in games:
        if (game.group_chat_id == group_id):
            has_active_game = True
            update.message.reply_text("Game has been ended")
            games.remove(game)
            break
    if has_active_game==False:
        update.message.reply_text("There is no game in this group!")

games = []
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler("new", new_game))
dispatcher.add_handler(CommandHandler("end", end_game))
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler('join', join))
dispatcher.add_handler(CommandHandler('leave', leave))
updater.start_polling()
