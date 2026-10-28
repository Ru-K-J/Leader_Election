def bully_election(start_process, alive):

    if not (1 <= start_process <= len(alive)) or not alive[start_process - 1]:
        raise ValueError("start_process skal være en levende proces i 1..N")

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


def improved_bully(start_process, alive):

    if not (1 <= start_process <= len(alive)) or not alive[start_process - 1]:
        raise ValueError("start_process skal være en levende proces i 1..N")

    messages = 0

    print("\nP" + str(start_process) + " starter ELECTION")

    # Start med højeste ID
    for process in range(len(alive), start_process, -1):

        print("P" + str(start_process) +
              " -> P" + str(process) +
              ": ELECTION")

        messages += 1

        if alive[process - 1]:

            print("P" + str(process) +
                  " -> P" + str(start_process) +
                  ": OK")

            messages += 1
            leader = process
            break

    else:
        leader = start_process

    print("\nP" + str(leader) + " bliver COORDINATOR")

    for process in range(1, leader):

        if alive[process - 1]:

            print("P" + str(leader) +
                  " -> P" + str(process) +
                  ": COORDINATOR")

            messages += 1

    return leader, messages


if __name__ == "__main__":

    # True = lever, False = crashed
    alive = [True, True, True, True, True, False]   # P1..P5 lever, P6 crashed

    print("ORIGINAL BULLY")
    leader, messages = bully_election(2, alive)
    print("\nLeader: P" + str(leader))
    print("Antal beskeder:", messages)

    print("\nFORBEDRET BULLY")
    leader, messages = improved_bully(2, alive)
    print("\nLeader: P" + str(leader))
    print("Antal beskeder:", messages)
