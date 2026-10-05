# ORIGINAL BULLY ALGORITHM
def bully_election(start_process, alive):

    # Vi starter med den proces, som opdager at lederen er død
    current_process = start_process

    # Vi tæller beskeder, så vi senere kan sammenligne algoritmerne
    messages = 0

    while True:

        print("\nP" + str(current_process) + " starter et election")

        # Her gemmer vi de processer med højere ID, som svarer
        answers = []

        # Kig på alle processer med højere ID
        for process in range(current_process + 1, len(alive) + 1):

            # Den nuværende proces sender ELECTION
            print("P" + str(current_process) +
                  " -> P" + str(process) +
                  ": ELECTION")

            messages = messages + 1

            # Hvis processen stadig lever, svarer den OK
            if alive[process - 1] == True:

                print("P" + str(process) +
                      " -> P" + str(current_process) +
                      ": OK")

                messages = messages + 1

                # Gem processen som en, der kan overtage election
                answers.append(process)

        # Hvis ingen højere processer svarede,
        # er current_process den højeste levende proces
        if len(answers) == 0:

            leader = current_process

            print("\nP" + str(leader) + " bliver ny leader")

            break

        # Ellers fortsætter den højeste proces, der svarede
        current_process = max(answers)


    # Den nye leader fortæller de andre,
    # at den nu er coordinator
    for process in range(1, len(alive) + 1):

        if alive[process - 1] == True and process != leader:

            print("P" + str(leader) +
                  " -> P" + str(process) +
                  ": COORDINATOR")

            messages = messages + 1


    return leader, messages


# -------------------------------------------------
# FORBEDRET BULLY ALGORITHM
# -------------------------------------------------

def improved_bully(start_process, alive):

    messages = 0

    print("\nP" + str(start_process) +
          " starter forbedret election")

    # Start med den proces, der har det højeste ID.
    #
    # Hvis vi finder en levende proces,
    # ved vi med det samme, at den skal være leader.
    for process in range(len(alive), start_process, -1):

        print("P" + str(start_process) +
              " -> P" + str(process) +
              ": ARE YOU ALIVE?")

        messages = messages + 1

        # Hvis processen lever, har vi fundet
        # den højeste levende proces
        if alive[process - 1] == True:

            print("P" + str(process) +
                  " -> P" + str(start_process) +
                  ": YES")

            messages = messages + 1

            leader = process

            # Stop med at lede
            break

    else:
        # Hvis ingen højere proces lever,
        # bliver start_process selv leader
        leader = start_process


    print("\nP" + str(leader) + " bliver ny leader")


    # Leader fortæller alle andre levende processer,
    # at den nu er coordinator
    for process in range(1, len(alive) + 1):

        if alive[process - 1] == True and process != leader:

            print("P" + str(leader) +
                  " -> P" + str(process) +
                  ": COORDINATOR")

            messages = messages + 1


    return leader, messages


# -------------------------------------------------
# EKSEMPEL
# -------------------------------------------------

# Vi har 6 processer:
#
# P1 P2 P3 P4 P5 P6
#
# True betyder at processen lever
# False betyder at processen er crashed

alive = [
    True,   # P1
    True,   # P2
    True,   # P3
    True,   # P4
    True,   # P5
    False   # P6 er crashed
]


# P6 var leader.
# P2 opdager at P6 ikke længere virker
# og starter derfor election.


print("ORIGINAL BULLY")
leader, messages = bully_election(2, alive)

print("\nLeader:", leader)
print("Antal beskeder:", messages)


print("FORBEDRET BULLY")

leader, messages = improved_bully(2, alive)

print("\nLeader:", leader)
print("Antal beskeder:", messages)
