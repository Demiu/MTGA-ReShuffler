#!/usr/bin/env python3

import sys
import argparse
import random
from enum import IntEnum

basic_names = ("Plains", "Island", "Swamp", "Mountain", "Forest")
basic_names_plural = ("Plains", "Islands", "Swamps", "Mountains", "Forests")

true_inputs = ("yes", "y", "true", "t", "1")
top_inputs = ("top", "front", "t")
middle_inputs = ("middle", "m")
bottom_inputs = ("bottom", "back", "b")
none_inputs = ("none", "n")

class Position(IntEnum):
    none = 0,
    top = 1,
    middle = 2,
    bottom = 3,
    count = 4
position_name = ("wherever", "at the top", "in the middle", "at the bottom")

# Reads decklist from the user
# Returns read decklist size, decklist list, sideboard string
def parse_decklist(has_sideboard):
    decksize = 0
    decklist = []
    sideboard = []

    print("Paste in your decklist (has to be in Arena's format), ")
    print("an empty line indicates the end of the list:")
    while True:
        line = input(">")
        if len(line) == 0:
            break

        # Cutoff first element and two last ones for count, set code and collector's number respectively
        # Which leaves the card's name in the middle
        line = line.split(" ", 1)
        line = [line[0]] + line[1].rsplit(" ", 2)

        if len(line) != 4:
            print("Too few elements in the card's decklist entry!")
            print("(", line, ")")
            return 0, []

        count = line[0]
        name = line[1]
        set_code = line[2].strip("()")
        coll_num = line[3]

        if not count.isdecimal():
            print("Invalid card count value!")
            print("(", line, ")")
            return 0, []
        if len(name) < 1:
            print("Invalid card name length!")
            print("(", line, ")")
            return 0, []
        if len(set_code) != 3:
            print("Invalid card's set name length!")
            print("(", line, ")")
            return 0, []
        if len(coll_num) < 1:
            print("Invalid card's collector number length!")
            print("(", line, ")")
            return 0, []

        decksize += int(count)
        decklist.append((int(count), name, set_code, coll_num))

    if (decksize == 0):
        print("You have to parse in a decklist! (is there an empty line at the start?)")
        return 0, []
    
    while True:
        line = input(">")
        if len(line) == 0:
            break
        
        sideboard.append(line)

    return decksize, decklist, sideboard

# Removes basics from decklist into another list
# Returns (separated list of lands, new decklist without said lands)
def separate_basics(decklist):
    basic_indexes = []
    landlist_dirty = []

    # Find basics lands in decklist and save their indexes
    for i in range(len(decklist)):
        # Check name
        if decklist[i][1] in basic_names:
            basic_indexes.append(i)

    for index in basic_indexes:
        landlist_dirty.append(decklist[index])
    for index in sorted(basic_indexes, reverse=True):
        decklist.pop(index)

    return landlist_dirty, decklist

# Segregates the landlist into a list of list of list of lands
# First layer of list separates basic types (Plains, Island etc.)
# The second separates land variations (different sets/arts etc.)
# The third layer is the land variation's data
# Returns (list of (list of (lands data) of type) in basic_names order)
def cleanup_landlist(landlist):
    new_landlist = []

    # Extend to fit all basic types
    basic_types = len(basic_names)
    for i in range(basic_types):
        new_landlist.append([])

    for entry in landlist:
        # Find where it belongs by name
        i = basic_names.index(entry[1])
        # Put it there
        new_landlist[i].append(entry)

    return new_landlist

# Prints found basic lands and their quantity to the user
def announce_found_lands(landlist):
    print("Found lands:")
    for i in range(len(landlist)):
        cnt = 0
        for j in range(len(landlist[i])):
            cnt += landlist[i][j][0]

        if cnt == 1:
            print(" *1", basic_names[i])
        elif cnt > 1:
            print(" *" + str(cnt), basic_names_plural[i])
        
# Reads non basic lands from the user
# Returns the indexes of specified nonbasic lands in decklist
def parse_nbl(decklist):
    print("Type in names or parts of names of nonbasic you wish to treat as a land")
    print("(eg. \"tower\" will match \"Detection Tower\")")
    print("Empty line to stop")

    nbl_indexes = []

    while True:
        sname = input(">").lower()

        if (len(sname) == 0):
            break

        # Find matching names
        found_indexes = []
        for i in range(len(decklist)):
            if i in nbl_indexes:
                continue
            if sname in decklist[i][1].lower():
                found_indexes.append(i)

        if len(found_indexes) == 0:
            print("Didn't found any matching cards! Check for typos")
        elif len(found_indexes) == 1:
            ok = input("Is \"" + decklist[found_indexes[0]]
                       [1] + "\" what you're looking for? (y/n): ")

            if ok in true_inputs:
                nbl_indexes.append(found_indexes[0])
                print(decklist[found_indexes[0]][1],
                      "is marked as a nonbasic land.")
            else:
                print("Ok, Check for any typos")
        elif len(found_indexes) > 1:
            print("Multiple cards match this, did you mean:")

            for i in range(len(found_indexes)):
                print(" *", i + 1, " - ",
                      decklist[found_indexes[i]][1], sep="")

            try:
                selection = int(input(
                    "(1-" + str(len(found_indexes)) + " or 0 if none of them are right): "))
            except ValueError:
                selection = 0
            
            if selection == 0:
                print("Ok, Check for any typos")
            elif selection > 0 and selection < (len(found_indexes) + 1):
                nbl_indexes.append(found_indexes[selection - 1])
                print(decklist[found_indexes[selection - 1]]
                      [1], "is marked as a nonbasic land.")
            else:
                print("Invalid number or not a number!")

    return nbl_indexes

