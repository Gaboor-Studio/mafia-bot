import telegram
import random
from Player import Player
from telegram.ext import CommandHandler
from Poll import Poll


class Game:

    def __init__(self, group_chat_id, group_data):
        self.votes = []
        self.players = []
        self.group_chat_id = group_chat_id
        self.group_data = group_data
        self.is_started = False

    def join_game(self, user: telegram.User, user_data: telegram.ext.CallbackContext.user_data,
                  update: telegram.Update, context: telegram.ext.CallbackContext):
        if "active_game" not in user_data.keys():
            user_data["active_game"] = self
            player = Player(user['first_name'], user['username'], user['id'], user_data)
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
                player = self.get_player_by_user(user)
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

    def get_player_by_user(self, user: telegram.User):
        for player in self.players:
            if player.user_name == user["username"]:
                return player
        return None

    def get_player_by_id(self, id: str):
        for player in self.players:
            if player.user_id == id:
                return player
        return None

    def get_player_by_user_name(self, user_name: str):
        for player in self.players:
            if player.user_name == user_name:
                return player
        return None

    def get_alive_players(self):
        list = []
        for player in self.players:
            if player.is_alive:
                list.append(player)
        return list

    def get_dead_players(self):
        list = []
        for player in self.players:
            if not player.is_alive:
                list.append(player)
        return list

    def start_game(self, context: telegram.ext.CallbackContext):
        group_data = self.group_data
        if "active_game" in group_data.keys():
            game = group_data["active_game"]
            if len(game.players) > 2:
                game.init()
                for player in game.players:
                    context.bot.send_message(chat_id=player.user_id, text=player.rule)
                context.bot.send_message(chat_id=self.group_chat_id, text='Game has been started!')
                self.is_started = True
                for player in game.players:  # need to add this line to playturn method later
                    player.talk(self.group_chat_id, context)
                    poll = Poll("hi", game.players, player)
                    poll.send_poll(context)

            else:
                context.bot.send_message(chat_id=self.group_chat_id, text='Game is canceled because there is not '
                                                                          'enough players. Invite your friends to'
                                                                          ' join.')
                self.delete_game(context)

        else:
            context.bot.send_message(chat_id=self.group_chat_id, text='There is no game in this group!')

    def delete_game(self, context: telegram.ext.CallbackContext):
        if not self.is_started:
            for job in context.job_queue._queue.queue:
                if job[1].name == self.group_chat_id:
                    context.job_queue._queue.queue.remove(job)
        for player in self.players:
            del player.user_data["active_game"]
        del self.group_data["active_game"]
