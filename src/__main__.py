import telegram

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from Game import Game, GameState
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
import requests
import threading
from Player import Player, Roles
from Poll import Poll
from LangUtils import get_data, get_lang, set_lang, get_database
import traceback
import codecs
from DataManager import Database
import os
from DataManager import Database, Mode

# 1212931959:AAHH9ViQhhhVRJBsEs9EwBv2pfkg8BMDFS4 Real Token
TOKEN = '404 Not Found'

# TOKEN = '1212931959:AAHH9ViQhhhVRJBsEs9EwBv2pfkg8BMDFS4'
updater = Updater(token=TOKEN, use_context=True)
bot = telegram.Bot(TOKEN)


def has_subscribed(update, context):
    user_id = update.message.from_user['id']
    chat_title = update.effective_chat['title']
    language = get_lang(update, context)
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    with codecs.open(os.path.join("Lang", language, "Analyzing"), 'r', encoding='utf8') as file:
        params = {'chat_id': user_id, 'text': f"{file.read()} {chat_title}"}
    r = requests.get(url=url, params=params)
    return r.json()['ok']


def testing(func):
    def wrapper_func(update, context):
        try:
            func(update, context)
        except Exception as e:
            traceback.print_exc(e)

    return wrapper_func


def admin_permission(func):
    def wrapper_func(update, context):
        group_id = update.effective_chat.id
        user_id = update.message.from_user['id']
        role = context.bot.get_chat_member(group_id, user_id).status
        if role == 'creator' or role == 'administrator' or group_id == user_id:
            func(update, context)
        else:
            language = get_lang(update, context)
            with codecs.open(os.path.join("Lang", language, "AdminPermission"), 'r', encoding='utf8') as file:
                update.message.reply_text(file.read())

    return wrapper_func


def just_for_group(func):
    def wrapper_func(update, context):
        if update.effective_chat.id == update.message.from_user["id"]:
            language = get_lang(update, context)
            with codecs.open(os.path.join("Lang", language, "JustForGroup"), 'r', encoding='utf8') as file:
                update.message.reply_text(file.read())
        else:
            func(update, context)

    return wrapper_func


def just_for_pv(func):
    def wrapper_func(update, context):
        if update.effective_chat.id != update.message.from_user["id"]:
            language = get_lang(update, context)
            with codecs.open(os.path.join("Lang", language, "JustForPV"), 'r', encoding='utf8') as file:
                update.message.reply_text(file.read())
        else:
            func(update, context)

    return wrapper_func


def fill_data(func):
    def wrapper_func(update, context):
        if context.user_data == {}:
            dic = get_database(update, context, True)
            if dic != None:
                for key, value in dic.items():
                    context.user_data[key] = value
            else:
                context.user_data["total_games"] = 0
                context.user_data["mafia_win"] = 0
                context.user_data["mafia_lose"] = 0
                context.user_data["city_win"] = 0
                context.user_data["city_lose"] = 0
                context.user_data["mafia_win_percent"] = 0
                context.user_data["city_win_percent"] = 0
                context.user_data["win_percent"] = 0
            context.user_data["state"] = None
            context.user_data["lang"] = 'en'
            context.user_data["lang_message"] = []
        if update.message.from_user.id != update.effective_chat.id:
            if context.chat_data == {}:
                for key, value in get_database(update, context).items():
                    context.chat_data[key] = value
                context.chat_data["lang_message"] = []
                context.chat_data["state"] = None
        func(update, context)

    return wrapper_func


@just_for_group
@fill_data
def new_game(update: telegram.Update, context: telegram.ext.CallbackContext):
    group_id = update.effective_chat.id
    group_data = context.chat_data
    user = update.message.from_user
    user_data = context.user_data
    language = get_lang(update, context)
    if "active_game" not in group_data.keys():
        if has_subscribed(update, context):
            game = Game(group_id, group_data, context, update)
            group_data["active_game"] = game
            game.start()
            context.bot.send_sticker(chat_id=game.group_chat_id,
                                     sticker="CAACAgQAAxkBAAEBEGZfEajfE4ubecspTvk_h_MmLWldhwACFwAD1ul3K_CgFM5dUHoRGgQ")

            with codecs.open(os.path.join("Lang", language, "NewGame"), 'r', encoding='utf8') as file:
                update.message.reply_text(file.read())
            game.join_game(user, user_data)
        else:
            with codecs.open(os.path.join("Lang", language, "StartPV"), 'r', encoding='utf8') as file:
                update.message.reply_text(file.read())
    else:
        with codecs.open(os.path.join("Lang", language, "UnfinishedGame"), 'r', encoding='utf8') as file:
            update.message.reply_text(file.read())


