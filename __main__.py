import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
from Game import Game

updater = Updater(token='1292704420:AAF_EyffRm1uwKCwuZ8n6okijs1BY60S128', use_context=True)



def new_game(update: telegram.Update, context: telegram.ext.CallbackContext):
    group_id = update.effective_chat.id
    group_data = context.chat_data
    if "active_game" not in group_data.keys():
        game = Game(group_id)
        group_data["active_game"] = game
        context.job_queue.run_once(start_game, 30, context=(update.message.chat_id,context.chat_data))
        update.message.reply_text("New game started")
    else:
        update.message.reply_text("This group has an unfinished game!")


def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    update.message.reply_text("Hi!")
    context.user_data["is_subscribed"] = True


def join(update: telegram.Update, context: telegram.ext.CallbackContext):
    user = update.message.from_user
    group_data = context.chat_data
    user_data = context.user_data
    if "active_game" in group_data.keys():
        group_game = group_data["active_game"]
        group_game.join_game(user, user_data, update)
    else:
        update.message.reply_text("There is no game in this group!")


def leave(update: telegram.Update, context: telegram.ext.CallbackContext):
    user = update.message.from_user
    group_data = context.chat_data
    user_data = context.user_data
    if "active_game" in group_data.keys():
        group_game = group_data["active_game"]
        group_game.leave_game(user, user_data, update)
    else:
        update.message.reply_text("There is no game in this group!")


def start_game(context: telegram.ext.CallbackContext):
    group_data = context.job.context[1]
    if "active_game" in group_data.keys():
        game = group_data["active_game"]
        game.start_game()
        for player in game.players:
            context.bot.send_message(chat_id=player.user_id, text=player.rule)
        context.bot.send_message(chat_id=context.job.context[0], text='Game has been started!')
    else:
        context.bot.send_message(chat_id=context.job.context[0], text='There is no game in this group!')


def end_game(update: telegram.Update, context: telegram.ext.CallbackContext):
    group_data = context.chat_data
    if "active_game" in group_data.keys():
        update.message.reply_text("Game ended")
        del group_data["active_game"]
    else:
        update.message.reply_text("There is no game in this group!")


dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler("new", new_game))
dispatcher.add_handler(CommandHandler("end", end_game))
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler('join', join))
dispatcher.add_handler(CommandHandler('leave', leave))
updater.start_polling()
