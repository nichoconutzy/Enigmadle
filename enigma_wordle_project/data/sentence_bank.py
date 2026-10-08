"""Add sentences here only. Target positions count words from zero."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SentenceSpec:
    title: str
    sentence: str
    target_positions: tuple
    briefing: str

    def __post_init__(self):
        words = self.sentence.upper().split()
        if not words or any(not word.isascii() or not word.isalpha() for word in words):
            raise ValueError('Sentences must contain only words A-Z separated by spaces.')
        positions = tuple(self.target_positions)
        if not positions or len(set(positions)) != len(positions) or any(
                type(i) is not int or not 0 <= i < len(words) for i in positions):
            raise ValueError('Target positions must be unique valid word indices.')
        object.__setattr__(self, 'sentence', ' '.join(words))
        object.__setattr__(self, 'target_positions', positions)

    @property
    def answers(self):
        words = self.sentence.split()
        return tuple(words[i] for i in self.target_positions)

    @property
    def masked_sentence(self):
        return ' '.join(f'[{self.target_positions.index(i) + 1}: {len(word)} letters]'
                        if i in self.target_positions else word
                        for i, word in enumerate(self.sentence.split()))


SENTENCES = (
    SentenceSpec('Bridge watch', 'GUARDS WATCH THE BRIDGE AT DAWN', (1, 3),
                 'Recover the action and the location from the intercepted report.'),
    SentenceSpec('Supply route', 'SUPPLY TRUCKS ARRIVE BEFORE SUNRISE', (1, 4),
                 'Identify the transport and its arrival deadline.'),
    SentenceSpec('Coastal signal', 'SEND THE SIGNAL AFTER THE SHIPS DEPART', (2, 5),
                 'Recover what must be sent and which vessels are mentioned.'),
    SentenceSpec('Night patrol', 'THE PATROL MOVES THROUGH THE FOREST TONIGHT', (1, 5),
                 'Identify the unit and its route.'),
)
