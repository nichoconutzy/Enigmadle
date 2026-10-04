from dataclasses import dataclass
import random

from enigma_constants import ALPHABET, ROTOR_SPECS
from enigma_machine import EnigmaMachine, _order, _triple, _plugboard, plugboard_combinations
from message_protocol import Transmission, send_message
from word_bank import load_valid_words
from wordle import WordleGame


@dataclass(frozen=True)
class DailyKey:
    rotor_order: tuple = ('I', 'II', 'III')
    ring_settings: tuple = ('A', 'A', 'A')
    plugboard_pairs: tuple = ()

    def __post_init__(self):
        object.__setattr__(self, 'rotor_order', _order(self.rotor_order))
        object.__setattr__(self, 'ring_settings', _triple(self.ring_settings, 'Rings'))
        mapping = _plugboard(self.plugboard_pairs)
        pairs = tuple(a + mapping[a] for a in sorted(mapping) if a < mapping[a])
        object.__setattr__(self, 'plugboard_pairs', pairs)

    def machine(self, windows='AAA'):
        return EnigmaMachine(windows, self.plugboard_pairs, self.rotor_order, self.ring_settings)


def random_daily_key(pair_count=10, randomize_rings=False, rng=None):
    """Sample directly, without enumerating or storing the huge keyspace.

    Fixed AAA rings plus ten pairs match QUOTED_KEYSPACE assumptions.
    Supply random.Random(seed) for reproducible coursework demonstrations.
    """
    plugboard_combinations(pair_count)
    rng = rng if rng is not None else random.SystemRandom()
    letters = rng.sample(ALPHABET, 2 * pair_count)
    pairs = tuple(letters[i] + letters[i + 1] for i in range(0, len(letters), 2))
    rings = tuple(rng.choice(ALPHABET) for _ in range(3)) if randomize_rings else tuple('AAA')
    return DailyKey(tuple(rng.sample(tuple(ROTOR_SPECS), 3)), rings, pairs)


@dataclass(frozen=True)
class Puzzle:
    """Internal puzzle data; the interface displays the key and transmission."""
    target_word: str
    daily_key: DailyKey
    transmission: Transmission
    allowed_words: tuple

    def new_wordle_game(self):
        """Create a fresh guessing round using this puzzle's vocabulary."""
        return WordleGame(self.target_word, self.transmission.ciphertext, self.allowed_words)


def create_puzzle(words=None, pair_count=10, randomize_rings=False, rng=None):
    """Generate the same kind of puzzle for GUI and terminal callers.

    Ten plugboard cables and fixed AAA rings match the quoted keyspace.
    Pass random.Random(seed) when a repeatable demonstration is needed.
    """
    rng = rng if rng is not None else random.SystemRandom()
    words = tuple(load_valid_words(words))
    target = rng.choice(words)
    daily_key = random_daily_key(pair_count, randomize_rings, rng)
    open_group = ''.join(rng.choice(ALPHABET) for _ in range(3))
    message_key = ''.join(rng.choice(ALPHABET) for _ in range(3))
    packet = send_message(daily_key.machine(), target, open_group, message_key)
    return Puzzle(target, daily_key, packet, words)
