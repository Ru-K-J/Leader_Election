import unittest
import random
import io
import time
from contextlib import redirect_stdout
from original_bully import bully_election
from improved_bully import improved_bully


def quiet(f, start_process, alive):
    """Kør f uden print-output (med input-validering hvis ikke i f)."""
    if not (1 <= start_process <= len(alive)) or not alive[start_process - 1]:
        raise ValueError("start_process skal være en levende proces i 1..N")
    with redirect_stdout(io.StringIO()):
        return f(start_process, alive)


def run_both(s, alive):
    return quiet(bully_election, s, alive), quiet(improved_bully, s, alive)


def expected(s, alive):
    """Uafhængigt orakel: (leder, orig-beskeder, forb-beskeder). Kræver alive[s-1]."""
    n, A = len(alive), sum(alive)
    L = max(i + 1 for i, x in enumerate(alive) if x)
    if L > s:
        initiators = [s] + [p for p in range(s + 1, n + 1) if alive[p - 1]]
        orig_election = sum((n - p) + sum(alive[p:]) for p in initiators)
        return L, orig_election + (A - 1), (n - L + 1) + 1 + (A - 1)
    return L, (n - s) + (A - 1), (n - s) + (A - 1)


# -------------------------------------------------
# 1. LEDERVALG (korrekthed)
# -------------------------------------------------
class TestCorrectness(unittest.TestCase):

    def test_basic(self):
        alive = [True] * 5 + [False]
        (lo, _), (li, _) = run_both(2, alive)
        self.assertEqual((lo, li), (5, 5))

    def test_multiple_failures(self):
        alive = [True, True, True, False, True, True, True, False, False, False]
        (lo, _), (li, _) = run_both(2, alive)
        self.assertEqual((lo, li), (7, 7))

    def test_initiator_is_highest_alive(self):
        (lo, _), (li, _) = run_both(1, [True, False, False, False])
        self.assertEqual((lo, li), (1, 1))

    def test_highest_process_alive(self):
        """Fanger off-by-one på P_N: ingen crashet."""
        (lo, _), (li, _) = run_both(2, [True] * 6)
        self.assertEqual((lo, li), (6, 6))

    def test_initiator_is_P_N(self):
        (lo, _), (li, _) = run_both(6, [True] * 6)
        self.assertEqual((lo, li), (6, 6))

    def test_single_process(self):
        (lo, _), (li, _) = run_both(1, [True])
        self.assertEqual((lo, li), (1, 1))

    def test_gap_in_ids(self):
        """Dødt hul midt i ID-rækken må ikke stoppe søgningen."""
        alive = [True, False, False, True, False, True, False]
        (lo, _), (li, _) = run_both(1, alive)
        self.assertEqual((lo, li), (6, 6))

    def test_only_initiator_alive(self):
        (lo, _), (li, _) = run_both(3, [False, False, True, False, False])
        self.assertEqual((lo, li), (3, 3))

    def test_index_convention(self):
        """P1 er alive[0]. Kun P1 lever -> leder skal være 1, ikke 0."""
        (lo, _), (li, _) = run_both(1, [True, False])
        self.assertEqual((lo, li), (1, 1))

    def test_random_leader_is_highest_alive(self):
        rng = random.Random(0)
        for _ in range(2000):
            n = rng.randint(1, 30)
            alive = [rng.random() > 0.4 for _ in range(n)]
            if not any(alive):
                continue
            s = rng.choice([i + 1 for i in range(n) if alive[i]])
            L = max(i + 1 for i in range(n) if alive[i])
            (lo, _), (li, _) = run_both(s, alive)
            self.assertEqual(lo, L, (alive, s))
            self.assertEqual(li, L, (alive, s))


