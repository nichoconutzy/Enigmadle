"""Sentence rounds use the existing daily key and message protocol."""
import random
from dataclasses import dataclass
from core.enigma_constants import ALPHABET
from core.message_protocol import send_message
from data.sentence_bank import SENTENCES
from game.puzzle import random_daily_key


@dataclass(frozen=True)
class SentencePuzzle:
    spec: object
    daily_key: object
    transmission: object
    known_pairs: tuple
    missing_pair_letter: str


def create_sentence_puzzle(rng=None):
    rng = rng if rng is not None else random.SystemRandom()
    spec = rng.choice(SENTENCES)
    key = random_daily_key(pair_count=4, randomize_rings=True, rng=rng)
    open_group = ''.join(rng.choice(ALPHABET) for _ in range(3))
    message_key = ''.join(rng.choice(ALPHABET) for _ in range(3))
    packet = send_message(key.machine(), spec.sentence.replace(' ', ''), open_group, message_key)
    return SentencePuzzle(spec, key, packet, key.plugboard_pairs[:-1], key.plugboard_pairs[-1][0])


class SentenceRound:
    max_attempts = 6

    def __init__(self, puzzle):
        self.puzzle = puzzle
        self.attempts = 0
        self.solved = [False] * len(puzzle.spec.answers)

    @property
    def won(self):
        return all(self.solved)

    @property
    def game_over(self):
        return self.won or self.attempts >= self.max_attempts

    def submit(self, values):
        if self.game_over:
            raise ValueError('This round has ended.')
        if len(values) != len(self.solved):
            raise ValueError('Fill every answer field.')
        cleaned = [v.strip().upper() for v in values]
        for i, (value, answer) in enumerate(zip(cleaned, self.puzzle.spec.answers)):
            if not self.solved[i] and (len(value) != len(answer) or not value.isascii() or not value.isalpha()):
                raise ValueError(f'Answer {i + 1} needs {len(answer)} letters A-Z.')
        self.attempts += 1
        for i, (value, answer) in enumerate(zip(cleaned, self.puzzle.spec.answers)):
            self.solved[i] = self.solved[i] or value == answer
        return tuple(self.solved)