# Separates nonbasic lands specified in nbl indexes from decklist
# Returns (separated list of nonbasic lands, new decklist without said lands)
def separate_nbls(decklist, nbl_indexes):
    nbls = []

    for index in nbl_indexes:
        nbls.append(decklist[index])
    for index in sorted(nbl_indexes, reverse=True):
        decklist.pop(index)

    return nbls, decklist

# Reads land positions from the user
def parse_land_pos(landlist, nbllist):
    print("\nNow you'll specify land positions in the new decklist to influence their priority",
          " *top    - the lands will go to the top, INCREASING their chance of being drawn in the first hand",
          " *middle - the lands will go to the middle, EQUALIZING their chance of being drawn in the first hand",
          " *bottom - the lands will go to the bottom, DECREASING their chance of being drawn in the first hand",
          " *none   - the lands will go wherever",
          sep="\n")
    
    basic_positions = []
    nbl_positions = []

    for i in range(len(landlist)):
        if len(landlist[i]) == 0:
            basic_positions.append(Position.none)
            continue
        
        while True:
            pos = input("Where should " + basic_names_plural[i] + " be put? (t/m/b/n): ").lower()

            if pos in none_inputs:
                pos = Position.none
            elif pos in top_inputs:
                pos = Position.top
            elif pos in middle_inputs:
                pos = Position.middle
            elif pos in bottom_inputs:
                pos = Position.bottom
            else:
                print("I don't know where that is!")
                continue
            
            basic_positions.append(pos)
            print(basic_names_plural[i], "will go", position_name[int(pos)])
            break
    
    for i in range(len(nbllist)):
        while True:
            pos = input("Where should " + nbllist[i][1] + " be put? (t/m/b/n): ").lower()

            if pos in none_inputs:
                pos = Position.none
            elif pos in top_inputs:
                pos = Position.top
            elif pos in middle_inputs:
                pos = Position.middle
            elif pos in bottom_inputs:
                pos = Position.bottom
            else:
                print("I don't know where that is!")
                continue
            
            nbl_positions.append(pos)
            print(nbllist[i][1], "will go", position_name[int(pos)])
            break
    
    return basic_positions, nbl_positions

# Reads land priorities from the user
# Returns a list of priorities 
# Priority values up to len(basic_names) are priorities for basic lands named basic_name[i]
# After that it's nonbasics priorities for nbllist[i - len(basic_name)]
# The priorities are front-to-back (most important front, less important front, middle...)
def parse_land_prio(landpos, nblpos, landlist, nbllist):
    bsc_type_cnt = 0
    lnd_type_cnt = 0
    for basic in landlist:
        if len(basic) > 0:
            lnd_type_cnt += 1
            bsc_type_cnt += 1
    lnd_type_cnt += len(nbllist)

    # Only 1 type of land
    if lnd_type_cnt == 1:
        # Only basic lands
        if bsc_type_cnt == 1:
            for i in range(len(landlist)):
                if len(landlist[i]) > 0:
                    return [i]
        # Only 1 type of nonbasic land
        else:
            # Return only the value of the first nbl, so 1 index out of range of basic_names
            return [len(basic_names)]
    
    # Multiple types of lands
    print("\nNow you'll pick card priority in their position")
    print("Eg. Islands and Swamps should go on to bottom, but which one should be first?")
    print("Names picked first will be put in more at the top (INCREASING their pick chance)")
    priolist = []
    for pos in range(Position.count):
        # Skip none
        if pos == Position.none:
            continue
        # Check how many are in pos
        pos_cnt = 0
        for pos_it in landpos:
            if pos_it == pos:
                pos_cnt += 1
        for pos_it in nblpos:
            if pos_it == pos:
                pos_cnt += 1
        if pos_cnt == 0:
            continue

        print("\nChoose the the land priority", position_name[pos])
        handled = 0
        while True:
            # Find one last and and add it at the end
            if handled == (pos_cnt - 1):
                for i in range(len(landlist)):
                    if len(landlist[i]) > 0 and landpos[i] == pos and not i in priolist:
                        priolist.append(i)
                        break
                for i in range(len(nbllist)):
                    if nblpos[i] == pos and not ((i + len(basic_names)) in priolist):
                        priolist.append(i + len(basic_names))
                break

            print("Choose next land:")
            # Print basics
            for i in range(len(landlist)):
                # Land has to be present, assigned to this position and not already handled
                if len(landlist[i]) > 0 and landpos[i] == pos and not i in priolist:
                    print(" *", (i + 1), " - ", basic_names_plural[i], sep="")
            # Print nbls
            for i in range(len(nbllist)):
                # Land has assigned to this position and not already handled
                if nblpos[i] == pos and not ((i + len(basic_names)) in priolist):
                    print(" *", (i + len(basic_names) + 1), " - ", nbllist[i][1], sep="")
            
            choice = int(input(">")) - 1
            # check if basic land
            if choice >= 0 and choice < len(basic_names):
                if len(landlist[choice]) > 0:
                    print(basic_names_plural[choice], "will go before the rest")
                    handled += 1
                    priolist.append(choice)
                    continue
            # check if nbl
            if choice >= len(basic_names) and choice < (len(basic_names) + len(nbllist)):
                print(nbllist[choice - len(basic_names)][1], "will go before the rest")
                handled += 1
                priolist.append(choice)
                continue
            
            #not found
            print("Invalid index!")
    
    return priolist

