import pandas as pd
from Player import Roles, Player
import threading
import enum


class Mode(enum.Enum):
    group_stats = 0
    group_language = 1
    get_group = 2
    players_stats = 3
    players_language = 4
    get_player = 5


class Database:
    lock = threading.Lock()

    @classmethod
    def do(cls, to_do, param1, param2=None):
        Database.lock.acquire()
        r = None
        if to_do == Mode.group_stats:
            r = Database.update_group_game_stats(param1, param2)
        elif to_do == Mode.group_language:
            r = Database.change_group_language(param1, param2)
        elif to_do == Mode.players_stats:
            r = Database.update_players_stats(param1, param2)
        elif to_do == Mode.players_language:
            r = Database.change_player_language(param1, param2)
        elif to_do == Mode.get_group:
            r = Database.get_group(param1)
        elif to_do == Mode.get_player:
            r = Database.get_player(param1)
        Database.lock.release()
        return r

    @classmethod
    def update_group_game_stats(cls, group_id, result):
        d = pd.read_csv("groups.csv")
        if group_id not in list(d['group']):
            if result == 'mafia':
                add = {'group': group_id, 'total_games': 1,
                       'mafia': 1, 'city': 0, 'lang': 'en', 'state': None}
            else:
                add = {'group': group_id, 'total_games': 1,
                       'mafia': 0, 'city': 1, 'lang': 'en', 'state': None}
            d = d.append(add, ignore_index=True)
        else:
            index = d[d['group'] == group_id].index[0]
            if result == 'mafia':
                d.loc[index, 'mafia'] += 1

            else:
                d.loc[index, 'city'] += 1

            d.loc[index, 'total_games'] += 1
        d.to_csv("groups.csv", index=False)

    @classmethod
    def change_group_language(cls, group_id, language):
        d = pd.read_csv("groups.csv")
        if group_id not in list(d['group']):
            add = {'group': group_id, 'total_games': 0,
                   'mafia': 0, 'city': 0, 'lang': language, 'state': None}
            d = d.append(add, ignore_index=True)
        else:
            index = d[d['group'] == group_id].index[0]
            d.loc[index, 'lang'] = language
        d.to_csv("groups.csv", index=False)

    '''
    Example

    update_players(database , list of players , result = Mafia or City )

    '''

    @classmethod
    def update_players_stats(cls, player_list, result):
        d = pd.read_csv("players.csv")
        ids = [player.user_id for player in player_list]
        roles = [player.role for player in player_list]
        for i in range(len(ids)):
            if ids[i] in list(d['player']):
                index = d[d['player'] == ids[i]].index[0]

                if (roles[i] == Roles.Mafia or roles[i] == Roles.GodFather) and (result == "mafia"):
                    d.loc[index, 'mafia_win'] += 1

                elif (roles[i] == Roles.Mafia or roles[i] == Roles.GodFather) and (result == "city"):
                    d.loc[index, 'mafia_lose'] += 1

                elif (roles[i] != Roles.Mafia and roles[i] != Roles.GodFather) and (result == "mafia"):
                    d.loc[index, 'city_lose'] += 1

                else:
                    d.loc[index, 'city_win'] += 1
                d.loc[index, 'total_games'] += 1

            else:

                if (roles[i] == Roles.Mafia or roles[i] == Roles.GodFather) and (result == "mafia"):
                    to_add = {'player': ids[i], 'total_games': 1, 'mafia_win': 1,
                              'mafia_lose': 0, 'city_win': 0, 'city_lose': 0, 'lang': 'en'}

                elif (roles[i] == Roles.Mafia or roles[i] == Roles.GodFather) and (result == "city"):
                    to_add = {'player': ids[i], 'total_games': 1, 'mafia_win': 0,
                              'mafia_lose': 1, 'city_win': 0, 'city_lose': 0, 'lang': 'en'}

                elif (roles[i] != Roles.Mafia and roles[i] != Roles.GodFather) and (result == "mafia"):
                    to_add = {'player': ids[i], 'total_games': 1, 'mafia_win': 0,
                              'mafia_lose': 0, 'city_win': 0, 'city_lose': 1, 'lang': 'en'}

                else:
                    to_add = {'player': ids[i], 'total_games': 1, 'mafia_win': 0,
                              'mafia_lose': 0, 'city_win': 1, 'city_lose': 0, 'lang': 'en'}
                d = d.append(to_add, ignore_index=True)
        d.to_csv("players.csv", index=False)

    @classmethod
    def change_player_language(cls, player_id, language):
        d = pd.read_csv("players.csv")
        if player_id in list(d['player']):
            index = d[d.player == player_id].index[0]
            d.loc[index, 'lang'] = language
        else:
            to_add = {'player': player_id, 'total_games': 0, 'mafia_win': 0,
                      'mafia_lose': 0, 'city_win': 0, 'city_lose': 0, 'lang': language}
            d = d.append(to_add, ignore_index=True)
        d.to_csv("players.csv", index=False)

    '''
    Example:

    update_group ( database , group_id , result = Mafia or City , language )

    '''

    @classmethod
    def get_group(cls, group_id):
        d = pd.read_csv("groups.csv")
        if d[d.group == group_id].reset_index().size == 0:
            return None
        gp = dict(d[d.group == group_id].reset_index().iloc[0])
        dic = {
            'group': gp['group'],
            'mafia': gp['mafia'],
            'city': gp['city'],
            'total_games': gp['total_games'],
            'lang': gp['lang']
        }
        if dic['total_games'] == 0:
            dic['mafia_percent'] = 0
            dic['city_percent'] = 0
        else:
            dic['mafia_percent'] = gp['mafia'] / gp['total_games'] * 100
            dic['city_percent'] = gp['city'] / gp['total_games'] * 100
        return dic

    @classmethod
    def get_player(cls, player_id):
        d = pd.read_csv("players.csv")
        if d[d.player == player_id].reset_index().size == 0:
            return None
        pl = dict(d[d.player == player_id].reset_index().iloc[0])
        dic = {
            'player': pl['player'],
            'mafia_win': pl['mafia_win'],
            'city_win': pl['city_win'],
            'mafia_lose': pl['mafia_lose'],
            'city_lose': pl['city_lose'],
            'total_games': pl['total_games'],
            'lang': pl['lang']
        }
        if pl['total_games'] == 0:
            dic["win_percent"] = 0
        else:
            dic["win_percent"] = (
                pl['mafia_win'] + pl['city_win']) / pl["total_games"] * 100
        if pl['mafia_win'] + pl["mafia_lose"] == 0:
            dic["mafia_win_percent"] = 0
        else:
            dic['mafia_win_percent'] = pl['mafia_win'] / \
                (pl['mafia_win'] + pl["mafia_lose"]) * 100
        if pl['city_win'] + pl["city_lose"] == 0:
            dic["city_win_percent"] = 0
        else:
            dic['city_win_percent'] = pl['city_win'] / \
                (pl['city_win'] + pl["city_lose"]) * 100
        return dic


g = pd.DataFrame({
    'group': [],
    'total_games': [],
    'mafia': [],
    'city': [],
    'lang': [],
})

p = pd.DataFrame({
    'player': [],
    'total_games': [],
    'mafia_win': [],
    'mafia_lose': [],
    'city_win': [],
    'city_lose': [],
    'lang': [],
})

if __name__ == "__main__":
    p.to_csv("players.csv", index=False)
    g.to_csv("groups.csv", index=False)

# p = pd.read_csv("players.csv")
# g = pd.read_csv("groups.csv")

# t1 = threading.Thread(
#     target=Database.do, args=(Mode.group_stats, 654321, 'mafia'))
# t2 = threading.Thread(
#     target=Database.do, args=(Mode.group_language, 77777, 'fa'))
# t3 = threading.Thread(
#     target=Database.do, args=(Mode.group_stats, 347349, 'city'))

# t1.start()
# t2.start()
# t3.start()

# print(p)
# print(g)
