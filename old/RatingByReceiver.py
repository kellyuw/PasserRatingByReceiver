import numpy as np
import pandas as pd
import nflgame

pd.options.mode.chained_assignment = None  # default='warn'


#Parse stats for particular stat
def parse_play(p, s, t):
    return int(s.split(t + ': ')[1].split(',')[0])

#Check values for passer_rating calculation
def check_val(r):
    if r > 2.375:
        return 2.375
    elif r < 0:
        return 0
    else:
        return r

#Teams
teams = [t[0] for t in nflgame.teams]

#Stat types of interest
stat_types = ['play_num', 'pass_player', 'passing_att', 'passing_cmp', 'passing_incmp', 'passing_int', 'passing_tds', 'passing_yds', 'rec_player', 'receiving_tar', 'receiving_rec', 'receiving_yds']

#Set lower threshold for pass attempts here
pass_att_thr = 50


for yr in range(2011,2017):

    #Initialize empty dataframe for stats each year
    df = pd.DataFrame([np.zeros(len(stat_types))])
    df.columns = [stat_types]
    all_plays = df[1:]

    print 'Getting stats for year: ' + str(yr)

    for team in teams:

        try:
            games = nflgame.games(year = yr, week = range(1,18), kind = 'REG', home = team)
            plays = nflgame.combine_plays(games)

            for i, play in enumerate(plays):
                r = {}
                r['play_num'] = i
                for player in play.players:
                    s = player.formatted_stats()
                    if 'passing_att' in s:
                        r['pass_player'] = str(player.name)
                    elif 'receiving_tar' in s:
                        r['rec_player'] = str(player.name)
                        r['rec_player_pos'] = str(player.guess_position)
                    for t in stat_types:
                        if player.has_cat(t):
                            r[t] = parse_play(player, s, t)
                for t in stat_types:
                    if not r.has_key(t):
                        r[t] = None
                for j in ['qtr','down','ydstogo']:
                    r[j] = play.data[j]
                if r['pass_player'] is not None or r['rec_player'] is not None:
                    new_stats = pd.DataFrame.from_dict(r, orient = 'index').T
                    all_plays = pd.concat([all_plays, new_stats])
        except TypeError:
            print 'Error: ' + team

    imp_stats = all_plays.groupby(['pass_player','rec_player']).sum().sort_values('passing_int', ascending = False)[['passing_att', 'passing_cmp', 'passing_yds', 'passing_tds', 'passing_int','rec_player_pos']]
    f_stats = imp_stats[(imp_stats['passing_att'] > int(pass_att_thr))]
    f_stats.fillna(value = 0, method = None, axis = None, inplace = True)

    #Calculate per_att for use with passer_rtg calculation
    for e in ['cmp','yds','tds','int']:
        f_stats[e + '_per_att'] = f_stats['passing_' + e] / f_stats['passing_att']

    #More passer_rtg calculations
    #https://en.wikipedia.org/wiki/Passer_rating#NFL_and_CFL_formula
    f_stats['a'] = f_stats['cmp_per_att'].apply(lambda x: check_val((x - .3) * 5))
    f_stats['b'] = f_stats['yds_per_att'].apply(lambda x: check_val((x - 3) * .25))
    f_stats['c'] = f_stats['tds_per_att'].apply(lambda x: check_val(x * 20))
    f_stats['d'] = f_stats['int_per_att'].apply(lambda x: check_val(2.375 - (x * 25)))
    f_stats['passer_rtg'] = ((f_stats['a'] + f_stats['b'] + f_stats['c'] + f_stats['d']) / 6) * 100

    #Clean up the position column a bit
    f_stats['rec_pos'] = f_stats['rec_player_pos'].apply(lambda x: x[0:2])
    f_stats = f_stats.drop('rec_player_pos', 1)

    #Save to csv by year
    f_stats.sort_values('passer_rtg', ascending = True).to_csv(str(yr) + 'RatingByReceiver_PassAttThr' + str(pass_att_thr) + '.csv', sep = ',')
