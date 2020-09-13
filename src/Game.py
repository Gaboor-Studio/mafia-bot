import telegram
import random
from Player import Player, Roles
from telegram.ext import Updater
from Poll import Poll
import time
import enum
import threading
import ctypes
import traceback
from LangUtils import get_data, get_lang
import os
import codecs
import math
from DataManager import Database, Mode


class GameState(enum.Enum):
    Day = 0
    Night = 1


class Game(threading.Thread):

    def __init__(self, group_chat_id, group_data, context, update):
        threading.Thread.__init__(self)
        self.night_votes = {"Mafia_shot": None,
                            "Detective": None, "Doctor": None, "Sniper": None}
        self.voters = {}
        '''example: {"salinariaID":"No"}'''
        self.day_votes = {}
        '''example: {"amirparsa_salID":["salinariaID","mohokajaID"]} voters to amirparsa_sal'''
        self.mafias = []
        self.citizens = []
        self.players = []
        self.just_players = []
        self.group_chat_id = group_chat_id
        self.group_data = group_data
        self.is_started = False
        self.is_finished = False
        self.state = GameState.Day
        self.print_result = False
        self.context = context
        self.update = update
        self.messages = {"Mafia_shot": None,
                         "Detective": None, "Doctor": None, "Sniper": None}
        self.sniper_shots = 0
        self.day_night_counter = 0
        self.edit_vote = True
        self.situation_announce_votes = []
        self.situation_announce = 0
        self.force_start = []
        self.is_join = True

    def run(self):
        try:
            t = 180
            time_breaker = 0
            for i in range(33):
                if self.is_finished:
                    break
                language = self.group_data["lang"]
                if len(self.force_start) < int(len(self.players) * 2 / 3) or len(
                        self.players) < 5 or len(self.force_start) < 5:
                    time.sleep(5)
                    t -= 5
                    time_breaker = time_breaker + 1
                    if time_breaker % 6 == 0:
                        with codecs.open(os.path.join("Lang", language, f'{t}sec'), 'r', encoding='utf8') as file:
                            self.context.bot.send_message(
                                chat_id=self.group_chat_id, text=file.read())
                else:
                    break
            if not self.is_finished:
                self.is_join = False
                time.sleep(5)
                self.start_game()
        except Exception as e:
            traceback.print_exc(e)
        finally:
            if self.is_finished:
                self.delete_game()

    def get_thread_id(self):
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def raise_exception(self):
        thread_id = self.get_thread_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')

    def reset_info(self):
        self.night_votes = {"Mafia_shot": None,
                            "Detective": None, "Doctor": None, "Sniper": None}
        self.voters = {}
        self.day_votes = {}
        for player in self.get_alive_players():
            self.day_votes[player.user_id] = []

    def find_votes_more_than_half(self):
        players = []
        num_of_alive_players = len(self.get_alive_players())
        for key, value in self.day_votes.items():
            if len(value) >= math.ceil(num_of_alive_players / 2):
                players.append(self.get_player_by_id(key))
        return players

    def find_player_with_most_vote(self):
        players = []
        max_votes = 0
        for key, value in self.day_votes.items():
            if len(value) >= max_votes:
                max_votes = len(value)
        for key, value in self.day_votes.items():
            if len(value) == max_votes:
                player = self.get_player_by_id(key)
                players.append(player)
        return players

    def get_list(self):
        list_join = ""
        for player in self.players:
            list_join += player.get_markdown_call() + "\n"

        return list_join

    def get_citizens(self):
        city = []
        for player in self.get_alive_players():
            if player.role != Roles.Mafia and player.role != Roles.GodFather:
                city.append(player)
        return city

    def get_player_by_role(self, role: Roles):
        for player in self.get_alive_players():
            if player.role == role:
                return player
        return None

    def get_citizens_name(self):
        city = []
        for player in self.get_alive_players():
            if player.role != Roles.Mafia and player.role != Roles.GodFather:
                city.append(player.name)
        return city

    def join_game(self, user: telegram.User, user_data: telegram.ext.CallbackContext.user_data):
        language = self.group_data["lang"]
        if not self.is_started:
            if self.is_join:
                user_data["active_game"] = self
                player = Player(user.full_name, user.username,
                                user.id, user_data, self)
                self.players.append(player)
                self.just_players.append(player)
                with codecs.open(os.path.join("Lang", language, "CurrentPlayers"), 'r', encoding='utf8') as file:
                    self.update.message.reply_markdown(
                        file.read() + "  \n" + self.get_list())

                with codecs.open(os.path.join("Lang", language, "SuccessfullyJoin"), 'r', encoding='utf8') as file:
                    self.context.bot.send_message(
                        chat_id=user['id'], text=file.read())
        else:
            with codecs.open(os.path.join("Lang", language, "HasStartedJoin"), 'r', encoding='utf8') as file:
                self.update.message.reply_text(file.read())
                self.context.bot.send_message(
                    chat_id=user['id'], text=file.read())

    def leave_game(self, update: telegram.Update, user: telegram.User,
                   user_data: telegram.ext.CallbackContext.user_data):
        language = self.group_data["lang"]
        if "active_game" in user_data.keys():
            if user_data["active_game"] == self:
                if self.is_join:
                    del user_data["active_game"]
                    player = self.get_player_by_id(user.id)
                    if player in self.force_start:
                        self.force_start.remove(player)
                    self.players.remove(player)
                    self.just_players.remove(player)
                    with codecs.open(os.path.join("Lang", language, "LeaveGame"), 'r', encoding='utf8') as file:
                        update.message.reply_text(file.read())
            else:
                with codecs.open(os.path.join("Lang", language, "NotInGame"), 'r', encoding='utf8') as file:
                    update.message.reply_text(file.read())
        else:
            with codecs.open(os.path.join("Lang", language, "NotJoinedYet"), 'r', encoding='utf8') as file:
                update.message.reply_text(file.read())

    def force_start_game(self, update: telegram.Update, user: telegram.User,
                         user_data: telegram.ext.CallbackContext.user_data):
        language = self.group_data["lang"]
        if "active_game" in user_data.keys():
            if user_data["active_game"] == self:
                player = self.get_player_by_id(user.id)
                if player not in self.force_start:
                    num_force = int(len(self.players) * 2 / 3)
                    if num_force < 5:
                        num_force = 5
                    self.force_start.append(self.get_player_by_id(user.id))
                    with codecs.open(os.path.join("Lang", language, "RemainingPlayers"), 'r', encoding='utf8') as file:
                        text = file.read()
                        text = text.replace('$', player.get_markdown_call(), 1)
                        text = text.replace(
                            '$', f"*{str(len(self.force_start))}*", 1)
                        text = text.replace('$', f"*{str(num_force)}*", 1)
                        self.context.bot.send_message(
                            chat_id=self.group_chat_id, text=text, parse_mode="Markdown")
                else:
                    print(".")
                    with codecs.open(os.path.join("Lang", language, "AlreadyForceStop"), 'r', encoding='utf8') as file:
                        print(".")
                        update.message.reply_text(file.read())
            else:
                with codecs.open(os.path.join("Lang", language, "NotInGame"), 'r', encoding='utf8') as file:
                    update.message.reply_text(file.read())
        else:
            with codecs.open(os.path.join("Lang", language, "NotJoinedYet"), 'r', encoding='utf8') as file:
                update.message.reply_text(file.read())

    def get_alive_players(self):
        alive = []
        for player in self.players:
            if player.is_alive:
                alive.append(player)
        return alive

    def get_alive_players_name(self):
        alive = []
        for player in self.get_alive_players():
            alive.append(player.name)
        return alive

    def get_player_by_id(self, id):
        for player in self.get_alive_players():
            if player.user_id == id:
                return player
        return None

    def get_player_by_name(self, name):
        for player in self.get_alive_players():
            if player.name == name:
                return player
        return None

    def get_player_by_username(self, username):
        for player in self.get_alive_players():
            if player.user_name == username:
                return player
        return None

    def get_players_without_detect(self):
        without_detect = []
        for player in self.get_alive_players():
            if player.role != Roles.Detective:
                without_detect.append(player)
        return without_detect

    def get_players_without_sniper(self):
        without_sniper = []
        for player in self.get_alive_players():
            if player.role != Roles.Sniper:
                without_sniper.append(player)
        return without_sniper

    def start_game(self):
        language = self.group_data["lang"]
        if len(self.players) > 4:
            self.set_players_roles()
            with codecs.open(os.path.join("Lang", language, "GameStarted"), 'r', encoding='utf8') as file:
                self.context.bot.send_message(
                    chat_id=self.group_chat_id, text=file.read())
            self.is_started = True
            self.reset_info()
            self.situation_announce = len(self.get_alive_players()) // 5 + 1
            while self.result_game():
                self.turn()
        else:
            with codecs.open(os.path.join("Lang", language, "GameCanceled"), 'r', encoding='utf8') as file:
                self.context.bot.send_message(
                    chat_id=self.group_chat_id, text=file.read())
        self.is_finished = True

    def delete_game(self):
        for player in self.players:
            del player.user_data["active_game"]
        del self.group_data["active_game"]
        self.raise_exception()
        self.is_finished = True

    def set_players_roles(self):
        mafia_number = 0
        # GodFather
        if len(self.players) > 5:
            r = random.randrange(0, len(self.just_players))
            self.just_players[r].role = Roles.GodFather
            self.mafias.append(self.just_players[r])
            self.just_players[r].emoji = "🚬🧛"
            mafia_number = mafia_number + 1
            self.just_players[r].mafia_rank = mafia_number
            self.just_players[r].send_role(self.context)
            self.just_players.pop(r)
        # Other Mafias
        for i in range(int(len(self.players) / 3) - mafia_number):
            r = random.randrange(0, len(self.just_players))
            self.just_players[r].role = Roles.Mafia
            self.just_players[r].emoji = "🧛"
            self.mafias.append(self.just_players[r])
            mafia_number = mafia_number + 1
            self.just_players[r].mafia_rank = mafia_number
            self.just_players[r].send_role(self.context)
            self.just_players.pop(r)
        # Doctor
        r = random.randrange(0, len(self.just_players))
        self.just_players[r].role = Roles.Doctor
        self.just_players[r].emoji = "👨‍⚕️‍"
        self.citizens.append(self.just_players[r])
        self.just_players[r].send_role(self.context)
        self.just_players.pop(r)
        # Detective
        r = random.randrange(0, len(self.just_players))
        self.just_players[r].role = Roles.Detective
        self.just_players[r].emoji = "👮‍"
        self.citizens.append(self.just_players[r])
        self.just_players[r].send_role(self.context)
        self.just_players.pop(r)
        # Bulletproof
        """change the number to 9"""
        if len(self.players) > 9:
            r = random.randrange(0, len(self.just_players))
            self.just_players[r].role = Roles.Bulletproof
            self.just_players[r].emoji = "🛡‍"
            self.just_players[r].shield = True
            self.citizens.append(self.just_players[r])
            self.just_players[r].send_role(self.context)
            self.just_players.pop(r)
        # Sniper
        if len(self.players) > 8:
            self.sniper_shots = mafia_number - 2
            r = random.randrange(0, len(self.just_players))
            self.just_players[r].role = Roles.Sniper
            self.just_players[r].emoji = "🕸‍"
            self.citizens.append(self.just_players[r])
            self.just_players[r].send_role(self.context)
            language = self.group_data["lang"]
            message = ""
            with codecs.open(os.path.join("Lang", language, "SniperNumOfShots"), 'r', encoding='utf8') as file:
                message += file.read() + f"*{self.sniper_shots}*" + "  \n"
            with codecs.open(os.path.join("Lang", language, "SniperBeCareful"), 'r', encoding='utf8') as file:
                message += file.read()
            self.context.bot.send_message(
                chat_id=self.just_players[r].user_id, text=message, parse_mode="Markdown")
            self.just_players.pop(r)
        # Citizens
        for player in self.just_players:
            player.role = Roles.Citizen
            self.citizens.append(player)
            player.emoji = "👨‍💼"
            player.send_role(self.context)
        self.just_players.clear()

    def notify_mafias(self):
        language = self.group_data["lang"]
        for mafia in self.mafias:
            text = ""
            with codecs.open(os.path.join("Lang", language, "OtherMafias"), 'r', encoding='utf8') as file:
                text = file.read() + "\n "
            for teammate in self.mafias:
                if mafia.user_id != teammate.user_id:
                    if teammate.role == Roles.GodFather:
                        text += teammate.get_markdown_call() + " is GodFather" + "  \n"
                    else:
                        text += teammate.get_markdown_call() + " is Mafia" + "  \n"
            self.context.bot.send_message(
                chat_id=mafia.user_id, text=text, parse_mode="Markdown")

    def send_day_votes(self, players_list):
        for player in players_list:
            language = self.group_data["lang"]
            poll = None
            text = ""
            if language == 'en':
                poll = Poll("Vote to kill: " + player.get_markdown_call() + "  \nVoters:" + "🙋‍♂️", ["YES", "NO"],
                            self.group_chat_id, "day")
                text = f"Voting results to kill: {player.get_markdown_call()}:  \n\nYes: "
            else:
                poll = Poll("رای برای کشتن: " + player.get_markdown_call() + "  \n" + "🙋‍♂️" + "رای دهندگان:",
                            ["آره", "نه"],
                            self.group_chat_id, "day")
                text = f"نتیجه ی رای گیری برای کشتن {player.get_markdown_call()}:  \n\nآره: "
            self.edit_vote = True
            poll_message = poll.send_poll(self.context)
            with codecs.open(os.path.join("Lang", language, "VoteTime"), 'r', encoding='utf8') as file:
                time_message = self.context.bot.send_message(
                    chat_id=self.group_chat_id, text=file.read())
            time.sleep(13)
            self.edit_vote = False
            time.sleep(2)
            for user_id, status in self.voters.items():
                if status == "YES":
                    self.day_votes[player.user_id].append(user_id)
                    p = self.get_player_by_id(user_id)
                    text += "  \n" + p.get_markdown_call()
            if language == 'en':
                text += "  \n\nNo:"
            else:
                text += " \n\nنه:"
            for user_id, status in self.voters.items():
                if status == "NO":
                    p = self.get_player_by_id(user_id)
                    text += "  \n" + p.get_markdown_call()
            poll_message.edit_text(text=text, parse_mode="Markdown")
            time_message.delete()
            self.voters = {}

    def situation_vote(self):
        language = self.group_data["lang"]
        poll = None
        text = ""
        with codecs.open(os.path.join("Lang", language, "LeftAnnounce"), 'r', encoding='utf8') as file:
            text = file.read()
            text = text.replace('*', str(self.situation_announce), 1)
            self.context.bot.send_message(
                chat_id=self.group_chat_id, text=text)

        if language == 'en':
            poll = Poll("Vote to announce situation: " + "  \nVoters:" + "🙋‍♂️", ["YES", "NO"],
                        self.group_chat_id, "day")
            text = "Voting results to announce: \n\nYes: "
        else:
            poll = Poll("رای برای اعلام وضعیت: " + "  \n" + "🙋‍♂️" + "رای دهندگان:",
                        ["آره", "نه"],
                        self.group_chat_id, "day")
            text = "نتیجه ی رای گیری برای اعلام وضعیت :  \n\nآره: "
        poll_message = poll.send_poll(self.context)
        with codecs.open(os.path.join("Lang", language, "VoteTime"), 'r', encoding='utf8') as file:
            time_message = self.context.bot.send_message(
                chat_id=self.group_chat_id, text=file.read())
        time.sleep(15)
        for user_id, status in self.voters.items():
            if status == "YES":
                self.situation_announce_votes.append(user_id)
                p = self.get_player_by_id(user_id)
                text += "  \n" + p.get_markdown_call()
        if language == 'en':
            text += "  \n\nNo:"
        else:
            text += " \n\nنه:"
        for user_id, status in self.voters.items():
            if status == "NO":
                p = self.get_player_by_id(user_id)
                text += "  \n" + p.get_markdown_call()
        poll_message.edit_text(text=text, parse_mode="Markdown")
        time_message.delete()
        self.voters = {}

        if len(self.situation_announce_votes) > len(self.get_alive_players()) // 2:

            self.situation_announce = self.situation_announce - 1

            all_player = len(self.get_alive_players())
            city = len(self.get_citizens())
            mafia = all_player - city
            text = ""
            with codecs.open(os.path.join("Lang", language, "AnnounceSituation"), 'r', encoding='utf8') as file:
                text = file.read()
                text = text.replace('*', str(mafia), 1)
                text = text.replace('*', str(city), 1)
            self.context.bot.send_message(
                chat_id=self.group_chat_id, text=text)
            if self.situation_announce == 0:
                with codecs.open(os.path.join("Lang", language, "LastAnnounce"), 'r', encoding='utf8') as file:
                    self.context.bot.send_message(
                        chat_id=self.group_chat_id, text=file.read())
            else:
                with codecs.open(os.path.join("Lang", language, "LeftAnnounce"), 'r', encoding='utf8') as file:
                    text = file.read()
                    text = text.replace('*', str(self.situation_announce), 1)
                    self.context.bot.send_message(
                        chat_id=self.group_chat_id, text=text)

        else:
            with codecs.open(os.path.join("Lang", language, "AnnounceDidntAccept"), 'r', encoding='utf8') as file:
                self.context.bot.send_message(
                    chat_id=self.group_chat_id, text=file.read())

    def update_mafia_ranks(self, dead_mafia):
        language = self.group_data["lang"]
        for p in self.get_alive_players():
            if p.mafia_rank > dead_mafia.mafia_rank:
                p.mafia_rank = p.mafia_rank - 1
                with codecs.open(os.path.join("Lang", language, "MafiaRank"), 'r', encoding='utf8') as file:
                    self.context.bot.send_message(
                        chat_id=p.user_id, text=file.read() + str(p.mafia_rank))

    def send_day_list(self):
        message = "Players:\n"
        for player in self.get_alive_players():
            message = message + "🙂 " + player.get_markdown_call() + " \n"
        if len(self.players) > len(self.get_alive_players()):
            for player in self.players:
                if player not in self.get_alive_players():
                    message = message + "💀 " + player.get_markdown_call() + " \n"
        self.context.bot.send_message(chat_id=self.group_chat_id, text=message, parse_mode="MarkDown")

    def day(self):
        self.context.bot.send_sticker(chat_id=self.group_chat_id,
                                      sticker="CAACAgQAAxkBAAEBTvZfVoDnLCoHnmNokQ0xDu_r1L21JAACSwAD1ul3KzlRQvdVVv9-GwQ")
        language = self.group_data["lang"]
        if language == "en":
            self.context.bot.send_message(
                chat_id=self.group_chat_id, text="Day is started")
        else:
            self.context.bot.send_message(
                chat_id=self.group_chat_id, text="روز شروع شد!")

        self.state = GameState.Day

        self.send_day_list()

        # Situation announce
        if self.day_night_counter > 2 and self.situation_announce > 0:
            self.situation_vote()

        for player in self.get_alive_players():
            player.talk(self.group_chat_id, self.context)
            time.sleep(45)
        if self.day_night_counter != 0:
            self.send_day_votes(self.get_alive_players())
            kill_players = self.find_votes_more_than_half()
            message = ""
            if len(kill_players) != 0:
                with codecs.open(os.path.join("Lang", language, "DefendingPlayers"), 'r', encoding='utf8') as file:
                    message = file.read() + "  \n"
                for player in kill_players:
                    message += player.get_markdown_call() + "  \n"
            else:
                with codecs.open(os.path.join("Lang", language, "NoDefend"), 'r', encoding='utf8') as file:
                    message = file.read()
            self.context.bot.send_message(
                chat_id=self.group_chat_id, text=message, parse_mode="Markdown")
            self.reset_info()
            for player in kill_players:
                player.talk(self.group_chat_id, self.context)
                time.sleep(15)
            if len(kill_players) >= 1:
                self.send_day_votes(kill_players)
                final_kill = self.find_votes_more_than_half()
                if len(final_kill) == 0:
                    with codecs.open(os.path.join("Lang", language, "NobodyDeadHalf"), 'r', encoding='utf8') as file:
                        self.context.bot.send_message(
                            chat_id=self.group_chat_id, text=file.read())
                elif len(final_kill) == 1:
                    player = final_kill[0]
                    if player.shield:
                        player.shield = False
                        """Fix the message text"""
                        with codecs.open(os.path.join("Lang", language, "BulletproofAnounce"), 'r',
                                         encoding='utf8') as file:
                            self.context.bot.send_message(
                                chat_id=self.group_chat_id, text=f"{player.get_markdown_call()} {file.read()}",
                                parse_mode="Markdown")
                    else:
                        with codecs.open(os.path.join("Lang", language, "FinalWill"), 'r', encoding='utf8') as file:
                            self.context.bot.send_message(chat_id=self.group_chat_id, text=player.get_markdown_call(
                            ) + file.read(), parse_mode="Markdown")
                        if player.role == Roles.Mafia or player.role == Roles.GodFather:
                            self.update_mafia_ranks(player)
                        time.sleep(15)
                        player.is_alive = False
                else:
                    players = self.find_player_with_most_vote()
                    if len(players) == 1:
                        player = players[0]
                        if player.shield:
                            player.shield = False
                            """Fix the message text"""
                            with codecs.open(os.path.join("Lang", language, "BulletproofAnounce"), 'r',
                                             encoding='utf8') as file:
                                self.context.bot.send_message(
                                    chat_id=self.group_chat_id, text=f"{player.get_markdown_call()} {file.read()}",
                                    parse_mode="Markdown")
                        else:
                            with codecs.open(os.path.join("Lang", language, "FinalWill"), 'r', encoding='utf8') as file:
                                self.context.bot.send_message(chat_id=self.group_chat_id, text=player.get_markdown_call(
                                ) + file.read(), parse_mode="Markdown")
                            time.sleep(15)
                            player.is_alive = False
                            if player.role == Roles.Mafia or player.role == Roles.GodFather:
                                self.update_mafia_ranks(player)
                    else:
                        with codecs.open(os.path.join("Lang", language, "NobodyDiedSame"), 'r',
                                         encoding='utf8') as file:
                            self.context.bot.send_message(
                                chat_id=self.group_chat_id, text=file.read())
                        time.sleep(5)
            else:
                with codecs.open(os.path.join("Lang", language, "NobodyDeadHalf"), 'r', encoding='utf8') as file:
                    self.context.bot.send_message(
                        chat_id=self.group_chat_id, text=file.read())
                time.sleep(15)
            self.reset_info()

    def night_result(self):
        language = self.group_data["lang"]
        detective_player = self.get_player_by_role(Roles.Detective)
        doctor_player = self.get_player_by_role(Roles.Doctor)
        sniper_player = self.get_player_by_role(Roles.Sniper)
        mafia_kill = True
        sniper_kill = 0
        randomly_chosen = ""
        with codecs.open(os.path.join("Lang", language, "ChosenRandomly"), 'r', encoding='utf8') as file:
            randomly_chosen = file.read()
        if self.night_votes.get("Mafia_shot") is None:
            r = random.randrange(0, len(self.get_citizens()))
            self.night_votes.update(
                {"Mafia_shot": self.get_citizens()[r].user_id})
            self.messages.get("Mafia_shot").edit_text(
                text=f"{randomly_chosen} {self.get_citizens()[r].get_markdown_call()}", parse_mode="MarkDown")

        if self.night_votes.get("Doctor") is None and doctor_player is not None:
            r = random.randrange(0, len(self.get_alive_players()))
            self.night_votes.update(
                {"Doctor": self.get_alive_players()[r].user_id})
            self.messages.get("Doctor").edit_text(
                text=f"{randomly_chosen} {self.get_alive_players()[r].get_markdown_call()}", parse_mode="MarkDown")

        if self.night_votes.get("Sniper") is None and sniper_player is not None and self.messages.get(
                "Sniper") is not None:
            with codecs.open(os.path.join("Lang", language, "SniperDidntChoose"), 'r', encoding='utf8') as file:
                self.messages.get("Sniper").edit_text(text=file.read())

        if self.night_votes.get("Detective") is None and detective_player is not None:
            r = random.randrange(
                0, len(self.get_players_without_detect()))
            self.night_votes.update(
                {"Detective": self.get_players_without_detect()[r].user_id})
            self.messages.get("Detective").edit_text(
                text=f"{randomly_chosen} {self.get_players_without_detect()[r].get_markdown_call()}",
                parse_mode="MarkDown")

        if doctor_player is not None and str(self.night_votes.get("Mafia_shot")) == str(self.night_votes.get("Doctor")):
            mafia_kill = False

        if self.get_player_by_id(int(self.night_votes.get("Mafia_shot"))).shield:
            mafia_kill = False
            self.get_player_by_id(
                int(self.night_votes.get("Mafia_shot"))).shield = False

        if detective_player is not None:
            if self.get_player_by_id(int(self.night_votes.get("Detective"))).role == Roles.Mafia:
                with codecs.open(os.path.join("Lang", language, "DetectiveRight"), 'r', encoding='utf8') as file:
                    self.context.bot.send_message(
                        chat_id=detective_player.user_id, text=file.read())
            else:
                with codecs.open(os.path.join("Lang", language, "DetectiveWrong"), 'r', encoding='utf8') as file:
                    self.context.bot.send_message(
                        chat_id=detective_player.user_id, text=file.read())

        if self.night_votes.get("Sniper") is not None:
            if self.get_player_by_id(int(self.night_votes.get("Sniper"))).role == Roles.Mafia:
                sniper_kill = 1
                self.sniper_shots -= 1
            elif self.get_player_by_id(int(self.night_votes.get("Sniper"))).role != Roles.GodFather:
                sniper_kill = 2
                self.sniper_shots -= 1
        if sniper_player is not None and str(
                self.night_votes.get("Sniper")) == str(self.night_votes.get("Doctor")) and sniper_kill == 1:
            sniper_kill = 0

        kill_list = []
        if sniper_kill == 1:
            kill_list.append(self.get_player_by_id(
                int(self.night_votes.get("Sniper"))))
            self.update_mafia_ranks(self.get_player_by_id(
                int(self.night_votes.get("Sniper"))))

        elif sniper_kill == 2:
            kill_list.append(sniper_player)

        if mafia_kill:
            kill_list.append(self.get_player_by_id(
                int(self.night_votes.get("Mafia_shot"))))

        random.shuffle(kill_list)
        message = ""
        if len(kill_list) == 0:
            with codecs.open(os.path.join("Lang", language, "NoNightDead"), 'r', encoding='utf8') as file:
                message += file.read()
        else:
            with codecs.open(os.path.join("Lang", language, "NightDead"), 'r', encoding='utf8') as file:
                message += file.read() + "  \n"
        for player in kill_list:
            message += player.get_markdown_call() + "  \n"
            player.is_alive = False

        if sniper_kill == 1:
            with codecs.open(os.path.join("Lang", language, "SniperCongrats"), 'r', encoding='utf8') as file:
                message += file.read()
        self.context.bot.send_message(
            chat_id=self.group_chat_id, text=message, parse_mode="Markdown")

        self.night_votes = {"Mafia_shot": None,
                            "Detective": None, "Doctor": None, "Sniper": None}
        self.messages = {"Mafia_shot": None,
                         "Detective": None, "Doctor": None, "Sniper": None}

    def night(self):
        self.context.bot.send_sticker(chat_id=self.group_chat_id,
                                      sticker="CAACAgQAAxkBAAEBTvRfVoDkyT_4cuxWVkyG3sSE5YwMZwACTwAD1ul3K7fApYkW8UiOGwQ")
        language = self.group_data["lang"]
        self.state = GameState.Night
        if self.day_night_counter == 1 and len(self.mafias) > 1:
            with codecs.open(os.path.join("Lang", language, "FirstNightDesc"), 'r', encoding='utf8') as file:
                self.context.bot.send_message(
                    chat_id=self.group_chat_id, text=file.read())
            self.notify_mafias()
            for i in range(2):
                if self.is_finished:
                    break
                with codecs.open(os.path.join("Lang", language, f"Night{30 - i * 15}sec"), 'r',
                                 encoding='utf8') as file:
                    self.context.bot.send_message(
                        chat_id=self.group_chat_id, text=file.read())
                time.sleep(15)

        else:
            with codecs.open(os.path.join("Lang", language, "NightStart"), 'r', encoding='utf8') as file:
                self.context.bot.send_message(
                    chat_id=self.group_chat_id, text=file.read())
            for player in self.get_alive_players():
                if player.mafia_rank == 1:
                    with codecs.open(os.path.join("Lang", language, "MafiaVoteNight"), 'r', encoding='utf8') as file:
                        poll = Poll(file.read() + player.emoji,
                                    self.get_citizens(), player.user_id, "night")
                        self.messages.update(
                            {"Mafia_shot": poll.send_poll(self.context)})
                elif player.role == Roles.Sniper:
                    if self.sniper_shots > 0:
                        with codecs.open(os.path.join("Lang", language, "SniperVoteNight"), 'r',
                                         encoding='utf8') as file:
                            poll = Poll(file.read(
                            ) + player.emoji, self.get_players_without_sniper(), player.user_id, "night")
                            self.messages.update(
                                {"Sniper": poll.send_poll(self.context)})
                    else:
                        with codecs.open(os.path.join("Lang", language, "SniperEnd"), 'r', encoding='utf8') as file:
                            self.context.bot.send_message(
                                chat_id=player.user_id, text=file.read())
                elif player.role == Roles.Detective:
                    with codecs.open(os.path.join("Lang", language, "DetectiveVoteNight"), 'r',
                                     encoding='utf8') as file:
                        poll = Poll(file.read(
                        ) + player.emoji, self.get_players_without_detect(), player.user_id, "night")
                        self.messages.update(
                            {"Detective": poll.send_poll(self.context)})
                elif player.role == Roles.Doctor:
                    with codecs.open(os.path.join("Lang", language, "DoctorVoteNight"), 'r', encoding='utf8') as file:
                        poll = Poll(file.read() + player.emoji,
                                    self.get_alive_players(), player.user_id, "night")
                        self.messages.update(
                            {"Doctor": poll.send_poll(self.context)})
            for i in range(4):
                with codecs.open(os.path.join("Lang", language, f"Night{60 - i * 15}sec"), 'r',
                                 encoding='utf8') as file:
                    self.context.bot.send_message(
                        chat_id=self.group_chat_id, text=file.read())
                time.sleep(15)

            self.night_result()

    def print_roles(self):
        language = self.group_data["lang"]
        text = ""
        for player in self.players:
            if player.mafia_rank == 0:
                text += "🙂"
            else:
                text += "😈"
            with codecs.open(os.path.join("Lang", language, f"{player.role.name}Name"), 'r', encoding='utf8') as file:
                text += player.get_markdown_call() + " " + file.read() + player.emoji + "\n"
        self.context.bot.send_message(
            chat_id=self.group_chat_id, text=text, parse_mode="Markdown")

    def update_players_dict(self, result):
        for player in self.players:
            data = player.user_data
            data["total_games"] += 1
            if (player.role == Roles.Mafia or player.role == Roles.GodFather) and (result == "mafia"):
                data["mafia_win"] += 1
            elif (player.role == Roles.Mafia or player.role == Roles.GodFather) and (result == "city"):
                data["mafia_lose"] += 1
            elif (player.role != Roles.Mafia and player.role != Roles.GodFather) and (result == "mafia"):
                data["city_lose"] += 1
            else:
                data["city_win"] += 1
            if data['mafia_win'] + data["mafia_lose"] != 0:
                data['mafia_win_percent'] = data['mafia_win'] / \
                                            (data['mafia_win'] + data["mafia_lose"]) * 100
            if data['city_win'] + data["city_lose"] != 0:
                data['city_win_percent'] = data['city_win'] / \
                                           (data['city_win'] + data["city_lose"]) * 100
            data["win_percent"] = (data['mafia_win'] +
                                   data['city_win']) / data["total_games"] * 100

    def update_group_dict(self, result):
        data = self.group_data
        data["total_games"] += 1
        if result == "mafia":
            data["mafia"] += 1
        else:
            data["city"] += 1
        data['mafia_percent'] = data["mafia"] / data["total_games"] * 100
        data['city_percent'] = data["city"] / data["total_games"] * 100

    def result_game(self):
        mafias = 0
        citizens = 0
        for player in self.get_alive_players():
            if player.role == Roles.GodFather or player.role == Roles.Mafia:
                mafias += 1
            else:
                citizens += 1

        if mafias >= citizens:
            language = self.group_data["lang"]
            if not self.print_result:
                self.print_result = True
                self.context.bot.send_sticker(chat_id=self.group_chat_id,
                                              sticker="CAACAgQAAxkBAAEBEGpfEajpXdMaTTseiJvWttCJFXbtwwACGQAD1ul3K3z"
                                                      "-LuYH7F5fGgQ")
                with codecs.open(os.path.join("Lang", language, "MafiaWon"), 'r', encoding='utf8') as file:
                    self.context.bot.send_message(
                        chat_id=self.group_chat_id, text=file.read())
                self.print_roles()
            self.update_group_dict("mafia")
            self.update_players_dict("mafia")
            Database.do(Mode.players_stats, self.players, "mafia")
            Database.do(Mode.group_stats, self.group_chat_id, "mafia")
            # Database.update_players_stats(player_list=self.players, result="mafia")
            return False
        elif mafias == 0:
            language = self.group_data["lang"]
            if not self.print_result:
                self.print_result = True
                self.context.bot.send_sticker(chat_id=self.group_chat_id,
                                              sticker="CAACAgQAAxkBAAEBEGhfEajlbVPbMEesXXrgq4wOe"
                                                      "-5eBAACGAAD1ul3K4WFHtFPPfm2GgQ")

                with codecs.open(os.path.join("Lang", language, "CityWon"), 'r', encoding='utf8') as file:
                    self.context.bot.send_message(
                        chat_id=self.group_chat_id, text=file.read())
                self.print_roles()
            self.update_players_dict("city")
            self.update_group_dict("city")
            Database.do(Mode.players_stats, self.players, "city")
            Database.do(Mode.group_stats, self.group_chat_id, "city")
            # Database.update_players_stats(player_list=self.players, result="city")
            return False
        return True

    def turn(self):
        if self.day_night_counter % 2 != 0:
            self.night()
        else:
            self.day()
        self.day_night_counter += 1
