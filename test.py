import sqlite3
import random

cache = set()
CURRENT_STANDINGS = {}
conn = sqlite3.connect("users.db")
cursor = conn.cursor()

def setup():
    cursor.execute("""
        SELECT username FROM users
    """)
    result = cursor.fetchall()
    for name in result:
        # Newly inserted player
        if name not in CURRENT_STANDINGS:
            CURRENT_STANDINGS[name[0]] = 0

def fetch_results():
    cursor.execute("""
        SELECT username, status FROM users
    """)

    result = cursor.fetchall()
    if len(result)%2 == 1:
        return "Odd pairings. Please insert another player"
    results = {}
    for output in result:
        if output[0] not in results:
            results[output[0]] = output[1]

    for key, value in results.items():
        if value == "Win":
            CURRENT_STANDINGS[key] += 1
        elif value == "Lose":
            CURRENT_STANDINGS[key] -= 1

def order(dictionary):
    sorted_pos = list(sorted(dictionary.items(), key=lambda item: item[1], reverse=True))
    return sorted_pos


def calculate_swiss():
    pairings = []
    sorted_pos = order(CURRENT_STANDINGS)

    # Sort based off pts
    grps = []
    grp = []
    for i in range(len(sorted_pos)-1):
        if sorted_pos[i][1] == sorted_pos[i+1][1]:
            grp.append(sorted_pos[i][0])
        else:
            grp.append(sorted_pos[i][0])
            grps.append(grp)
            grp = []
    grp.append(sorted_pos[-1][0])
    grps.append(grp)

    temp = []
    for grp in grps:
        if temp:
            for name in temp:
                grp.append(name)
            temp = []
        if (len(grp)%2) == 1:
            temp = [grp.pop()]
        
        # Now pair the players in this group
        while len(grp) >= 2:
            # Get all possible valid pairs that haven't been matched before
            valid_pairs = []
            for i in range(len(grp)):
                for j in range(i+1, len(grp)):
                    pair = tuple(sorted((grp[i], grp[j])))  
                    if pair not in cache:
                        valid_pairs.append((i, j, pair))
            
            if not valid_pairs:
                # No valid pairs left, have to rematch
                i, j = 0, 1
                pair = tuple(sorted((grp[i], grp[j])))
            else:
                # Randomly select one of the valid pairs
                i, j, pair = random.choice(valid_pairs)
            
            # Add the pair to pairings and cache
            pairings.append((grp[i], grp[j]))
            cache.add(pair)
            
            # Remove the paired players from the group
            # Remove the higher index first to avoid index errors
            grp.pop(max(i, j))
            grp.pop(min(i, j))
    return pairings
        

setup()
result = fetch_results()
if result:
    print(result)
else:
    print(result)
    print(order(CURRENT_STANDINGS))
    pairings = calculate_swiss()
    print("pairings", pairings)