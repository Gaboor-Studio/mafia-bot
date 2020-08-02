import telegram
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler
from Game import Game, GameState
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import requests

from Player import Player, Roles
from Poll import Poll

# 1212931959:AAHH9ViQhhhVRJBsEs9EwBv2pfkg8BMDFS4 Real Token
TOKEN = '1212931959:AAHH9ViQhhhVRJBsEs9EwBv2pfkg8BMDFS4'
# TOKEN = '1212931959:AAHH9ViQhhhVRJBsEs9EwBv2pfkg8BMDFS4'
updater = Updater(token=TOKEN, use_context=True)
bot = telegram.Bot(TOKEN)


def admin_permission(func):
    def wrapper_func(update, context):
        group_id = update.effective_chat.id
        user_id = update.message.from_user['id']
        role = context.bot.get_chat_member(group_id, user_id).status
        if role == 'creator' or role == 'administrator':
            func(update, context)
        else:
            update.message.reply_text("You dont have admin permission to run this command!")

    return wrapper_func


def just_for_group(func):
    def wrapper_func(update, context):
        if update.effective_chat.id == update.message.from_user["id"]:
            update.message.reply_text("This command is just for groups!")
        else:
            func(update, context)

    return wrapper_func


def just_for_pv(func):
    def wrapper_func(update, context):
        if update.effective_chat.id != update.message.from_user["id"]:
            update.message.reply_text("This command is just for private chat!")
        else:
            func(update, context)

    return wrapper_func


@just_for_group
def new_game(update: telegram.Update, context: telegram.ext.CallbackContext):
    group_id = update.effective_chat.id
    group_data = context.chat_data
    user = update.message.from_user
    user_data = context.user_data
    if "active_game" not in group_data.keys():
        game = Game(group_id, group_data)
        group_data["active_game"] = game
        context.job_queue.run_once(game.start_game, 60, context=(update.message.chat_id, context.chat_data),
                                   name=group_id)
        context.bot.send_sticker(chat_id=game.group_chat_id,
                                 sticker="CAACAgQAAxkBAAEBEGZfEajfE4ubecspTvk_h_MmLWldhwACFwAD1ul3K_CgFM5dUHoRGgQ")
        update.message.reply_text("New game started")
        game.join_game(user, user_data, update, context)
    else:
        update.message.reply_text("This group has an unfinished game!")


@just_for_pv
def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    update.message.reply_text("Hi!")


@just_for_group
def join(update: telegram.Update, context: telegram.ext.CallbackContext):
    user = update.message.from_user
    group_data = context.chat_data
    user_data = context.user_data
    if "active_game" in group_data.keys():
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        params = {'chat_id': user['id'],
                  'text': f"Analyzing your request to join the mafia game in group {update.effective_chat['title']}"}
        r = requests.get(url=url, params=params)
        has_subscribed = r.json()['ok']
        if has_subscribed:
            group_game = group_data["active_game"]
            group_game.join_game(user, user_data, update, context)
        else:
            update.message.reply_text("Please start the bot in private chat and try again!")
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


@admin_permission
@just_for_group
def end_game(update: telegram.Update, context: telegram.ext.CallbackContext):
    group_data = context.chat_data
    if "active_game" in group_data.keys():
        group_data["active_game"].delete_game(context)
        update.message.reply_text("Game ended")
    else:
        update.message.reply_text("There is no game in this group!")


def button(update: telegram.Update, context: telegram.ext.CallbackContext):
    global the_player
    query = update.callback_query
    game = context.user_data["active_game"]
    if game.state == GameState.Day:
        query.answer()
        vote = query.data
        print(query.from_user)
        if vote == "YES":
            if '@' + query.from_user['username'] not in game.day_votes:
                game.day_votes.append('@' + query.from_user['username'])
        else:
            if '@' + query.from_user['username'] in game.day_votes:
                game.day_votes.remove('@' + query.from_user['username'])
        keyboard = []
        keyboard.append([InlineKeyboardButton("YES", callback_data="YES")])
        keyboard.append([InlineKeyboardButton("NO", callback_data="NO")])
        text = ""
        for voter in game.day_votes:
            text = text + voter + "\n"
        query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif game.state == GameState.Night:
        query.answer()
        vote = query.data
        player = game.get_player_by_id(query.from_user['id'])
        if player.mafia_rank == 1:
            game.night_votes.update({"Mafia_shot": vote})
        elif player.role == Roles.Sniper:
            game.night_votes.update({"Sniper": vote})
        elif player.role == Roles.Detective:
            game.night_votes.update({"Detective": vote})
        elif player.role == Roles.Doctor:
            game.night_votes.update({"Doctor": vote})
        query.edit_message_text(text=f"Your choice: @{vote}")


dispatcher = updater.dispatcher
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(CommandHandler("new", new_game))
dispatcher.add_handler(CommandHandler("end", end_game))
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler('join', join))
dispatcher.add_handler(CommandHandler('leave', leave))
updater.start_polling()