# -------------------------------------------------
# 1b. BASIC TESTS (enkle scenarier)
# -------------------------------------------------
class TestBullyAlgorithms(unittest.TestCase):

    def test_correct_leader(self):
        alive = [True, True, True, True, True, False]
        leader1, messages1 = run_both(2, alive)[0][0], run_both(2, alive)[0][1]
        leader2, messages2 = run_both(2, alive)[1][0], run_both(2, alive)[1][1]
        self.assertEqual(leader1, 5)
        self.assertEqual(leader2, 5)

    def test_start_process_becomes_leader(self):
        alive = [True, True, True, False, False]
        leader1, messages1 = run_both(3, alive)[0][0], run_both(3, alive)[0][1]
        leader2, messages2 = run_both(3, alive)[1][0], run_both(3, alive)[1][1]
        self.assertEqual(leader1, 3)
        self.assertEqual(leader2, 3)

    def test_highest_process_wins(self):
        alive = [True, True, True, True, True]
        leader1, messages1 = run_both(2, alive)[0][0], run_both(2, alive)[0][1]
        leader2, messages2 = run_both(2, alive)[1][0], run_both(2, alive)[1][1]
        self.assertEqual(leader1, 5)
        self.assertEqual(leader2, 5)

    def test_improved_uses_fewer_messages(self):
        alive = [True, True, True, True, True, False]
        (leader1, original_messages), (leader2, improved_messages) = run_both(2, alive)
        self.assertLess(improved_messages, original_messages)


# -------------------------------------------------
# 2. BESKEDTAL (håndudledte værdier + formel)
# -------------------------------------------------
class TestMessageCounts(unittest.TestCase):

    def test_hand_derived(self):
        cases = [  # (alive, s, leder, orig, forb)
            ([True] * 5 + [False], 2, 5, 20, 7),
            ([True, True, True, False, True, True, True, False, False, False], 2, 7, 42, 10),
            ([True, False, False, False], 1, 1, 3, 3),
            ([True] * 3, 1, 3, 8, 4),
            ([True] * 6, 2, 6, 25, 7),
            ([True], 1, 1, 0, 0),
            ([True] * 6, 6, 6, 5, 5),
        ]
        for alive, s, leader, orig, imp in cases:
            (lo, mo), (li, mi) = run_both(s, alive)
            self.assertEqual((lo, mo), (leader, orig), (alive, s))
            self.assertEqual((li, mi), (leader, imp), (alive, s))

    def test_random_vs_oracle(self):
        rng = random.Random(1)
        for _ in range(2000):
            n = rng.randint(1, 30)
            alive = [rng.random() > 0.4 for _ in range(n)]
            if not any(alive):
                continue
            s = rng.choice([i + 1 for i in range(n) if alive[i]])
            L, orig, imp = expected(s, alive)
            (lo, mo), (li, mi) = run_both(s, alive)
            self.assertEqual((lo, mo), (L, orig), (alive, s))
            self.assertEqual((li, mi), (L, imp), (alive, s))

    def test_improved_never_worse(self):
        rng = random.Random(2)
        for _ in range(2000):
            n = rng.randint(1, 30)
            alive = [rng.random() > 0.4 for _ in range(n)]
            if not any(alive):
                continue
            s = rng.choice([i + 1 for i in range(n) if alive[i]])
            (_, mo), (_, mi) = run_both(s, alive)
            self.assertLessEqual(mi, mo, (alive, s))

    def test_improved_independent_of_initiator(self):
        """Når L > s afhænger forbedret ikke af s."""
        alive = [True] * 8 + [False] * 2
        counts = {run_both(s, alive)[1][1] for s in range(1, 8)}
        self.assertEqual(len(counts), 1)

    def test_original_grows_with_lower_initiator(self):
        """Original er dyrere, jo lavere initiatoren er (worst case = P1)."""
        alive = [True] * 9 + [False]
        counts = [run_both(s, alive)[0][1] for s in range(1, 9)]
        self.assertEqual(counts, sorted(counts, reverse=True))

    def test_messages_are_nonnegative_ints(self):
        (_, mo), (_, mi) = run_both(2, [True, True, False])
        for m in (mo, mi):
            self.assertIsInstance(m, int)
            self.assertGreaterEqual(m, 0)


