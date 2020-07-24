import telegram
import random
from Player import Player, Mafia, GodFather, Citizen, Doctor, Detective, Sniper
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
        self.day_votes = {}
        '''example: {"amirparsa_sal" : {"yes_votes" : ["salinaria","mohokaja"], "no_votes" : [] },
                                                "salinaria" : {"yes_votes" : ["amirparsa_sal"], "no_votes" : []
                                                                                                  "}'''

        self.rules = {"Godfather": None, "Mafia": [], "Doctor": None,
                      "Detective": None, "Sniper": None, "Citizen": []}
        self.mafias = []
        self.citizens = []
        self.players = []
        self.just_players = []
        self.group_chat_id = group_chat_id
        self.group_data = group_data
        self.is_started = False
        self.state = GameState.Day

    def join_game(self, user: telegram.User, user_data: telegram.ext.CallbackContext.user_data,
                  update: telegram.Update, context: telegram.ext.CallbackContext):
        if "active_game" not in user_data.keys():
            user_data["active_game"] = self
            player = Player(user['first_name'],
                            user['username'], user['id'], user_data, self)
            self.players.append(player)
            # update.message.reply_text(self.get_list())
            context.bot.send_message(
                chat_id=user['id'], text="You joined the game successfully")
            self.day_votes.update(
                {player.user_name: {"yes_votes": [], "no_votes": []}})
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
                update.message.reply_text(
                    '@' + player.user_name + " successfully left the game!")
            else:
                update.message.reply_text("You are not in this game!")
        else:
            update.message.reply_text("You have not joined a game yet!")

    def start_game(self, context: telegram.ext.CallbackContext):
        group_data = self.group_data
        if "active_game" in group_data.keys():
            game = group_data["active_game"]
            if len(game.players) > 2:
                game.set_players_rules(context)
                for player in game.players:
                    context.bot.send_message(
                        chat_id=player.user_id, text=player.rule)
                context.bot.send_message(
                    chat_id=self.group_chat_id, text='Game has been started!')
                self.is_started = True
                # self.turn(context)

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

    # def find_in_players(self, player):
    #     for p in self.players:
    #         if (p.equals(player)):
    #             return self.players.index(p)
    #     return - 1

    def set_players_rules(self):
        mafia_number = 1
        # First Mafia
        r = random.randrange(0, len(self.just_players))
        index = self.find_in_players(self.just_players[r])
        self.players[index] = Mafia(self.just_players[r].name, self.just_players[r].user_name, self.just_players[r].user_id, self.just_players[r].user_data,
                                    self.just_players[r].active_game)
        self.mafias.append(self.players[index])
        self.just_players.pop(r)

        # GodFather
        if mafia_number < len(self.players) // 3:
            r = random.randrange(0, len(self.just_players))
            index = self.find_in_players(self.just_players[r])
            self.players[index] = GodFather(self.just_players[r].name, self.just_players[r].user_name, self.just_players[r].user_id, self.just_players[r].user_data,
                                            self.just_players[r].active_game)
            self.mafias.append(self.players[index])
            mafia_number = 2
            self.just_players.pop(r)

        # Other Mafias
        while(len(self.players) // 3 < mafia_number):
            r = random.randrange(0, len(self.just_players))
            index = self.find_in_players(self.just_players[r])
            self.players[index] = Mafia(self.just_players[r].name, self.just_players[r].user_name, self.just_players[r].user_id, self.just_players[r].user_data,
                                        self.just_players[r].active_game)
            self.mafias.append(self.players[index])
            self.just_players.pop(r)
            mafia_number += 1
        # Doctor
        r = random.randrange(0, len(self.just_players))
        index = self.find_in_players(self.just_players[r])
        self.players[index] = Doctor(self.just_players[r].name, self.just_players[r].user_name, self.just_players[r].user_id, self.just_players[r].user_data,
                                     self.just_players[r].active_game)
        self.citizens.append(self.players[index])
        self.just_players.pop(r)

        # Detective
        r = random.randrange(0, len(self.just_players))
        index = self.find_in_players(self.just_players[r])
        self.players[index] = Detective(self.just_players[r].name, self.just_players[r].user_name, self.just_players[r].user_id, self.just_players[r].user_data,
                                        self.just_players[r].active_game)
        self.citizens.append(self.players[index])
        self.just_players.pop(r)

        # Sniper
        if len(self.players) > 6:
            r = random.randrange(0, len(self.just_players))
            index = self.find_in_players(self.just_players[r])
            self.players[index] = Sniper(self.just_players[r].name, self.just_players[r].user_name, self.just_players[r].user_id, self.just_players[r].user_data,
                                         self.just_players[r].active_game)
            self.citizens.append(self.players[index])
            self.just_players.pop(r)

        # Citizens
        for i in range(len(self.just_players)):
            index = self.find_in_players(self.just_players[i])
            self.players[index] = Mafia(self.just_players[i].name, self.just_players[i].user_name, self.just_players[i].user_id, self.just_players[i].user_data,
                                        self.just_players[i].active_game)
            self.citizens.append(self.just_players[i])
            self.just_players.pop(i)

        # for i in range(len(self.players)):
        #     context.bot.send_sticker(chat_id=self.players[i].user_id,
        #                              sticker=self.players[i].sticker)
        # context.bot.send_message(

