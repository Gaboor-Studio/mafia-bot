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
        self.players = []
        self.mafias = []
        self.citizens = []
        self.group_chat_id = group_chat_id
        self.group_data = group_data
        self.is_started = False
        self.state = GameState.Day

    def join_game(self, user: telegram.User, user_data: telegram.ext.CallbackContext.user_data,
                  update: telegram.Update, context: telegram.ext.CallbackContext):
        if "active_game" not in user_data.keys():
            user_data["active_game"] = self
            player = Player(user['first_name'],
                            user['username'], user['id'], user_data)
            self.players.append(player)
            update.message.reply_text(self.get_list())
            context.bot.send_message(
                chat_id=user['id'], text="You joined the game successfully")
            array = []
            self.votes.update({'@' + player.user_name: array})
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
                game.init()
                for player in game.players:
                    context.bot.send_message(
                        chat_id=player.user_id, text=player.rule)
                context.bot.send_message(
                    chat_id=self.group_chat_id, text='Game has been started!')
                self.is_started = True
                self.turn(context)

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

    def player_just_player(self):
        player_just_player = []
        for player in self.players:
            if type(player) == 'Player':
                player_just_player.append(player)
        return player_just_player

    def set_players_rules(self):
        mafia_number = 1
		#First Mafia
        r = random.randrange(0, len(self.player_just_player()))
        self.player_just_player()[r] = Mafia(player.name, player.user_name, player.user_id, player.user_data,
                           player.active_game)
        self.mafias.append(self.player_just_player()[r])    	
        # GodFather
        if(mafia_number<len(self.players)/3):
            r = random.randrange(0, len(self.player_just_player()))
            self.player_just_player()[r] = GodFather(player.name, player.user_name, player.user_id, player.user_data,player.active_game)  
            self.mafias.append(self.player_just_player()[r]) 
            mafia_number = 2
		#Other Mafias
        for i in range(len(self.players)/3 - mafia_number):
            r = random.randrange(0, len(self.player_just_player()))
            self.player_just_player()[r] = Mafia(player.name, player.user_name, player.user_id, player.user_data,
                           player.active_game) 
            self.mafias.append(self.player_just_player()[r]) 
        # Doctor
        r = random.randrange(0, len(self.player_just_player()))
        self.player_just_player()[r] = Doctor(player.name, player.user_name, player.user_id, player.user_data,
                           player.active_game) 
        self.citizens.append(self.player_just_player()[r]) 
        # Detective
        r = random.randrange(0, len(self.player_just_player()))
        self.player_just_player()[r] = Detective(player.name, player.user_name, player.user_id, player.user_data,
                           player.active_game)
        self.citizens.append(self.player_just_player()[r]) 
        # Sniper
        if(len(self.players>6)):
            r = random.randrange(0, len(self.player_just_player()))
            self.player_just_player()[r] = Sniper(player.name, player.user_name, player.user_id, player.user_data,
                           player.active_game) 
            self.citizens.append(self.player_just_player()[r])
        # Citizens
        for i in range(len(self.player_just_player())):
            self.player_just_player[i] = Citizen(player.name, player.user_name, player.user_id, player.user_data,
                             player.active_game)
            self.citizens.append(self.player_just_player()[i])

    def get_citizens(self):
        citizens = []
        for player in self.players:
            if isinstance(player, Citizen):
                citizens.append(player)
        return citizens
