import pandas as pd

g= pd.DataFrame({
    'group': [],
    'mafia': [],
    'people': [],
    'language': []
    })

p= pd.DataFrame({
    'player': [],
    'mafia_win': [],
    'mafia_lose': [],
    'people_win': [],
    'people_lose': [],
    
    })



def add_group(d, groupid, result, language):
    if groupid not in list(d['group']):
        if result== 'mafia':
            add= {'group': groupid, 'mafia': 1, 'people': 0, 'language': language}
        else:
            add= {'group': groupid, 'mafia': 0, 'people': 1, 'language': language}
        d= d.append(add, ignore_index=True)
    else:
        index= d[d['group']== groupid].index[0]
        if result== 'mafia':
            d.loc[index, 'mafia']+=1
        
        else:
            d.loc[index, 'people']+=1
    
    d['totalgames']= d['mafia']+ d['people']
    
    return d
        
        


def add_players(d, playerlist):
    ids= [i[0] for i in playerlist]
    roles= [i[1] for i in playerlist]
    results= [i[2] for i in playerlist]
    for i in range(len(ids)):
        if ids[i] in list(d['player']):
            
            index= d[d['player']== ids[i]].index[0]
            
            if (roles[i]== 'mafia') and (results[i]== 1):
                d.loc[index, 'mafia_win']+=1
             
            if (roles[i]== 'mafia') and (results[i]== 0):
                d.loc[index, 'mafia_lose']+=1
                
            if (roles[i]== 'people') and (results[i]== 1):
                d.loc[index, 'people_win']+=1
            
            if (roles[i]== 'people') and (results[i]== 0):
                d.loc[index, 'people_lose']+=1
        
        else:
            
            if (roles[i]== 'mafia') and (results[i]== 1):
                to_add= {'player': ids[i], 'mafia_win': 1, 'mafia_lose': 0,'people_win': 0, 'people_lose': 0,}
             
            if (roles[i]== 'mafia') and (results[i]== 0):
                to_add= {'player': ids[i], 'mafia_win': 0, 'mafia_lose': 1,'people_win': 0, 'people_lose': 0,}
             
            if (roles[i]== 'people') and (results[i]== 1):
                to_add= {'player': ids[i], 'mafia_win': 0, 'mafia_lose': 0,'people_win': 1, 'people_lose': 0,}
             
            if (roles[i]== 'people') and (results[i]== 0):
                to_add= {'player': ids[i], 'mafia_win': 0, 'mafia_lose': 0,'people_win': 0, 'people_lose': 1,}
            d= d.append(to_add, ignore_index=True)
        d['total']= d['people_lose']+ d['people_win']+ d['mafia_win']+ d['mafia_lose']
    
    return d


def get_group(d, groupid):
    gp = dict(d[d.group== groupid].reset_index().iloc[0])
    return {
        'group': gp['group'],
        'mafia': gp['mafia'],
        'people': gp['people'],
        'total': gp['totalgames'],
        'mafia_percent': gp['mafia']/ gp['totalgames'],
        'people_percent': gp['people']/ gp['totalgames']
        }

    

def get_player(d, playerid):
    pl = dict(d[d.player== playerid].reset_index().iloc[0])
    return {
        'player': pl['player'],
        'mafia_win': pl['mafia_win'],
        'people_win': pl['people_win'],
        'mafia_lose': pl['mafia_lose'],
        'people_lose': pl['people_lose'],
        'total': pl['total'],
        
        'mafia_win_percent': pl['mafia_win']/ pl['total'],
        'people_win_percent': pl['people_win']/ pl['total']
        
        }
    

