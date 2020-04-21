import telegram
import random
from Player import Player


class Game:

    def __init__(self, group_chat_id):
        self.players = []
        self.group_chat_id = group_chat_id

    def join_game(self, user: telegram.User, user_data: telegram.ext.CallbackContext.user_data,
                  update: telegram.Update, context: telegram.ext.CallbackContext):
        if "active_game" not in user_data.keys():
            user_data["active_game"] = self
            player = Player(user['first_name'], user['username'], user['id'])
            self.players.append(player)
            update.message.reply_text(self.get_list())
            context.bot.send_message(chat_id=user['id'], text="You joined the game successfully")
        else:
            if user_data["active_game"] == self:
                update.message.reply_text('@' + user['username'] + " has already joined the game!")
                context.bot.send_message(chat_id=user['id'], text="You have already joined the game")
            else:
                update.message.reply_text('@' + user['username'] + " has already joined a game in another group!")
                context.bot.send_message(chat_id=user['id'], text="You have already joined a game in another group")

    def leave_game(self, user: telegram.User, user_data: telegram.ext.CallbackContext.user_data,
                   update: telegram.Update):
        if "active_game" in user_data.keys():
            if user_data["active_game"] == self:
                del user_data["active_game"]
                player = self.get_player(user)
                self.players.remove(player)
                update.message.reply_text('@' + player.user_name + " successfully left the game!")
            else:
                update.message.reply_text("You are not in this game!")
        else:
            update.message.reply_text("You have not joined a game yet!")

    def init(self):
        for i in range(int(len(self.players) / 3)):
            while True:
                r = random.randrange(0, len(self.players), 1)
                if self.players[r].rule == "citizen":
                    self.players[r].rule = "mafia"
                    break
        while True:
            r = random.randrange(0, len(self.players), 1)
            if self.players[r].rule == "citizen":
                self.players[r].rule = "police"
                break
        while True:
            r = random.randrange(0, len(self.players), 1)
            if self.players[r].rule == "citizen":
                self.players[r].rule = "doctor"
                break

    def get_list(self):
        players_list = ""
        for player in self.players:
            players_list += '@' + player.user_name + '\n'
        return players_list

    def get_player(self, user: telegram.User):
        for player in self.players:
            if player.user_name == user["username"]:
                return player
        return None

    def start_game(self, context: telegram.ext.CallbackContext):
        group_data = context.job.context[1]
        if "active_game" in group_data.keys():
            game = group_data["active_game"]
            game.init()
            for player in game.players:
                context.bot.send_message(chat_id=player.user_id, text=player.rule)
            context.bot.send_message(chat_id=context.job.context[0], text='Game has been started!')
        else:
            context.bot.send_message(chat_id=context.job.context[0], text='There is no game in this group!')
