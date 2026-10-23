# -------------------------------------------------
# FORBEDRET BULLY ALGORITHM
# -------------------------------------------------

def improved_bully(start_process, alive):

    messages = 0

    print("\nP" + str(start_process) + " starter forbedret election")

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