# -------------------------------------------------
# 3. BENCHMARK (lukket formel + forventet tabel)
# -------------------------------------------------
class TestBenchmark(unittest.TestCase):

    EXPECTED = {  # N: (orig = N^2 - N - 1, forb = N + 1, besparelse %)
        5: (19, 6, 68.42),
        10: (89, 11, 87.64),
        25: (599, 26, 95.66),
        50: (2449, 51, 97.92),
        100: (9899, 101, 98.98),
    }

    def test_closed_form_and_table(self):
        for n, (orig, imp, red) in self.EXPECTED.items():
            alive = [True] * (n - 1) + [False]
            (_, mo), (_, mi) = run_both(1, alive)
            self.assertEqual(mo, n * n - n - 1)
            self.assertEqual(mi, n + 1)
            self.assertEqual((mo, mi), (orig, imp))
            self.assertEqual(round((1 - mi / mo) * 100, 2), red)

    def test_savings_approach_one_hundred_percent(self):
        """Når N vokser, nærmer 1 - (N+1)/(N^2-N-1) sig 100% (1.0)."""
        alive = [True] * 499 + [False]
        (_, mo), (_, mi) = run_both(1, alive)
        self.assertAlmostEqual(1 - mi / mo, 1.0, places=2)


# -------------------------------------------------
# 3b. BIG-O SKALERING (tid / arbejde)
# -------------------------------------------------
class TestBigO(unittest.TestCase):

    def _measure_runtime(self, func, n, repeats):
        alive = [True] * n
        start = time.perf_counter()
        for _ in range(repeats):
            quiet(func, 1, alive)
        return time.perf_counter() - start

    def test_original_algorithm_scales_about_quadratically(self):
        """Når n dobles, skal original-bully grov omtrent 4x."""
        sizes = [40, 80, 160]
        times = [self._measure_runtime(bully_election, n, repeats=30) for n in sizes]

        for i in range(1, len(times)):
            ratio = times[i] / times[i - 1]
            self.assertGreater(ratio, 2.5, msg=(sizes[i], sizes[i - 1], ratio))
            self.assertLess(ratio, 8.0, msg=(sizes[i], sizes[i - 1], ratio))

    def test_improved_algorithm_scales_about_linearly(self):
        """Når n dobles, skal forbedret-bully grov omtrent 2x."""
        sizes = [40, 80, 160]
        times = [self._measure_runtime(improved_bully, n, repeats=200) for n in sizes]

        for i in range(1, len(times)):
            ratio = times[i] / times[i - 1]
            self.assertGreater(ratio, 1.4, msg=(sizes[i], sizes[i - 1], ratio))
            self.assertLess(ratio, 3.5, msg=(sizes[i], sizes[i - 1], ratio))


# -------------------------------------------------
# 4. UGYLDIGT INPUT
# -------------------------------------------------
class TestInvalidInput(unittest.TestCase):

    def test_dead_initiator(self):
        for f in (bully_election, improved_bully):
            with self.assertRaises(ValueError):
                quiet(f, 2, [True, False, False])

    def test_initiator_out_of_range(self):
        for f in (bully_election, improved_bully):
            for s in (0, 7):
                with self.assertRaises(ValueError):
                    quiet(f, s, [True] * 6)


# -------------------------------------------------
# EKSEMPEL + UDFØRELSE AF 26 UNIT TESTS
# -------------------------------------------------
if __name__ == "__main__":
    alive = [
        True,   # P1
        True,   # P2
        True,   # P3
        True,   # P4
        True,   # P5
        False   # P6 er crashed
    ]

    print("=========== ORIGINAL BULLY ===========")
    leader, messages = bully_election(2, alive)
    print("\nLeader:", leader)
    print("Antal beskeder:", messages, "\n")

    print("=========== FORBEDRET BULLY ===========")
    leader, messages = improved_bully(2, alive)
    print("\nLeader:", leader)
    print("Antal beskeder:", messages, "\n")

    print("=========== UNIT TESTS (26 TESTS) ===========")
    unittest.main(argv=[''], verbosity=2, exit=False)