@fill_data
@just_for_pv
def start(update: telegram.Update, context: telegram.ext.CallbackContext):
    t = threading.Thread(target=set_lang, args=(update, context))
    t.start()
    with codecs.open(os.path.join("Lang", "en", "Start"), 'r', encoding='utf8') as file:
        update.message.reply_text(file.read())


@fill_data
@just_for_group
def join(update: telegram.Update, context: telegram.ext.CallbackContext):
    user = update.message.from_user
    group_data = context.chat_data
    user_data = context.user_data
    user = update.message.from_user
    language = get_lang(update, context)
    if "active_game" in group_data.keys():
        if has_subscribed(update, context):
            group_game = group_data["active_game"]
            if "active_game" not in user_data.keys():
                group_game.join_game(user, user_data)
            else:
                if user_data["active_game"] == group_game:
                    with codecs.open(os.path.join("Lang", language, "AlreadyJoined"), 'r', encoding='utf8') as file:
                        update.message.reply_markdown(file.read())
                        context.bot.send_message(
                            chat_id=user['id'], text=file.read())
                else:
                    with codecs.open(os.path.join("Lang", language, "AlreadyJoinedAnotherGroup"), 'r',
                                     encoding='utf8') as file:
                        update.message.reply_markdown(file.read())
                        context.bot.send_message(
                            chat_id=user['id'], text=file.read())

        else:
            with codecs.open(os.path.join("Lang", language, "StartPV"), 'r', encoding='utf8') as file:
                update.message.reply_text(file.read())
    else:
        with codecs.open(os.path.join("Lang", language, "NoGame"), 'r', encoding='utf8') as file:
            update.message.reply_text(file.read())


@fill_data
@just_for_group
def leave(update: telegram.Update, context: telegram.ext.CallbackContext):
    user = update.message.from_user
    group_data = context.chat_data
    user_data = context.user_data
    language = get_lang(update, context)
    if "active_game" in group_data.keys():
        group_game = group_data["active_game"]
        if not group_game.is_started:
            group_game.leave_game(user, user_data)
        else:
            with codecs.open(os.path.join("Lang", language, "HasStartedLeave"), 'r', encoding='utf8') as file:
                update.message.reply_text(file.read())

    else:
        with codecs.open(os.path.join("Lang", language, "NoGame"), 'r', encoding='utf8') as file:
            update.message.reply_text(file.read())


@fill_data
@admin_permission
@just_for_group
def end_game(update: telegram.Update, context: telegram.ext.CallbackContext):
    group_data = context.chat_data
    language = get_lang(update, context)
    if "active_game" in group_data.keys():
        group_data["active_game"].delete_game()
        with codecs.open(os.path.join("Lang", language, "EndGame"), 'r', encoding='utf8') as file:
            update.message.reply_text(file.read())
    else:
        with codecs.open(os.path.join("Lang", language, "NoGame"), 'r', encoding='utf8') as file:
            update.message.reply_text(file.read())


def button(update: telegram.Update, context: telegram.ext.CallbackContext):
    query = update.callback_query
    game = context.user_data["active_game"]
    if game.state == GameState.Day:
        language = context.chat_data["lang"]
        vote = query.data
        if game.get_player_by_id(query.from_user['id']) != None and query['message']['chat'][
                'id'] == game.group_chat_id:
            if vote == "YES" or vote == "آره":
                game.voters[query.from_user['id']] = "YES"
            else:
                game.voters[query.from_user['id']] = "NO"
            context.bot.answer_callback_query(
                query.id, text=f"{vote}")
            keyboard = []
            if language == 'en':
                keyboard.append(
                    [InlineKeyboardButton("YES", callback_data="YES")])
                keyboard.append(
                    [InlineKeyboardButton("NO", callback_data="NO")])
            else:
                keyboard.append(
                    [InlineKeyboardButton("آره", callback_data="آره")])
                keyboard.append(
                    [InlineKeyboardButton("نه", callback_data="نه")])
            if game.edit_vote:
                text = query.message.text_markdown
                lines = text.splitlines(True)
                text = lines[0] + lines[1]
                if text[-1] == '\n':
                    text = text[:-1]
                for user_id in game.voters.keys():
                    p = game.get_player_by_id(user_id)
                    text += "  \n" + p.get_markdown_call()
                query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(
                    keyboard), parse_mode="Markdown")

    elif game.state == GameState.Night:
        language = context.user_data['active_game'].group_data["lang"]
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
        if language == 'en':
            query.edit_message_text(text="Your choice: " + game.get_player_by_id(int(vote)).get_markdown_call(),
                                    parse_mode="MarkDown")
        else:
            query.edit_message_text(text="انتخاب انجام شد: " + game.get_player_by_id(int(vote)).get_markdown_call(),
                                    parse_mode="MarkDown")


@fill_data
def help_me(update, context):
    language = get_lang(update, context)
    with codecs.open(os.path.join("Lang", language, "Help"), 'r', encoding='utf8') as file:
        context.bot.send_message(
            chat_id=update.message.chat_id, text=file.read(), parse_mode="Markdown")


