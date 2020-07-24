import telegram
import random
from Player import Player, Rules
from telegram.ext import Updater
from Poll import Poll
import time
import enum


class GameState(enum.Enum):
    Day = 0
    Night = 1


class Game:

    def __init__(self, group_chat_id, group_data):
        self.night_votes = {"Mafia_shot": None,
                            "Detective": None, "Doctor": None, "Sniper": None}
        self.day_votes = []
        '''example: ["@salinaria" , "mohokaja"}'''
        self.mafias = []
        self.citizens = []
        self.players = []
        self.just_players = []
        self.group_chat_id = group_chat_id
        self.group_data = group_data
        self.is_started = False
        self.state = GameState.Day

    def get_list(self):
        list_join = ""
        for player in self.players:
            list_join = list_join + "@" + player.user_name + "\n"

        return list_join

    def join_game(self, user: telegram.User, user_data: telegram.ext.CallbackContext.user_data,
                  update: telegram.Update, context: telegram.ext.CallbackContext):
        if "active_game" not in user_data.keys():
            user_data["active_game"] = self
            player = Player(user['first_name'],
                            user['username'], user['id'], user_data, self)
            self.players.append(player)
            self.just_players.append(player)
            update.message.reply_text(self.get_list())

            context.bot.send_message(
                chat_id=user['id'], text="You joined the game successfully")
        else:
            if user_data["active_game"] == self:
                update.message.reply_text(
                    '@' + user['username'] + " has already joined the game!")
                context.bot.send_message(
                    chat_id=user['id'], text="You have already joined the game")
            else:
                update.message.reply_text(
                    '@' + user['username'] + " has already joined a game in another group!")
                context.bot.send_message(
                    chat_id=user['id'], text="You have already joined a game in another group")

    def leave_game(self, user: telegram.User, user_data: telegram.ext.CallbackContext.user_data,
                   update: telegram.Update):
        if "active_game" in user_data.keys():
            if user_data["active_game"] == self:
                del user_data["active_game"]
                player = self.get_player_by_user(user)
                del self.votes['@' + player.user_name]
                self.players.remove(player)
                self.just_players.remove(player)
                update.message.reply_text(
                    '@' + player.user_name + " successfully left the game!")
            else:
                update.message.reply_text("You are not in this game!")
        else:
            update.message.reply_text("You have not joined a game yet!")

    def get_alive_players(self):
        alive = []
        for player in self.players:
            if player.is_alive:
                alive.append(player)
        return alive

    def start_game(self, context: telegram.ext.CallbackContext):
        group_data = self.group_data
        if "active_game" in group_data.keys():
            game = group_data["active_game"]
            if len(game.players) > 2:
                game.set_players_rules(context)
                context.bot.send_message(
                    chat_id=self.group_chat_id, text='Game has been started!')
                self.is_started = True
                self.day(context)
            else:
                context.bot.send_message(chat_id=self.group_chat_id, text='Game is canceled because there is not '
                                                                          'enough players. Invite your friends to'
                                                                          ' join.')
                self.delete_game(context)

        else:
            context.bot.send_message(
                chat_id=self.group_chat_id, text='There is no game in this group!')

    def delete_game(self, context: telegram.ext.CallbackContext):
        if not self.is_started:
            for job in context.job_queue._queue.queue:
                if job[1].name == self.group_chat_id:
                    context.job_queue._queue.queue.remove(job)
        for player in self.players:
            del player.user_data["active_game"]
        del self.group_data["active_game"]
        self.just_players.clear()

    def set_players_rules(self, context: telegram.ext.CallbackContext):
        mafia_number = 0
        # GodFather
        if len(self.players) >= 6:
            r = random.randrange(0, len(self.just_players))
            self.just_players[r].rule = Rules.GodFather
            self.mafias.append(self.just_players[r])
            self.just_players[r].send_rule(context)
            self.just_players.pop(r)
            mafia_number = mafia_number + 1
        # Other Mafias
        for i in range(int(len(self.players) / 3) - mafia_number):
            r = random.randrange(0, len(self.just_players))
            self.just_players[r].rule = Rules.Mafia
            self.mafias.append(self.just_players[r])
            self.just_players[r].send_rule(context)
            self.just_players.pop(r)
        # Doctor
        r = random.randrange(0, len(self.just_players))
        self.just_players[r].rule = Rules.Doctor
        self.citizens.append(self.just_players[r])
        self.just_players[r].send_rule(context)
        self.just_players.pop(r)
        # Detective
        r = random.randrange(0, len(self.just_players))
        self.just_players[r].rule = Rules.Detective
        self.citizens.append(self.just_players[r])
        self.just_players[r].send_rule(context)
        self.just_players.pop(r)
        # Sniper
        if len(self.players) > 6:
            r = random.randrange(0, len(self.just_players))
            self.just_players[r].rule = Rules.Sniper
            self.citizens.append(self.just_players[r])
            self.just_players[r].send_rule(context)
            self.just_players.pop(r)
        # Citizens
        for player in self.just_players:
            print(len(self.just_players))
            player.rule = Rules.Citizen
            self.citizens.append(player)
            player.send_rule(context)
            self.just_players.remove(player)

    def day(self, context: telegram.ext.CallbackContext):
        self.state = GameState.Day
        for player in self.get_alive_players():
            context.job_queue.run_once(player.talk(self.group_chat_id, context), 5, context)
        for player in self.get_alive_players():
            poll = Poll("Do you want to kill " + "@" + player.user_name + " ?", ["YES", "NO"],
                        self.group_chat_id)
            poll.send_poll(context)
            context.bot.send_message(chat_id=self.group_chat_id, text="15 seconds left until the end of voting")
            context.job_queue.run_once(self.show_result, 15, context)
