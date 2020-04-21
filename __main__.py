import telegram
from telegram.ext import Updater
from telegram.ext import CommandHandler
from Game import Game

updater = Updater(token='1292704420:AAF_EyffRm1uwKCwuZ8n6okijs1BY60S128', use_context=True)
bot = telegram.Bot('1292704420:AAF_EyffRm1uwKCwuZ8n6okijs1BY60S128')


def just_for_group(func):
    def wrapper_func(update, context=None):
        if update.effective_chat.id == update.message.from_user["id"]:
            update.message.reply_text("This command is just for groups!")
        else:
            func(update, context)

    return wrapper_func


def just_for_pv(func):
    def wrapper_func(update, context=None):
        if update.effective_chat.id != update.message.from_user["id"]:
            update.message.reply_text("This command is just for private chat!")
        else:
            func(update, context)

    return wrapper_func


@just_for_group
def new_game(update: telegram.Update, context: telegram.ext.CallbackContext):
    group_id = update.effective_chat.id
    group_data = context.chat_data
    if "active_game" not in group_data.keys():
        game = Game(group_id)
        group_data["active_game"] = game
        context.job_queue.run_once(game.start_game, 5, context=(update.message.chat_id, context.chat_data))
        update.message.reply_text("New game started")
    else:
        update.message.reply_text("This group has an unfinished game!")


@just_for_pv
def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    update.message.reply_text("Hi!")
    context.user_data["has_subscribed"] = True


@just_for_group
def join(update: telegram.Update, context: telegram.ext.CallbackContext):
    user = update.message.from_user
    group_data = context.chat_data
    user_data = context.user_data
    if "active_game" in group_data.keys():
        if "has_subscribed" in user_data.keys():
            if user_data["has_subscribed"]:
                group_game = group_data["active_game"]
                group_game.join_game(user, user_data, update)
            else:
                update.message.reply_text("You have not started me in private chat.Please start me and try again.")
        else:
            update.message.reply_text("You have not started me in private chat.Please start me and try again.")
    else:
        update.message.reply_text("There is no game in this group!")


@just_for_group
def leave(update: telegram.Update, context: telegram.ext.CallbackContext):
    user = update.message.from_user
    group_data = context.chat_data
    user_data = context.user_data
    if "active_game" in group_data.keys():
        group_game = group_data["active_game"]
        group_game.leave_game(user, user_data, update)
    else:
        update.message.reply_text("There is no game in this group!")

@just_for_group
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
