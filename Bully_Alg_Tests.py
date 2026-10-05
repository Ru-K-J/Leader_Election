import unittest
import random
import io
from contextlib import redirect_stdout


def quiet(f, *args):
    """Kør f uden print-output."""
    with redirect_stdout(io.StringIO()):
        return f(*args)


def run_both(s, alive):
    return quiet(bully_election, s, alive), quiet(improved_bully, s, alive)


def expected(s, alive):
    """Uafhængigt orakel: (leder, orig-beskeder, forb-beskeder). Kræver alive[s-1]."""
    n, A = len(alive), sum(alive)
    L = max(i + 1 for i, x in enumerate(alive) if x)
    if L > s:
        a = sum(alive[s:])  # levende i (s, n]
        return L, (n - s) + a + (n - L) + (A - 1), (n - L + 1) + 1 + (A - 1)
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
# 2. BESKEDTAL (håndudledte værdier + formel)
# -------------------------------------------------
class TestMessageCounts(unittest.TestCase):

    def test_hand_derived(self):
        cases = [  # (alive, s, leder, orig, forb)
            ([True] * 5 + [False], 2, 5, 12, 7),
            ([True, True, True, False, True, True, True, False, False, False], 2, 7, 20, 10),
            ([True, False, False, False], 1, 1, 3, 3),
            ([True] * 3, 1, 3, 6, 4),
            ([True] * 6, 2, 6, 13, 7),
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

    EXPECTED = {  # N: (orig, forb, besparelse %)
        5: (11, 6, 45.45),
        10: (26, 11, 57.69),
        25: (71, 26, 63.38),
        50: (146, 51, 65.07),
        100: (296, 101, 65.88),
    }

    def test_closed_form_and_table(self):
        for n, (orig, imp, red) in self.EXPECTED.items():
            alive = [True] * (n - 1) + [False]
            (_, mo), (_, mi) = run_both(1, alive)
            self.assertEqual(mo, 3 * n - 4)
            self.assertEqual(mi, n + 1)
            self.assertEqual((mo, mi), (orig, imp))
            self.assertEqual(round((1 - mi / mo) * 100, 2), red)

    def test_savings_approach_two_thirds(self):
        alive = [True] * 999 + [False]
        (_, mo), (_, mi) = run_both(1, alive)
        self.assertAlmostEqual(1 - mi / mo, 2 / 3, places=2)


# -------------------------------------------------
# 4. UGYLDIGT INPUT (kræver guard i algoritmerne)
# -------------------------------------------------
# Tilføj først i begge funktioner:
#   if not (1 <= start_process <= len(alive)) or not alive[start_process - 1]:
#       raise ValueError("start_process skal være en levende proces i 1..N")
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
# UDFØRELSE (Jupyter-sikker)
# -------------------------------------------------
unittest.main(argv=[''], verbosity=2, exit=False)