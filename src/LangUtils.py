from DataManager import Database, Mode


def get_database(update, context, is_player=False):
    dic = {}
    if update.message.from_user.id == update.effective_chat.id or is_player:
        dic = Database.do(Mode.get_player, update.message.from_user.id)
    else:
        dic = Database.do(Mode.get_group, update.effective_chat.id)
    return dic


def get_data(update, context):
    if update.message.from_user.id == update.effective_chat.id:
        dic = context.user_data
    else:
        dic = context.chat_data
    return dic


def get_lang(update, context):
    return get_data(update, context)["lang"]


def set_lang(update, context):
    if update.message.from_user.id == update.effective_chat.id:
        Database.do(Mode.players_language,
                    update.message.from_user.id, context.user_data['lang'])
    else:
        Database.do(Mode.group_language, update.effective_chat.id,
                    context.chat_data['lang'])
