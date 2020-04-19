import telegram
from Player import Player

class Game:

    def __init__(self,group_chat_id):
        self.players = []
        self.group_chat_id=group_chat_id

    def join_game(self, user_info: telegram.User, update: telegram.Update):
        print(1)
        is_in_the_game = False
        for player in self.players:
            if player.user_name == user_info['username']:
                is_in_the_game = True
        print(2)
        if not is_in_the_game:
            player = Player(user_info['first_name'], user_info['username'])
            print(3)
            self.players.append(player)
            players_list = ""
            print(4)
            for player in self.players:
                players_list += '@' + player.user_name + '\n'
            print(5)
            update.message.reply_text(players_list)

        else:
            update.message.reply_text('@' + user_info['username'] + " has already joined the game")


    def leave_game(self, user_info: telegram.User, update: telegram.Update):
        is_in_the_game = False
        for player in self.players:
            if player.user_name == user_info['username']:
                self.players.remove(player)
                is_in_the_game = True
                update.message.reply_text('@' + player.user_name + " successfully left the game")
        if not is_in_the_game:
            update.message.reply_text("You have not joined the game")
