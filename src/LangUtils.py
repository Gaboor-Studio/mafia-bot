from DataManager import Database, Mode


def get_database(update, context):
    dic = {}
    if update.message.from_user.id == update.effective_chat.id:
        print("get database")
        dic = Database.do(Mode.get_player, update.message.from_user.id)
        print("get database")
        # if dic is None:
        #     print("get database")
        #     Database.do(Mode.players_language,
        #                 update.message.from_user.id, context.user_data["lang"])
        #     print("get database")
        #     dic = Database.do(Mode.get_player, update.message.from_user.id)
        #     print("get database")
    else:
        dic = Database.do(Mode.get_group, update.effective_chat.id)
        # if dic is None:
        #     Database.do(Mode.group_language,
        #                 update.effective_chat.id, 'en')
        #     dic = Database.do(Mode.get_group, update.effective_chat.id)
    print("get database")
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
