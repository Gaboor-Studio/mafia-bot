import telegram
import random
from Player import Player
from telegram.ext import Updater
from Poll import Poll


class Game:

    def __init__(self, group_chat_id, group_data):
        self.votes = {}
        self.players = []
        self.group_chat_id = group_chat_id
        self.group_data = group_data
        self.is_started = False
        self.state="day";

    def join_game(self, user: telegram.User, user_data: telegram.ext.CallbackContext.user_data,
                  update: telegram.Update, context: telegram.ext.CallbackContext):
        if "active_game" not in user_data.keys():
            user_data["active_game"] = self
            player = Player(user['first_name'], user['username'], user['id'], user_data)
            self.players.append(player)
            update.message.reply_text(self.get_list())
            context.bot.send_message(chat_id=user['id'], text="You joined the game successfully")
            arrlist = []
            self.votes.update({'@' + player.user_name: arrlist})
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
                del self.votes['@' + player.user_name]
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
                self.day(context)
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

    # def show_result(self, context: telegram.ext.CallbackContext):
    #     dead = {}
    #     for player, votes in self.votes:
    #         votes_list = ""
    #         votes_count = 0
    #         for username in votes:
    #             votes_list += username + " and "
    #             votes_count += 1
    #         dead.update({player: votes_count})
    #         context.bot.send_message(chat_id=self.group_chat_id, text=player + ' voted to' + votes_list)
    #     kill = ""
    #     kill_num = 0
    #     number_of_voters={}
    #     for player in self.get_alive_players():
    #         number_of_voters.update({player.user_name : 0})
    #     for votes in dead.values():
    #         if dead.get(player) > kill_num:
    #             kill = player
    #             kill_num = dead.get(player)
    #     context.bot.send_message(chat_id=self.group_chat_id, text=kill + " died")
    #     kill.replace('@', '')
    #     dead_player = self.get_player_by_user_name(kill)
    #     dead_player.is_alive = False
    #     del self.votes['@' + kill]

    def day(self, context: telegram.ext.CallbackContext):
        self.state = "day"
        for player in self.get_alive_players():
            player.talk(self.group_chat_id, context)
        for player in self.get_alive_players():
            poll = Poll("Who do you want to kill?", self.other_players(player), player)
            poll.send_poll(context)
        context.bot.send_message(chat_id=self.group_chat_id, text="30 seconds left until the end of voting")
        context.job_queue.run_once(self.show_result, 30, context)

    def get_mafia_number(self):
        counter = 0
        for player in self.get_alive_players():
            if (player.rule == 'mafia'):
                counter = counter + 1
        return counter

    def mafia_list(self, context):
        mafias_list = ""
        founded_mafias = 0
        for player in self.players:
            if (player.rule == 'mafia'):
                founded_mafias += 1
                if (founded_mafias != self.get_mafia_number()):
                    mafias_list += "@" + player.user_name + " and "
                if (founded_mafias == self.get_mafia_number()):
                    mafias_list += "@" + player.user_name
        message = ""
        if (self.get_mafia_number() == 1):
            message = "You are the only mafia of the game. good luck :)"
        if (self.get_mafia_number() > 1):
            message = "Your mafia team is " + mafias_list + "good luck :)"
        return message

    def mafia_want(self):
        targets = []
        for player in self.get_alive_players():
            if (player.rule != 'mafia'):
                targets.append(player)
        return targets

    def other_players(self, player):
        players = []
        for p in self.get_alive_players():
            if (p.rule != player.rule):
                players.append(player)
        return players

    def night(self, context: telegram.ext.CallbackContext):
        self.state = "night"
        for player in self.players:
            if (player.rule == 'police'):
                poll = Poll("who do you doubt🕵️?", self.other_players(player), player)
                poll.send_poll(context)
            if (player.rule == 'doctor'):
                poll = Poll("who do you want to save👨‍", self.get_alive_players(), player)
                poll.send_poll(context)
            if (player.rule == 'mafia'):
                poll = Poll("who do you want to kill😈", self.mafia_want(), player)
                poll.send_poll(context)
