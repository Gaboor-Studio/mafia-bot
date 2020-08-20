def get_data(update, context):
    if update.message.from_user.id == update.effective_chat.id:
        dic = context.user_data
    else:
        dic = context.chat_data
    return dic


def get_lang(update, context):
    return get_data(update, context)["lang"]