# Reads cards "fake cmc" used for determining their order in decklist
# Returns an array of fake cmcs the size of decklist with each nth entry representing nth elem. in decklist
# Or an empty array if the user doesnt wish to specify fake cmcs
def parse_mana(decklist):
    print("\nNow you can specify FAKE converted mana cost")
    print("These will determine the position of the nonland cards in the deck")
    print("The cards with LESS cmc will go on top, INCREASING their chance for being drawn")
    print("These are not checked and can be fake")
    print("Eg. You can give UUW card 3.5 cmc and 2U card 2.7 cmc, because the 2nd card is easier to cast")
    print("Or you can give an expensive 1-of card low cmc in hopes you'll get it in your opening hand")
    print("If you don't specify these fake cmc the cards will go into the deck at random")
    opt = input("Do you wish to specify fake mana costs? (y/n): ")

    if not opt in true_inputs:
        return []
    
    cmcs = []
    for card in decklist:
        cmc = float(input("What's the fake cmc of \"" + card[1] + "\"? (number): "))
        cmcs.append(cmc)
    
    return cmcs
           
# Makes a decklist from provided data
# Returns newly created decklist
def make_new_decklist(decksize, decklist, landlist, nbllist, landpos, nblpos, landprio, manalist):
    # Setup spells decklist
    if len(manalist) > 0:
        # sort decklist according to manalist
        decklist = [x for y,x in sorted(zip(manalist, decklist))]
    else:
        # random order
        random.shuffle(decklist)

    # Put in lands with "wherever" location, aka the ones not in landprio
    for i in range(len(landlist)):
        if not i in landprio:
            for j in range(len(landlist[i])):
                decklist.insert(random.randrange(0, len(decklist)), landlist[i][j])
    for i in range(len(nbllist)):
        if not (i + len(landlist)) in landprio:
            decklist.insert(random.randrange(0, len(decklist)), nbllist[i])
    
    # Merge lands and decklist
    new_decksize = 0
    new_decklist = []
    # Put in top lands
    while len(landprio) > 0:
        land_prio_idx = landprio[0]
        is_basic = land_prio_idx < len(landlist)
        # Check if same position (top)
        if is_basic:
            if landpos[land_prio_idx] != Position.top:
                break
        else:
            if nblpos[land_prio_idx - len(landlist)] != Position.top:
                break
        # Fill in this land type
        if is_basic:
            for basic_variant in landlist[land_prio_idx]:
                new_decksize += basic_variant[0]
                new_decklist.append(basic_variant)
        else:
            new_decksize += nbllist[land_prio_idx - len(landlist)][0]
            new_decklist.append(nbllist[land_prio_idx - len(landlist)])
        landprio.pop(0)
    
    # Fill in spells till middle
    half = int(decksize / 2)
    while new_decksize < half:
        if len(decklist) == 0:
            break

        amount = decklist[0][0]
        if (new_decksize + amount) < half:
            new_decksize += amount
            new_decklist.append(decklist[0])
            decklist.pop(0)
        else:
            # Split spell type
            amount = half - new_decksize
            new_decksize += amount

            # Some shufflin around because tuple is immutable
            new_entry = (amount,) + decklist[0][1:]
            new_decklist.append(new_entry)

            old_entry = decklist.pop(0)
            decklist.insert(0, (old_entry[0] - amount,) + old_entry[1:])
    
    # Fill in middle lands
    while len(landprio) > 0:
        land_prio_idx = landprio[0]
        is_basic = land_prio_idx < len(landlist)
        # Check if same position (middle)
        if is_basic:
            if landpos[land_prio_idx] != Position.middle:
                break
        else:
            if nblpos[land_prio_idx - len(landlist)] != Position.middle:
                break
        # Fill in this land type
        if is_basic:
            for basic_variant in landlist[land_prio_idx]:
                new_decksize += basic_variant[0]
                new_decklist.append(basic_variant)
        else:
            new_decksize += nbllist[land_prio_idx - len(landlist)][0]
            new_decklist.append(nbllist[land_prio_idx - len(landlist)])
        landprio.pop(0)

    # Fill in the rest of the spells
    while len(decklist) > 0:
        amount = decklist[0][0]
        new_decksize += amount
        new_decklist.append(decklist[0])
        decklist.pop(0)
    
    while len(landprio) > 0:
        land_prio_idx = landprio[0]
        is_basic = land_prio_idx < len(landlist)
        # Fill in this land type
        if is_basic:
            for basic_variant in landlist[land_prio_idx]:
                new_decksize += basic_variant[0]
                new_decklist.append(basic_variant)
        else:
            new_decksize += nbllist[land_prio_idx - len(landlist)][0]
            new_decklist.append(nbllist[land_prio_idx - len(landlist)])
        landprio.pop(0)
    
    return new_decklist

