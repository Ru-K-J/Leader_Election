# ORIGINAL BULLY ALGORITHM
def bully_election(start_process, alive):

    messages = 0
    leader = None
    election_started = [False] * len(alive)

    def election(process):

        nonlocal messages, leader

        if election_started[process - 1]:
            return

        election_started[process - 1] = True
        print("\nP" + str(process) + " starter ELECTION")

        higher_alive = []

        # Send ELECTION til alle processer med højere ID
        for higher in range(process + 1, len(alive) + 1):

            print("P" + str(process) +
                  " -> P" + str(higher) +
                  ": ELECTION")

            messages += 1

            # Levende processer svarer OK
            if alive[higher - 1]:

                print("P" + str(higher) +
                      " -> P" + str(process) +
                      ": OK")

                messages += 1
                higher_alive.append(higher)

        # Ingen højere proces svarede
        if len(higher_alive) == 0:

            leader = process
            print("\nP" + str(leader) + " bliver COORDINATOR")
            return

        # Processer der svarede OK overtager election
        for higher in higher_alive:
            election(higher)

    election(start_process)

    # Leader fortæller de andre at den er coordinator
    for process in range(1, leader):

        if alive[process - 1]:

            print("P" + str(leader) +
                  " -> P" + str(process) +
                  ": COORDINATOR")

            messages += 1

    return leader, messages