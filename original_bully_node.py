import sys
import socket
import select
import time


if len(sys.argv) != 2:
    print("Usage: python3 node.py <process_id>")
    sys.exit(1)


process_id = int(sys.argv[1])
port = 5000 + process_id
total_processes = 6

leader = None
election_in_progress = False
election_answers = []
election_started = False

# Message counters
election_messages = 0
ok_messages = 0
coordinator_messages = 0

election_deadline = None
election_response_timeout = 2

coordinator_deadline = None
coordinator_timeout = 5

last_leader_check = time.time()
leader_check_interval = 5

# -------------------------
# SEND A MESSAGE
# -------------------------

def send_message(target_process, message):

    global election_messages
    global ok_messages
    global coordinator_messages

    # Count outgoing election-message attempts
    if message == "ELECTION":
        election_messages += 1

    target_port = 5000 + target_process

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        target_host = "p" + str(target_process)
        client.connect((target_host, target_port))

        full_message = message + " " + str(process_id)

        client.send(full_message.encode())

        if message == "OK":
            ok_messages += 1

        elif message == "COORDINATOR":
            coordinator_messages += 1

        print(
            "P" + str(process_id) +
            " -> P" + str(target_process) +
            ": " + message
        )

        return True

    except (ConnectionRefusedError, socket.gaierror):
        print(
            "P" + str(target_process) +
            " is not responding"
        )
        return False

    finally:
        client.close()

def start_election():

    global election_in_progress
    global leader
    global election_answers
    global election_deadline
    global coordinator_deadline
    global election_started

    if election_in_progress or election_started:
        return

    election_started = True
    election_in_progress = True
    leader = None
    election_answers = []
    election_deadline = None
    coordinator_deadline = None

    print(
        "\nP" + str(process_id) +
        " starts an election"
    )

    for process in range(
        process_id + 1,
        total_processes + 1
    ):

        send_message(process, "ELECTION")

    # Allow time for OK responses to arrive
    election_deadline = time.time() + election_response_timeout

def check_leader():

    global leader
    global election_started

    if leader is None:
        print("No leader is currently known")
        return

    if leader == process_id:
        print("P" + str(process_id) + " is the leader")
        return

    print(
        "P" + str(process_id) +
        " is checking leader P" +
        str(leader)
    )

    success = send_message(leader, "PING")

    if not success:

        print(
            "Leader P" + str(leader) +
            " is not responding"
        )

        leader = None
        election_started = False

        start_election()

# -------------------------
# SERVER
# -------------------------

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind(("0.0.0.0", port))
server.listen()

print("Process P" + str(process_id) +
      " is running on port " + str(port))

print("Commands: election, status, check, send <process_id> <message>")


# -------------------------
# MAIN LOOP
# -------------------------

try:
    while True:

        # Wait for either:
        # 1. another process sending us something
        # 2. keyboard input
        readable, _, _ = select.select(
            [server, sys.stdin],
            [],
            [],
            1
        )

        for source in readable:

            # Incoming network message
            if source == server:

                connection, address = server.accept()

                data = connection.recv(1024)
                message = data.decode()

                parts = message.split()

                message_type = parts[0]
                sender = int(parts[1])

                print(
                    "\nP" + str(process_id) +
                    " received " + message_type +
                    " from P" + str(sender)
                )

                # Automatically answer an ELECTION message
                if message_type == "ELECTION":

                    print(
                        "P" + str(process_id) +
                        " automatically responds OK"
                    )

                    send_message(sender, "OK")

                    # Every higher process that responds OK
                    # continues the election, but only if
                    # it has not already started one.
                    if not election_started and leader != process_id:
                        start_election()

                elif message_type == "OK":

                    if election_in_progress and election_deadline is not None:

                        if sender not in election_answers:

                            election_answers.append(sender)

                            print(
                                "P" + str(process_id) +
                                " recorded OK from P" + str(sender)
                            )

                elif message_type == "COORDINATOR":

                    leader = sender
                    election_in_progress = False
                    election_deadline = None
                    coordinator_deadline = None
                    election_answers = []
                    election_started = False

                    print(
                        "P" + str(process_id) +
                        " now knows that P" +
                        str(leader) +
                        " is the leader"
                    )

                elif message_type == "PING":

                    send_message(sender, "PONG")

                connection.close()

            # Keyboard command
            elif source == sys.stdin:

                try:
                    command = input()
                except EOFError:
                    continue

                parts = command.split(maxsplit=2)

                if command == "election":

                    start_election()

                elif command == "status":

                    print("\n--- STATUS ---")
                    print("Process: P" + str(process_id))
                    print("Leader:", leader)
                    print("Election in progress:", election_in_progress)

                    print("\n--- MESSAGE COUNTERS ---")
                    print("ELECTION:", election_messages)
                    print("OK:", ok_messages)
                    print("COORDINATOR:", coordinator_messages)

                    total_election_messages = (
                        election_messages
                        + ok_messages
                        + coordinator_messages
                    )

                    print("Total simulation-style messages:", total_election_messages)

                elif command == "check":

                    check_leader()

                elif len(parts) == 3 and parts[0] == "send":

                    target_process = int(parts[1])
                    message = parts[2]

                    send_message(target_process, message)

                else:

                    print("Commands:")
                    print("  election")
                    print("  status")
                    print("  send <process_id> <message>")

        # Check the leader periodically
        current_time = time.time()

        # Finish collecting OK responses
        if (
            election_in_progress
            and election_deadline is not None
            and current_time >= election_deadline
        ):

            election_deadline = None

            if len(election_answers) > 0:
                # Higher processes have already started their
                # own elections when they received ELECTION.
                # Wait for the highest living process to
                # announce itself as COORDINATOR.
                coordinator_deadline = time.time() + coordinator_timeout

            else:

                leader = process_id
                election_in_progress = False
                election_started = False
                election_deadline = None
                coordinator_deadline = None

                print(
                    "\nP" + str(process_id) +
                    " is the new leader"
                )

                # Announce the new leader to all other processes
                for process in range(1, process_id):

                    send_message(process, "COORDINATOR")

        # Check whether the selected process failed
        # to announce a new coordinator
        if (
            election_in_progress
            and coordinator_deadline is not None
            and current_time >= coordinator_deadline
        ):

            print(
                "P" + str(process_id) +
                " timed out waiting for COORDINATOR"
            )

            coordinator_deadline = None
            election_in_progress = False
            election_started = False

            # Try the election again
            start_election()

        if current_time - last_leader_check >= leader_check_interval:

            last_leader_check = current_time

            if leader is not None and leader != process_id:

                check_leader()

except KeyboardInterrupt:

    print("\nProcess P" + str(process_id) + " stopped")
    server.close()