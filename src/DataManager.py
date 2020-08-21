import pandas as pd
import Player
from Player import Roles

g = pd.DataFrame({
    'group': [],
    'mafia': [],
    'city': [],
    'language': []
})

p = pd.DataFrame({
    'player': [],
    'mafia_win': [],
    'mafia_lose': [],
    'city_win': [],
    'city_lose': [],

})

'''
Example:

update_group ( database , group_id , result = Mafia or City , language )

'''


def update_group(d, group_id, result, language):
    if group_id not in list(d['group']):
        if result == 'mafia':
            add = {'group': group_id, 'mafia': 1, 'city': 0, 'language': language}
        else:
            add = {'group': group_id, 'mafia': 0, 'city': 1, 'language': language}
        d = d.append(add, ignore_index=True)
    else:
        index = d[d['group'] == group_id].index[0]
        if result == 'mafia':
            d.loc[index, 'mafia'] += 1

        else:
            d.loc[index, 'city'] += 1

    d['total_games'] = d['mafia'] + d['people']

    return d


'''
Example 

update_players(database , list of players , result = Mafia or City )

'''


def update_players(d, player_list, result):
    ids = [player.user_id for player in player_list]
    roles = [player.role for player in player_list]
    for i in range(len(ids)):
        if ids[i] in list(d['player']):
            index = d[d['player'] == ids[i]].index[0]

            if (roles[i] == Roles.Mafia or roles[i] == Roles.GodFather) and (result == "Mafia"):
                d.loc[index, 'mafia_win'] += 1

            elif (roles[i] == Roles.Mafia or roles[i] == Roles.GodFather) and (result == "City"):
                d.loc[index, 'mafia_lose'] += 1

            elif (roles[i] != Roles.Mafia and roles[i] != Roles.GodFather) and (result == "Mafia"):
                d.loc[index, 'city_lose'] += 1

            else:
                d.loc[index, 'city_win'] += 1

        else:

            if (roles[i] == Roles.Mafia or roles[i] == Roles.GodFather) and (result == "Mafia"):
                to_add = {'player': ids[i], 'mafia_win': 1, 'mafia_lose': 0, 'people_win': 0, 'people_lose': 0, }

            elif (roles[i] == Roles.Mafia or roles[i] == Roles.GodFather) and (result == "City"):
                to_add = {'player': ids[i], 'mafia_win': 0, 'mafia_lose': 1, 'people_win': 0, 'people_lose': 0, }

            elif (roles[i] != Roles.Mafia and roles[i] != Roles.GodFather) and (result == "Mafia"):
                to_add = {'player': ids[i], 'mafia_win': 0, 'mafia_lose': 0, 'people_win': 1, 'people_lose': 0, }

            else:
                to_add = {'player': ids[i], 'mafia_win': 0, 'mafia_lose': 0, 'people_win': 0, 'people_lose': 1, }
            d = d.append(to_add, ignore_index=True)
        d['total'] = d['people_lose'] + d['people_win'] + d['mafia_win'] + d['mafia_lose']

    return d


def get_group(d, group_id):
    gp = dict(d[d.group == group_id].reset_index().iloc[0])
    return {
        'group': gp['group'],
        'mafia': gp['mafia'],
        'city': gp['city'],
        'total': gp['total_games'],
        'mafia_percent': gp['mafia'] / gp['total_games'],
        'city_percent': gp['city'] / gp['total_games']
    }


def get_player(d, player_id):
    pl = dict(d[d.player == player_id].reset_index().iloc[0])
    return {
        'player': pl['player'],
        'mafia_win': pl['mafia_win'],
        'city_win': pl['city_win'],
        'mafia_lose': pl['mafia_lose'],
        'city_lose': pl['city_lose'],
        'total': pl['total'],

        'mafia_win_percent': pl['mafia_win'] / pl['total'],
        'city_win_percent': pl['people_win'] / pl['total']

    }
