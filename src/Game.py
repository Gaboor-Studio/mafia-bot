import telegram
import random
from Player import Player, Roles
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
        self.voters = []
        '''example: ["salinaria" , "mohokaja"}'''
        self.day_votes = {}
        '''example: {"amirparsa_sal":["salinaria","mohokaja"]} voters to amirparsa_sal'''
        self.mafias = []
        self.citizens = []
        self.players = []
        self.just_players = []
        self.group_chat_id = group_chat_id
        self.group_data = group_data
        self.is_started = False
        self.state = GameState.Day

    def reset_info(self):
        self.night_votes = {"Mafia_shot": None,
                            "Detective": None, "Doctor": None, "Sniper": None}
        self.voters = []
        self.day_votes = {}
        for player in self.get_alive_players():
            self.day_votes[player.user_name] = []

    def find_votes_more_than_half(self):
        players = []
        num_of_alive_players = len(self.get_alive_players())
        for key, value in self.day_votes.items():
            if len(value) >= (num_of_alive_players - 1) // 2:
                players.append(self.get_player_by_username(key))
        return players

    def find_player_with_most_vote(self):
        player = None
        max_votes = 0
        for key, value in self.day_votes.items():
            if len(value) >= max_votes:
                player = self.get_player_by_username(key)
                max_votes = len(value)
        return player

    def get_list(self):
        list_join = ""
        for player in self.players:
            list_join += player.get_markdown_call() + "\n"

        return list_join

    def join_game(self, user: telegram.User, user_data: telegram.ext.CallbackContext.user_data,
                  update: telegram.Update, context: telegram.ext.CallbackContext):
        if "active_game" not in user_data.keys():
            user_data["active_game"] = self
            player = Player(user.full_name, user.username,
                            user.id, user_data, self)
            self.players.append(player)
            self.just_players.append(player)
            update.message.reply_markdown(self.get_list())

            context.bot.send_message(
                chat_id=user['id'], text="You joined the game successfully")
        else:
            if user_data["active_game"] == self:
                update.message.reply_markdown(
                    f"[{user.full_name}](tg://user?id={user.id}) has already joined the game!", parse_mode="MarkdownV2")
                context.bot.send_message(
                    chat_id=user['id'], text="You have already joined the game")
            else:
                update.message.reply_markdown(
                    f"[{user.full_name}](tg://user?id={user.id}) has already joined a game in another group!",
                    parse_mode="MarkdownV2")
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
                update.message.reply_text(
                    player.get_markdown_call() + " successfully left the game!", parse_mode="MarkdownV2")
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

    def start_game(self, context: telegram.ext.CallbackContext):
        group_data = self.group_data
        if "active_game" in group_data.keys():
            game = group_data["active_game"]
            if len(game.players) > 2:
                game.set_players_roles(context)
                context.bot.send_message(
                    chat_id=self.group_chat_id, text='Game has been started!')
                self.is_started = True
                self.reset_info()
                self.day(context)
                self.night(context)
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

    def set_players_roles(self, context: telegram.ext.CallbackContext):
        mafia_number = 0
        # GodFather
        if len(self.players) >= 6:
            r = random.randrange(0, len(self.just_players))
            self.just_players[r].role = Roles.GodFather
            self.mafias.append(self.just_players[r])
            self.just_players.pop(r)
            mafia_number = mafia_number + 1
            self.just_players[r].mafia_rank = mafia_number
            self.just_players[r].send_role(context)
        # Other Mafias
        for i in range(int(len(self.players) / 3) - mafia_number):
            r = random.randrange(0, len(self.just_players))
            self.just_players[r].role = Roles.Mafia
            self.mafias.append(self.just_players[r])
            mafia_number = mafia_number + 1
            self.just_players[r].mafia_rank = mafia_number
            self.just_players[r].send_role(context)
            self.just_players.pop(r)
        # Doctor
        r = random.randrange(0, len(self.just_players))
        self.just_players[r].role = Roles.Doctor
        self.citizens.append(self.just_players[r])
        self.just_players[r].send_role(context)
        self.just_players.pop(r)
        # Detective
        r = random.randrange(0, len(self.just_players))
        self.just_players[r].role = Roles.Detective
        self.citizens.append(self.just_players[r])
        self.just_players[r].send_role(context)
        self.just_players.pop(r)
        # Sniper
        if len(self.players) > 6:
            r = random.randrange(0, len(self.just_players))
            self.just_players[r].role = Roles.Sniper
            self.citizens.append(self.just_players[r])
            self.just_players[r].send_role(context)
            self.just_players.pop(r)
        # Citizens
        for player in self.just_players:
            player.role = Roles.Citizen
            self.citizens.append(player)
            player.send_role(context)
            self.just_players.remove(player)

    def day(self, context: telegram.ext.CallbackContext):
        self.state = GameState.Day
        for player in self.get_alive_players():
            player.talk(self.group_chat_id, context)
            time.sleep(5)
        for player in self.get_alive_players():
            context.bot.send_message(chat_id=self.group_chat_id,
                                     text="Do you want to kill " + player.get_markdown_call() + " ?",
                                     parse_mode="MarkdownV2")
            poll = Poll("Nobody voted yet!", ["YES", "NO"],
                        self.group_chat_id)
            poll.send_poll(context)
            context.bot.send_message(
                chat_id=self.group_chat_id, text="15 seconds left until the end of voting")
            time.sleep(15)
            self.day_votes[player.user_name] = self.voters.copy()
            self.voters = []

        kill_players = self.find_votes_more_than_half()
        self.reset_info()
        if len(kill_players) > 1:
            for player in kill_players:
                player.talk(self.group_chat_id, context)
                time.sleep(5)
            for player in kill_players:
                context.bot.send_message(chat_id=self.group_chat_id,
                                         text="Do you want to kill " + player.get_markdown_call() + " ?",
                                         parse_mode="MarkdownV2")
                poll = Poll("Nobody voted yet!", ["YES", "NO"],
                            self.group_chat_id)
                poll.send_poll(context)
                context.bot.send_message(
                    chat_id=self.group_chat_id, text="15 seconds left until the end of voting")
                time.sleep(15)
                self.day_votes[player.user_name] = self.voters.copy()
                self.voters = []
            final_kill = self.find_votes_more_than_half()
            if len(final_kill) == 0:
                context.bot.send_message(
                    chat_id=self.group_chat_id, text="Nobody died today!!")
            elif len(final_kill) == 1:
                player = final_kill[0]
                context.bot.send_message(
                    chat_id=self.group_chat_id,
                    text=player.get_markdown_call() + " died Everybody listen to his final will",
                    parse_mode="MarkdownV2")
                time.sleep(5)
            else:
                player = self.find_player_with_most_vote()
                context.bot.send_message(
                    chat_id=self.group_chat_id,
                    text=player.get_markdown_call() + " died Everybody listen to his final will",
                    parse_mode="MarkdownV2")
                time.sleep(5)
        else:
            context.bot.send_message(
                chat_id=self.group_chat_id, text="Nobody died today!!")
        self.reset_info()

    def night_result(self, context: telegram.ext.CallbackContext):
        mafia_kill = True
        sniper_kill = False
        detective_guess = False

        if self.night_votes.get("Mafia_shot") is not None and self.night_votes.get(
                "Doctor") is not None and self.night_votes.get("Mafia_shot") == self.night_votes.get("Doctor"):
            mafia_kill = False
        if self.get_player_by_name(self.night_votes.get("Detective")) is not None and self.get_player_by_name(
                self.night_votes.get("Detective")).role == Roles.Mafia:
            detective_guess = True
        if self.get_player_by_name(self.night_votes.get("Sniper")) is not None and (self.get_player_by_name(
                self.night_votes.get("Sniper")).role == Roles.Mafia or self.get_player_by_name(
            self.night_votes.get("Sniper")).role == Roles.GodFather):
            sniper_kill = True

        if mafia_kill and self.night_votes.get("Mafia_shot") is not None:
            context.bot.send_message(
                chat_id=self.group_chat_id, text=self.night_votes.get("Mafia_shot") + " died last night!!")
        else:
            context.bot.send_message(
                chat_id=self.group_chat_id, text="Nobody died last night!!")

        if sniper_kill and self.night_votes.get("Sniper") is not None:
            context.bot.send_message(
                chat_id=self.group_chat_id, text=self.night_votes.get("Sniper") + " died last night!!")
        else:
            for player in self.get_alive_players():
                if player.role == Roles.Sniper:
                    context.bot.send_message(chat_id=self.group_chat_id, text=player.name + "Nobody died last night!!")

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
                poll = Poll("Who do you want to kill😈?",
                            self.get_alive_players_name(), player.user_id)
                poll.send_poll(context)
            elif player.role == Roles.Sniper:
                poll = Poll("Who do you want to snipe😈?",
                            self.get_alive_players_name(), player.user_id)
                poll.send_poll(context)
            elif player.role == Roles.Detective:
                poll = Poll("Who do you want to doubt🕵️?",
                            self.get_alive_players_name(), player.user_id)
                poll.send_poll(context)
            elif player.role == Roles.Doctor:
                poll = Poll("Who do you want to save👨‍?",
                            self.get_alive_players_name(), player.user_id)
                poll.send_poll(context)
        time.sleep(30)
        self.night_result(context)

    def print_roles(self, context: telegram.ext.CallbackContext):
        text = ""
        for player in self.players:
            text = text + player.name + player.role.name + "\n"
        context.bot.send_message(
            chat_id=self.group_chat_id, text=text, parse_mode="MarkdownV2")

    def result_game(self, context: telegram.ext.CallbackContext):
        mafias = 0
        citizens = 0
        for player in self.get_alive_players():
            if player.role == Roles.GodFather or player.role == Roles.Mafia:
                mafias += 1
            else:
                citizens += 1

        if mafias >= citizens:
            context.bot.send_sticker(chat_id=self.group_chat_id,
                                     sticker="CAACAgQAAxkBAAEBEGpfEajpXdMaTTseiJvWttCJFXbtwwACGQAD1ul3K3z-LuYH7F5fGgQ")
            context.bot.send_message(
                chat_id=self.group_chat_id, text="Mafia win!")
            self.print_roles(context)
            return False
        elif mafias == 0:
            context.bot.send_sticker(chat_id=self.group_chat_id,
                                     sticker="CAACAgQAAxkBAAEBEGhfEajlbVPbMEesXXrgq4wOe-5eBAACGAAD1ul3K4WFHtFPPfm2GgQ")
            context.bot.send_message(
                chat_id=self.group_chat_id, text="City win!")
            self.print_roles(context)
            return False
        else:
            return True