# Prints the decklist in the MTGA format
def print_decklist(decklist, sideboard):
    print("\nHere's your new decklist:")
    for entry in decklist:
        print(entry[0], entry[1], "(" + entry[2] + ")", entry[3])
    
    if sideboard != "":
        print("")
        print(sideboard)

    print ("\nYou can now import this into MTGA")

def main(argv):
    decksize = 0
    # list of tuples, elements of the tuple are (amount, name, set code, collector's num) in this order
    decklist = []
    sideboard = ""
    # list of basic lands, grouped by type
    landlist = []
    # list of positions for each basic land type
    landpos = []
    # list of nbls
    nbllist = []
    # list of positions for each nonbasic land type
    nblpos = []
    # list of priorities of resolving lands, 0 to (len(basic_names) - 1) are basics, then offset nbl indx
    landprio = []
    # list of fake cmcs of decklist, for sorting
    manalist = []

    has_sb = input("Does this deck have a sideboard? (y/n): ")
    has_sb = has_sb.lower() in true_inputs

    decksize, decklist, sideboard = parse_decklist(has_sb)
    if decksize == 0:
        print("Something went wrong, aborting")
        return

    landlist, decklist = separate_basics(decklist)
    landlist = cleanup_landlist(landlist)

    announce_found_lands(landlist)

    has_nbl = input(
        "Are there any nonbasic lands you wish to specify for placement (this isn't required)? (y/n): ")
    has_nbl = has_nbl.lower() in true_inputs
    if has_nbl:
        nbl_indexes = parse_nbl(decklist)
        nbllist, decklist = separate_nbls(decklist, nbl_indexes)

    landpos, nblpos = parse_land_pos(landlist, nbllist)

    landprio = parse_land_prio(landpos, nblpos, landlist, nbllist)

    manalist = parse_mana(decklist)

    decklist = make_new_decklist(decksize, decklist, landlist, nbllist, landpos, nblpos, landprio, manalist)
    print_decklist(decklist, sideboard)


# Test deck
"""
2 Skymarcher Aspirant (RIX) 21
4 Dusk Legion Zealot (RIX) 70
4 Legion Lieutenant (RIX) 163
4 Martyr of Dusk (RIX) 14
2 Paladin of Atonement (RIX) 16
3 Sanctum Seeker (XLN) 120
2 Twilight Prophet (RIX) 88
3 Queen's Commission (XLN) 29
4 Call to the Feast (XLN) 219
4 Legion's Landing (XLN) 22
4 Radiant Destiny (RIX) 18
4 Conclave Tribunal (GRN) 6
1 Arch of Orazca (RIX) 185
1 Isolated Chapel (DAR) 241
1 Orzhov Guildgate (RNA) 252
8 Plains (M19) 261
6 Swamp (M19) 269
3 Unclaimed Territory (XLN) 258

2 Duress (XLN) 105
1 Settle the Wreckage (XLN) 34
1 Kaya's Wrath (RNA) 187
1 Vampire's Zeal (XLN) 43
1 Never Happened (GRN) 80
4 Bishop's Soldier (XLN) 6
2 Cast Down (DAR) 81
2 Ajani's Welcome (M19) 6
1 Ixalan's Binding (XLN) 17
"""

# Call main
if __name__ == "__main__":
    main(sys.argv[1:])