@fill_data
@admin_permission
def lang(update, context):
    dic = get_data(update, context)
    dic["state"] = "lang"
    keyboard = ReplyKeyboardMarkup(
        [["English", "فارسی"]], resize_keyboard=True, one_time_keyboard=True)
    language = dic["lang"]
    with codecs.open(os.path.join("Lang", language, "ChooseLang"), 'r', encoding='utf8') as file:
        message = context.bot.send_message(chat_id=update.message.chat_id, text=file.read(
        ), parse_mode="Markdown", reply_markup=keyboard)
        dic["lang_message"].append(message)


@fill_data
def text_handler(update, context):
    dic = get_data(update, context)
    if dic["state"] == "lang":
        if update.effective_message.text == "English":
            dic["lang"] = "en"
        else:
            dic["lang"] = "fa"
        set_lang(update, context)
        for message in dic["lang_message"]:
            message.delete()
        dic["lang_message"] = []
        with codecs.open(os.path.join("Lang", dic["lang"], "ChangeLang"), 'r', encoding='utf8') as file:
            context.bot.send_message(
                chat_id=update.effective_chat.id, text=file.read(), parse_mode="Markdown",
                reply_markup=ReplyKeyboardRemove())
    dic["state"] = None


def new_member(update, context):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            if get_database(update, context) is None:
                context.chat_data["state"] = None
                context.chat_data["lang"] = 'en'
                context.chat_data["lang_message"] = []
                context.chat_data["total_games"] = 0
                context.chat_data["mafia"] = 0
                context.chat_data["city"] = 0
                context.chat_data['mafia_percent'] = 0
                context.chat_data['city_percent'] = 0
                set_lang(update, context)
            else:
                for key, value in get_database(update, context).items():
                    context.chat_data[key] = value
                context.chat_data["lang_message"] = []
                context.chat_data["state"] = None


@fill_data
def stats(update: telegram.Update, context: telegram.ext.CallbackContext):
    lang = get_lang(update, context)
    user = update.message.from_user
    player_data = context.user_data
    user_id = user["id"]
    user_name = user.full_name
    mark_down = f"[{user_name}](tg://user?id={str(user_id)})"
    city_total = player_data["city_win"] + player_data["city_lose"]
    mafia_total = player_data["mafia_win"] + player_data["mafia_lose"]
    text = ""
    if lang == 'en':
        text = f"Stats for {mark_down}:\nplayed: {player_data['total_games']} times\nWin rate: {int(player_data['win_percent'])}%\nCity: {city_total} Win rate: {int(player_data['city_win_percent'])}%\nMafia: {mafia_total} Win rate: {int(player_data['mafia_win_percent'])}%\n------------------------"
    else:
        text = f"آمار {mark_down} در بازی:\nبازی های انجام شده: {player_data['total_games']}\nدرصد برد: {int(player_data['win_percent'])}%\n\nدفعاتی که شهروند بوده: {city_total}\n درصد برد شهروندی: {int(player_data['city_win_percent'])}%\n\nدفعاتی که مافیا بوده: {mafia_total}\n درصد برد مافیایی: {int(player_data['mafia_win_percent'])}%\n------------------------"
    update.message.reply_markdown(text=text)


@just_for_group
@fill_data
def group_stats(update: telegram.Update, context: telegram.ext.CallbackContext):
    group = context.chat_data
    lang = group["lang"]
    title = update.effective_chat['title']
    text = ""
    if lang == 'en':
        text = f"Stats for group {title}:\nTotal games: {group['total_games']}\nCity win: {group['city']}\nMafia win: {group['mafia']}"
    else:
        text = f"آمار گروه {title}:\nبازی های انجام شده: {group['total_games']}\nتعداد برد شهر: {group['city']}\nتعداد برد مافیا: {group['mafia']}"
    update.message.reply_markdown(text=text)


dispatcher = updater.dispatcher
dispatcher.add_handler(CallbackQueryHandler(button))
dispatcher.add_handler(CommandHandler("new", new_game))
dispatcher.add_handler(CommandHandler("help", help_me))
dispatcher.add_handler(CommandHandler("end", end_game))
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(CommandHandler('join', join))
dispatcher.add_handler(CommandHandler('leave', leave))
dispatcher.add_handler(CommandHandler('lang', lang))
dispatcher.add_handler(CommandHandler('stats', stats))
# dispatcher.add_handler(CommandHandler('global_stats', global_stats))
dispatcher.add_handler(CommandHandler('group_stats', group_stats))
dispatcher.add_handler(MessageHandler(
    Filters.status_update.new_chat_members, new_member))
dispatcher.add_handler(MessageHandler(Filters.all, text_handler))
updater.start_polling()
