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
last_leader_check = time.time()
leader_check_interval = 5

# Election message counters
are_you_alive_messages = 0
yes_messages = 0
coordinator_messages = 0
become_leader_messages = 0

# -------------------------
# SEND A MESSAGE
# -------------------------

def send_message(target_process, message):

    global are_you_alive_messages
    global coordinator_messages
    global become_leader_messages

    if message == "ARE_YOU_ALIVE":
        are_you_alive_messages += 1

    elif message == "COORDINATOR":
        coordinator_messages += 1

    elif message == "BECOME_LEADER":
        become_leader_messages += 1

    target_port = 5000 + target_process
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(2)

    try:
        target_host = "p" + str(target_process)
        client.connect((target_host, target_port))

        full_message = message + " " + str(process_id)
        client.sendall(full_message.encode())

        print(
            "P" + str(process_id) +
            " -> P" + str(target_process) +
            ": " + message
        )

        if message == "ARE_YOU_ALIVE":

            response = client.recv(1024).decode().strip()

            if response == "YES":
                print(
                    "P" + str(target_process) +
                    " -> P" + str(process_id) +
                    ": YES"
                )
                return True

            return False

        return True

    except (OSError, socket.timeout):

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

    if election_in_progress:
        return

    election_in_progress = True

    print(
        "\nP" + str(process_id) +
        " starts an improved election"
    )

    # Start with the highest possible process ID
    # and work downwards
    for process in range(
        total_processes,
        process_id,
        -1
    ):

        success = send_message(
            process,
            "ARE_YOU_ALIVE"
        )

        if success:

            leader = process
            election_in_progress = False

            print(
                "P" + str(process_id) +
                " found highest living process: P" +
                str(process)
            )

            send_message(
                process,
                "BECOME_LEADER"
            )

            return

    # No higher process is reachable,
    # so this process becomes the leader
    leader = process_id
    election_in_progress = False

    print(
        "\nP" + str(process_id) +
        " is the new leader"
    )
    # Announce the new leader to all other processes
    for process in range(1, total_processes + 1):

        if process != process_id:
            send_message(process, "COORDINATOR")

def check_leader():

    global leader

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

                if message_type == "COORDINATOR":

                    leader = sender
                    election_in_progress = False

                    print(
                        "P" + str(process_id) +
                        " now knows that P" +
                        str(leader) +
                        " is the leader"
                    )
                elif message_type == "PING":

                    send_message(sender, "PONG")

                elif message_type == "ARE_YOU_ALIVE":

                    print(
                        "P" + str(process_id) +
                        " automatically responds YES"
                        )
                    yes_messages += 1
                    connection.send("YES".encode())

                elif message_type == "BECOME_LEADER":

                    already_leader = (leader == process_id)

                    leader = process_id
                    election_in_progress = False

                    if not already_leader:

                        print(
                            "\nP" + str(process_id) +
                            " is the new leader"
                        )

                        # Announce the leader to all other processes
                        for process in range(1, total_processes + 1):

                            if process != process_id:
                                send_message(process, "COORDINATOR")

                    else:

                        # Already leader: confirm only to the requester
                        send_message(sender, "COORDINATOR")
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
                    print("ARE_YOU_ALIVE:", are_you_alive_messages)
                    print("YES:", yes_messages)
                    print("COORDINATOR:", coordinator_messages)
                    print("BECOME_LEADER:", become_leader_messages)

                    simulation_total = (
                        are_you_alive_messages
                        + yes_messages
                        + coordinator_messages
                    )

                    print("Total simulation-style messages:", simulation_total)
                    print(
                        "Total distributed election messages:",
                        simulation_total + become_leader_messages
                    )

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

        if current_time - last_leader_check >= leader_check_interval:

            last_leader_check = current_time

            if leader is not None and leader != process_id:

                check_leader()

except KeyboardInterrupt:

    print("\nProcess P" + str(process_id) + " stopped")
    server.close()