import telegram
import random
from Player import Player, Roles
from telegram.ext import Updater
from telegram.ext.dispatcher import run_async
from Poll import Poll
import time
import enum
import threading
import ctypes
import traceback


class GameState(enum.Enum):
    Day = 0
    Night = 1


class Game(threading.Thread):

    def __init__(self, group_chat_id, group_data, context):
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
        self.state = GameState.Day
        self.print_result = False
        self.context = context
        self.messages = {"Mafia_shot": None,
                         "Detective": None, "Doctor": None, "Sniper": None}

    def run(self):
        try:
            time.sleep(60)
            self.start_game(self.context)
        except Exception as e:
            traceback.print_exc(e)
        finally:
            print('ended')

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
            if len(value) >= (num_of_alive_players - 1) // 2:
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

    def get_citizens_name(self):
        city = []
        for player in self.get_alive_players():
            if player.role != Roles.Mafia and player.role != Roles.GodFather:
                city.append(player.name)
        return city

    def join_game(self, user: telegram.User, user_data: telegram.ext.CallbackContext.user_data,
                  update: telegram.Update, context: telegram.ext.CallbackContext):
        if "active_game" not in user_data.keys():
            user_data["active_game"] = self
            player = Player(user.full_name, user.username,
                            user.id, user_data, self)
            self.players.append(player)
            self.just_players.append(player)
            update.message.reply_markdown(
                "Current players:\n" + self.get_list())

            context.bot.send_message(
                chat_id=user['id'], text="You joined the game successfully")
        else:
            if user_data["active_game"] == self:
                update.message.reply_markdown(
                    "You have already joined the game!")
                context.bot.send_message(
                    chat_id=user['id'], text="You have already joined the game")
            else:
                update.message.reply_markdown(
                    "You have already joined a game in another group!")
                context.bot.send_message(
                    chat_id=user['id'], text="You have already joined a game in another group")

    def leave_game(self, user: telegram.User, user_data: telegram.ext.CallbackContext.user_data,
                   update: telegram.Update):
        if "active_game" in user_data.keys():
            if user_data["active_game"] == self:
                del user_data["active_game"]
                player = self.get_player_by_id(user.id)
                # del self.votes[player.user_name]
                self.players.remove(player)
                self.just_players.remove(player)
                update.message.reply_text("You left the game successfully!")
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

    def get_players_name_without_detect(self):
        without_detect = []
        for player in self.get_alive_players():
            if player.role != Roles.Detective:
                without_detect.append(player.name)
        return without_detect

    def get_players_name_without_sniper(self):
        without_sniper = []
        for player in self.get_alive_players():
            if player.role != Roles.Detective:
                without_sniper.append(player.name)
        return without_sniper

    def start_game(self, context: telegram.ext.CallbackContext):
        self.is_started = True
        group_data = self.group_data
        if "active_game" in group_data.keys():
            game = group_data["active_game"]
            if len(game.players) > 2:
                game.set_players_roles(context)
                context.bot.send_message(
                    chat_id=self.group_chat_id, text='Game has been started!')
                self.is_started = True
                self.reset_info()
                while self.result_game(context):
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
        for player in self.players:
            del player.user_data["active_game"]
        del self.group_data["active_game"]
        self.raise_exception()

    def set_players_roles(self, context: telegram.ext.CallbackContext):
        mafia_number = 0
        # GodFather
        if len(self.players) >= 6:
            r = random.randrange(0, len(self.just_players))
            self.just_players[r].role = Roles.GodFather
            self.mafias.append(self.just_players[r])
            self.just_players[r].emoji = "🧛"
            mafia_number = mafia_number + 1
            self.just_players[r].mafia_rank = mafia_number
            self.just_players[r].send_role(context)
            self.just_players.pop(r)
        # Other Mafias
        for i in range(int(len(self.players) / 3) - mafia_number):
            r = random.randrange(0, len(self.just_players))
            self.just_players[r].role = Roles.Mafia
            self.just_players[r].emoji = "🧛"
            self.mafias.append(self.just_players[r])
            mafia_number = mafia_number + 1
            self.just_players[r].mafia_rank = mafia_number
            self.just_players[r].send_role(context)
            self.just_players.pop(r)
        # Doctor
        r = random.randrange(0, len(self.just_players))
        self.just_players[r].role = Roles.Doctor
        self.just_players[r].emoji = "👨‍⚕️‍"
        self.citizens.append(self.just_players[r])
        self.just_players[r].send_role(context)
        self.just_players.pop(r)
        # Detective
        r = random.randrange(0, len(self.just_players))
        self.just_players[r].role = Roles.Detective
        self.just_players[r].emoji = "👮‍"
        self.citizens.append(self.just_players[r])
        self.just_players[r].send_role(context)
        self.just_players.pop(r)
        # Sniper
        if len(self.players) > 6:
            r = random.randrange(0, len(self.just_players))
            self.just_players[r].role = Roles.Sniper
            self.just_players[r].emoji = "🕸‍"
            self.citizens.append(self.just_players[r])
            self.just_players[r].send_role(context)
            self.just_players.pop(r)
        # Citizens
        for player in self.just_players:
            player.role = Roles.Citizen
            self.citizens.append(player)
            player.emoji = "👨‍💼"
            player.send_role(context)
        self.just_players.clear()
        if len(self.mafias) > 1:
            self.notify_mafias(context)

    def notify_mafias(self, context: telegram.ext.CallbackContext):
        for mafia in self.mafias:
            if len(self.mafias) == 2:
                text = "Your teammate is:\n"
            else:
                text = "Your teammates are:\n"
            for teammate in self.mafias:
                if mafia.user_id != teammate.user_id:
                    text += teammate.get_markdown_call()
            context.bot.send_message(
                chat_id=mafia.user_id, text=text, parse_mode="Markdown")

    def day(self, context: telegram.ext.CallbackContext):
        self.state = GameState.Day
        for player in self.get_alive_players():
            player.talk(self.group_chat_id, context)
            time.sleep(5)
        for player in self.get_alive_players():
            poll = Poll("Do you want to kill " + player.get_markdown_call() + "?  \nVoters:" + "🙋‍♂️", ["YES", "NO"],
                        self.group_chat_id)
            poll_message = poll.send_poll(context)
            time_message = context.bot.send_message(
                chat_id=self.group_chat_id, text="15 seconds left until the end of voting")
            time.sleep(15)
            text = f"Votes for {player.get_markdown_call()}:  \n\nYes: "
            for user_id, status in self.voters.items():
                if status == "YES":
                    self.day_votes[player.user_id].append(user_id)
                    p = self.get_player_by_id(user_id)
                    text += " " + p.get_markdown_call()
            text += "  \n\nNo:"
            for user_id, status in self.voters.items():
                if status == "NO":
                    p = self.get_player_by_id(user_id)
                    text += " " + p.get_markdown_call()
            poll_message.edit_text(text=text, parse_mode="Markdown")
            time_message.delete()
            print(self.day_votes, end="\n\n")
            print(self.voters)
            self.voters = {}

        kill_players = self.find_votes_more_than_half()
        print(f"{len(kill_players)} players defend themselves")
        self.reset_info()
        if len(kill_players) >= 1:
            for player in kill_players:
                player.talk(self.group_chat_id, context)
                time.sleep(5)
            for player in kill_players:
                poll = Poll("Do you want to kill " + player.get_markdown_call() + "?  \nVoters:" + "🙋‍♂️",
                            ["YES", "NO"],
                            self.group_chat_id)
                poll_message = poll.send_poll(context)
                time_message = context.bot.send_message(
                    chat_id=self.group_chat_id, text="15 seconds left until the end of voting")
                time.sleep(15)
                text = f"Votes for {player.get_markdown_call()}:  \n\nYes: "
                for user_id, status in self.voters.items():
                    if status == "YES":
                        self.day_votes[player.user_id].append(user_id)
                        p = self.get_player_by_id(user_id)
                        text += " " + p.get_markdown_call()
                text += "  \n\nNo:"
                for user_id, status in self.voters.items():
                    if status == "NO":
                        p = self.get_player_by_id(user_id)
                        text += " " + p.get_markdown_call()
                poll_message.edit_text(text=text, parse_mode="Markdown")
                time_message.delete()
                self.voters = {}
            print(self.day_votes, end="\n\n")
            final_kill = self.find_votes_more_than_half()
            print(f"{len(final_kill)} with more than half")
            if len(final_kill) == 0:
                context.bot.send_message(
                    chat_id=self.group_chat_id, text="Nobody died today.there is no player with more than half votes!!")
            elif len(final_kill) == 1:
                player = final_kill[0]
                context.bot.send_message(
                    chat_id=self.group_chat_id,
                    text=player.get_markdown_call() + "☠ died. Everybody listen to his final will",
                    parse_mode="Markdown")
                if player.role == Roles.Mafia or player.role == Roles.GodFather:
                    for p in self.get_alive_players():
                        if p.mafia_rank > player.mafia_rank:
                            p.mafia_rank = p.mafia_rank - 1
                            context.bot.send_message(chat_id=p.user_id,
                                                     text="Your new Mafia Rank : " + str(p.mafia_rank))
                time.sleep(5)
                player.is_alive = False
            else:
                players = self.find_player_with_most_vote()
                if len(players) == 1:
                    player = players[0]
                    context.bot.send_message(chat_id=self.group_chat_id, text=player.get_markdown_call(
                    ) + "☠️ died. Everybody listen to his final will", parse_mode="Markdown")
                    time.sleep(5)
                    player.is_alive = False
                    if player.role == Roles.Mafia or player.role == Roles.GodFather:
                        for p in self.get_alive_players():
                            if p.mafia_rank > player.mafia_rank:
                                p.mafia_rank = p.mafia_rank - 1
                                context.bot.send_message(chat_id=p.user_id,
                                                         text="Your new Mafia Rank : " + str(p.mafia_rank))
                else:
                    context.bot.send_message(
                        chat_id=self.group_chat_id,
                        text="Nobody died today because of players with same number of votes!!")
                    time.sleep(5)
        else:
            context.bot.send_message(
                chat_id=self.group_chat_id, text="Nobody died today.there is no player with more than half votes!!")
        self.reset_info()

    def night_result(self, context: telegram.ext.CallbackContext):
        mafia_kill = True
        sniper_kill = 0
        detective_guess = False

        if self.night_votes.get("Mafia_shot") is None:
            r = random.randrange(0, len(self.get_citizens()))
            self.night_votes.update(
                {"Mafia_shot": self.get_citizens()[r].name})
            self.messages.get("Mafia_shot").edit_text(
                text="Bot choose randomly " + self.get_citizens()[r].get_markdown_call(), parse_mode="MarkDown")

        if self.night_votes.get("Doctor") is None:
            r = random.randrange(0, len(self.get_alive_players()))
            self.night_votes.update(
                {"Doctor": self.get_alive_players()[r].name})
            self.messages.get("Doctor").edit_text(
                text="Bot choose randomly " + self.get_alive_players()[r].get_markdown_call(), parse_mode="MarkDown")

        # if self.night_votes.get("Sniper") is None:
        #     self.messages.get("Sniper").edit_text(
        #         text="You didnt choose anyone to snipe him")
        if self.night_votes.get("Detective") is None:
            r = random.randrange(
                0, len(self.get_players_name_without_detect()))
            self.night_votes.update(
                {"Detective": self.get_players_name_without_detect()[r].name})
            self.messages.get("Doctor").edit_text(
                text="Bot choose randomly " + self.get_players_name_without_detect()[r].get_markdown_call(), parse_mode="MarkDown")

        if self.night_votes.get("Mafia_shot") is not None and self.night_votes.get(
                "Doctor") is not None and self.night_votes.get("Mafia_shot") == self.night_votes.get("Doctor"):
            mafia_kill = False
        if self.get_player_by_name(self.night_votes.get("Detective")) is not None and self.get_player_by_name(
                self.night_votes.get("Detective")).role == Roles.Mafia:
            detective_guess = True

        if self.get_player_by_name(self.night_votes.get("Sniper")) is not None and (self.get_player_by_name(
            self.night_votes.get("Sniper")).role == Roles.Mafia or self.get_player_by_name(
                self.night_votes.get("Sniper")).role == Roles.GodFather):
            sniper_kill = 1
        elif self.get_player_by_name(self.night_votes.get("Sniper")) is not None:
            sniper_kill = 2

        if mafia_kill and self.night_votes.get("Mafia_shot") is not None:
            context.bot.send_message(
                chat_id=self.group_chat_id, text=self.night_votes.get("Mafia_shot") + "☠️ died last night!!")
            self.get_player_by_name(self.night_votes.get(
                "Mafia_shot")).is_alive = False
        else:
            context.bot.send_message(
                chat_id=self.group_chat_id, text="Nobody died last night!!")

        if sniper_kill == 1 and self.night_votes.get("Sniper") is not None:
            context.bot.send_message(
                chat_id=self.group_chat_id, text=self.night_votes.get("Sniper") + "☠️ died last night!!")
            self.get_player_by_name(
                self.night_votes.get("Sniper")).is_alive = False
            for p in self.get_alive_players():
                if p.mafia_rank > self.get_player_by_name(
                        self.night_votes.get("Sniper")).mafia_rank:
                    p.mafia_rank = p.mafia_rank - 1
                    context.bot.send_message(
                        chat_id=p.user_id, text="Your new Mafia Rank : " + str(p.mafia_rank))
        elif sniper_kill == 2:
            for player in self.get_alive_players():
                if player.role == Roles.Sniper:
                    context.bot.send_message(
                        chat_id=self.group_chat_id, text=player.name + "☠️ died last night!!")
                    player.is_alive = False

        for player in self.get_alive_players():
            if player.role == Roles.Detective:
                if detective_guess:
                    context.bot.send_message(
                        chat_id=player.user_id, text="You guessed right!")
                else:
                    context.bot.send_message(
                        chat_id=player.user_id, text="You guessed wrong!")

    def night(self, context: telegram.ext.CallbackContext):
        self.state = GameState.Night
        context.bot.send_message(
            chat_id=self.group_chat_id, text="30 seconds left from night")
        for player in self.get_alive_players():
            if player.mafia_rank == 1:
                poll = Poll("Who do you want to kill?" + player.emoji,
                            self.get_citizens_name(), player.user_id)
                self.messages.update({"Mafia_shot": poll.send_poll(context)})
            elif player.role == Roles.Sniper:
                poll = Poll("Who do you want to snipe?" + player.emoji,
                            self.get_alive_players_name(), player.user_id)
                self.messages.update({"Sniper": poll.send_poll(context)})
            elif player.role == Roles.Detective:
                poll = Poll("Who do you want to doubt?" + player.emoji,
                            self.get_alive_players_name(), player.user_id)
                self.messages.update({"Detective": poll.send_poll(context)})
            elif player.role == Roles.Doctor:
                poll = Poll("Who do you want to save‍?" + player.emoji,
                            self.get_alive_players_name(), player.user_id)
                self.messages.update({"Doctor": poll.send_poll(context)})
        print(self.messages)
        time.sleep(30)
        self.night_result(context)

    def print_roles(self, context: telegram.ext.CallbackContext):
        text = ""
        for player in self.players:
            if player.mafia_rank == 0:
                text = text + "🙂 " + player.get_markdown_call() + " " + player.role.name + \
                    player.emoji + "\n"
            else:
                text = text + "😈 " + player.get_markdown_call() + " " + player.role.name + \
                    player.emoji + "\n"
        context.bot.send_message(
            chat_id=self.group_chat_id, text=text, parse_mode="Markdown")

    def result_game(self, context: telegram.ext.CallbackContext):
        mafias = 0
        citizens = 0
        for player in self.get_alive_players():
            if player.role == Roles.GodFather or player.role == Roles.Mafia:
                mafias += 1
            else:
                citizens += 1

        if mafias >= citizens:
            if not self.print_result:
                self.print_result = True
                context.bot.send_sticker(chat_id=self.group_chat_id,
                                         sticker="CAACAgQAAxkBAAEBEGpfEajpXdMaTTseiJvWttCJFXbtwwACGQAD1ul3K3z"
                                                 "-LuYH7F5fGgQ")
                context.bot.send_message(
                    chat_id=self.group_chat_id, text="Mafia win!")
                self.print_roles(context)
            return False
        elif mafias == 0:
            if not self.print_result:
                self.print_result = True
                context.bot.send_sticker(chat_id=self.group_chat_id,
                                         sticker="CAACAgQAAxkBAAEBEGhfEajlbVPbMEesXXrgq4wOe"
                                                 "-5eBAACGAAD1ul3K4WFHtFPPfm2GgQ")
                context.bot.send_message(
                    chat_id=self.group_chat_id, text="City win!")
                self.print_roles(context)
            return False
        else:
            return True

    def turn(self, context: telegram.ext.CallbackContext):
        if self.result_game(context):
            self.night(context)
        if self.result_game(context):
            self.day(context)
