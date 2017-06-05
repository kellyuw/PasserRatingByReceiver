import nflgame
import pandas as pd

#Check values for passer_rating calculation
def check_val(r):
    if r > 2.375:
        return 2.375
    elif r < 0:
        return 0
    else:
        return r


#Initialize empty lists for schedule (all_games) and play (all_plays) details
all_games = []
all_plays = []


for yr in range(2011,2017):
    print('Getting data for year: ' + str(yr))
    
    #Get all plays from all regular season games for particular year
    games = nflgame.games_gen(year = yr, kind = 'REG')
    plays = nflgame.combine_plays(games).filter(passing_att__ge=1)
    
    #Initialize empty list for each row of play details
    all_s = []
    for p in plays:
        qb = p.players.filter(guess_position = 'QB')
        for q in qb:
            receiver = p.players.receiving()
            if q.player is not None:
                for r in receiver:
                    if r.player is not None:
                        s = {i:j for i,j in q.stats.iteritems()}
                        s.update({'receiver': r.player.name, 'qb': q.player.name, 'team': q.player.team, 'year':str(yr)})
                        all_s += [s]
    all_games += [{i:j for i,j in p.drive.game.schedule.iteritems()}]
    all_plays += all_s
    
#Concatenate all items for schedule and play details
stats_df = pd.concat([pd.DataFrame.from_dict(x, orient = 'index') for x in all_plays], axis = 1).T
sched_df = pd.concat([pd.DataFrame.from_dict(x, orient = 'index') for x in all_games], axis = 1).T

#Get sum for each year, team, qb, and receiver combination
sdf = stats_df.groupby(['year','team','qb','receiver']).sum()
sdf.fillna(value = 0, method = None, axis = None, inplace = True)
sdf.to_csv('Test.csv', sep = ',', header = True, index = False)

#Calculate per_att(for use with passer_rtg calculation)
for val in ['cmp','yds','tds','int']:
    sdf[val + '_per_att'] = sdf['passing_' + val] / sdf['passing_att']
        
#More passer_rtg calculations
#https://en.wikipedia.org/wiki/Passer_rating#NFL_and_CFL_formula
sdf['a'] = sdf['cmp_per_att'].apply(lambda x: check_val((x - .3) * 5))
sdf['b'] = sdf['yds_per_att'].apply(lambda x: check_val((x - 3) * .25))
sdf['c'] = sdf['tds_per_att'].apply(lambda x: check_val(x * 20))
sdf['d'] = sdf['int_per_att'].apply(lambda x: check_val(2.375 - (x * 25)))
sdf['passer_rtg'] = ((sdf['a'] + sdf['b'] + sdf['c'] + sdf['d']) / 6) * 100

#Save to csv
sdf.sort_values('passer_rtg', ascending = True).to_csv('data/RatingByReceiver.csv', sep = ',')
sched_df.to_csv('data/SchedInfo.csv', sep = ',')
