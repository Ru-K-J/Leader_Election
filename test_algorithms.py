from original_bully import bully_election
from improved_bully import improved_bully

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


print("=========== ORIGINAL BULLY ===========")
leader, messages = bully_election(2, alive)

print("\nLeader:", leader)
print("Antal beskeder:", messages, "\n")


print("=========== FORBEDRET BULLY ===========")

leader, messages = improved_bully(2, alive)

print("\nLeader:", leader)
print("Antal beskeder:", messages)
