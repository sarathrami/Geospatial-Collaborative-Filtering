from __future__ import division
from math import sqrt
import pickle
import powerlaw
import random

MAX_FRIENDS_ALLOWED = 30
usr_venue_rating = {}
friends = {}
user_frnd_dist = {}

def loadData(path="."):
    """
    usrs = {}
    for line in open(path + "/users.sample"):
        line = line.replace(' ', "")
        (id, longitude, latitude) = line.split("|")
        usrs[0] = (int(id), float(longitude), float(latitude))
        print usrs[0]

    user_frnd_dist = pickle.load(open(path + 'friends_gyr_equals.txt', 'rb'))
    data = []
    for usr in user_frnd_dist:
        frnd_dst = user_frnd_dist[usr]
        for fd in frnd_dst:
            data.append(fd[1])

    results = powerlaw.Fit(data)
    print results.power_law.alpha
    print results.power_law.xmin
    """
    for line in open(path + "ratings.dat"):
        try:
            (uid, vid, r) = map(int, line.replace(' ', "").split("|"))
            if uid not in usr_venue_rating: usr_venue_rating[uid] = {}
            if vid not in usr_venue_rating[uid]: usr_venue_rating[uid][vid] = {}
            usr_venue_rating[uid][vid] = r
        except:
            pass

    for line in open(path + "socialgraph.dat"):
        try:
            (uid1, uid2) = map(int, line.replace(' ', "").split("|"))
            if uid1 not in friends: friends[uid1]=[]
            if len(friends[uid1]) < MAX_FRIENDS_ALLOWED:
                friends[uid1].append(uid2)
        except:
            pass

def cosine_similarity(usr1, usr2, cache={}):

    if not usr1 or not usr2:
        return 0

    (usr1,usr2) = (usr1,usr2) if usr1 > usr2 else (usr2,usr1)
    if (usr1, usr2) in cache: return cache[(usr1, usr2)]

    usr1VSet = set(usr_venue_rating[usr1].keys()) if usr1 in usr_venue_rating else set()
    usr2VSet = set(usr_venue_rating[usr2].keys()) if usr2 in usr_venue_rating else set()
    if len(usr1VSet) == 0 or len(usr2VSet) == 0:
        cache[(usr1, usr2)] = 0
        return 0
    else:
        cache[(usr1, usr2)] = len(usr1VSet.intersection(usr2VSet))/(len(usr1VSet) + len(usr2VSet))
        return cache[(usr1, usr2)]

def pearson_simple_similarity(uid1, uid2, cache={}):

    if (uid1, uid2) in cache:
        return cache[(uid1, uid2)]

    sum_xy = 0
    sum_x = 0
    sum_y = 0
    sum_x2 = 0
    sum_y2 = 0
    n = 0

    if uid1 in usr_venue_rating:
        for vid in usr_venue_rating[uid1]:
            if vid in usr_venue_rating[uid2]:
                n += 1
                x = usr_venue_rating[uid1][vid]
                y = usr_venue_rating[uid2][vid]
                sum_xy += x * y
                sum_x += x
                sum_y += y
                sum_x2 += x**2
                sum_y2 += y**2

    if n == 0:
        cache[(uid1, uid2)] = 0
        return cache[(uid1, uid2)]

    denominator = sqrt(sum_x2 - (sum_x**2) / n) * sqrt(sum_y2 -(sum_y**2) / n)

    if denominator == 0:
        cache[(uid1, uid2)] = 0
    else:
        numerator = (sum_xy - (sum_x * sum_y) / n)
        cache[(uid1, uid2)] = numerator / denominator

    return cache[(uid1, uid2)]

def gyr_simple_similarity(uid1, uid2, cache={}):
    if (uid1, uid2) in cache:
        return cache[(uid1, uid2)]



    return cache[(uid1, uid2)]

def getMostSimilarNScores_Usrs(usr, n=5, fn_similarity = pearson_simple_similarity):
    similarity_vals = [(fn_similarity(usr, curr_usr), curr_usr)
              for curr_usr in usr_venue_rating if curr_usr != usr]
    similarity_vals.sort()
    similarity_vals.reverse()
    return similarity_vals[0:n]

def getRecommendations(usr, n=-1, fn_similarity = pearson_simple_similarity):
    total_similarity_score_for_vid = {}
    total_similarity_sums_for_vid = {}

    for curr_usr in usr_venue_rating:
        if curr_usr == usr or usr not in friends or curr_usr not in friends[usr]:
            continue

        similarity_scr = fn_similarity(usr, curr_usr)

        if similarity_scr <= 0:
            continue
        for vid in usr_venue_rating[curr_usr]:
            if vid not in usr_venue_rating[usr] or usr_venue_rating[usr][vid] == 0:
                if vid not in total_similarity_score_for_vid: total_similarity_score_for_vid[vid]=0
                if vid not in total_similarity_sums_for_vid: total_similarity_sums_for_vid[vid] = 0
                total_similarity_score_for_vid[vid] += usr_venue_rating[curr_usr][vid] * similarity_scr
                total_similarity_sums_for_vid[vid] += similarity_scr

    recommendations = [(total / total_similarity_sums_for_vid[vid], vid) for vid, total in total_similarity_score_for_vid.items()]
    recommendations.sort()
    recommendations.reverse()
    return recommendations[0:n]


def randomVenueRemoval(usr, per_rem=20):
    removed_venue_rating_list = []
    if usr in usr_venue_rating:
        venues_ratings = usr_venue_rating[usr]
        while len(venues_ratings) > 0 and per_rem > 100 * len(removed_venue_rating_list)/ len(venues_ratings):
            venue = venues_ratings.keys()[random.randrange(0, len(venues_ratings))]
            removed_venue_rating_list.append((venue, venues_ratings[venue]))
            del venues_ratings[venue]

    return removed_venue_rating_list

def randomVerification(iterations = 1, per_rem=20, fn_similarity = pearson_simple_similarity):

    hit = 0
    runs = 0
    i = 0
    usrs = list(usr_venue_rating.keys())
    while usrs and len(usrs) and i < iterations:
        usr = usrs.pop(random.randrange(0, len(usrs)))
        solution = randomVenueRemoval(usr, per_rem=20)

        if not solution or not len(solution):
            print "Nothing removed."
            continue
        else:
            i += 1

        venues_removed = [x[0] for x in solution]

        print 'User [%d] randomly selected for test...' % usr
        print 'Venues removed for User [%d] are' % usr, venues_removed
        found_solution = getRecommendations(usr, n=-1, fn_similarity=fn_similarity)
        venues_recovered = [x[1] for x in found_solution]
        print 'Venues recovered for User [%d] are' % usr, venues_recovered
        success_ratio = len(set(venues_recovered).intersection(set(venues_removed))) / (len(venues_removed))
        hit += success_ratio
        runs += 1

        # put back the ratings
        for vr in solution:
            usr_venue_rating[usr][vr[0]] = vr[1]

        print 'Success ratio is {0}'.format(100*int(success_ratio))
        print '-'*50

    print 'Avg success ratio is {0}'.format(100*int(hit)/runs)

if __name__ == '__main__':
    loadData("./data/")
    randomVerification(iterations=25, per_rem=20, fn_similarity=cosine_similarity)

    for uid in friends:
        if uid == 5:
            print 'Friends of [%d] are =' % uid, friends[uid]
            print getRecommendations(uid, fn_similarity = pearson_simple_similarity)
            #print getRecommendations(uid, fn_similarity = cosine_similarity)
            print '-'*50                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    
