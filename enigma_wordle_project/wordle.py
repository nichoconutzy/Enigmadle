import string


GREEN = '🟩'
YELLOW = '🟨'
GREY = '⬛'
WORD_LENGTH = 5
MAX_GUESSES = 3


def _normalize_word(value, label):
    """Accept ASCII letters only, allowing lowercase and surrounding space."""
    if not isinstance(value, str):
        raise ValueError(f'{label} must be text.')
    value = value.strip()
    if len(value) != WORD_LENGTH or any(c not in string.ascii_letters for c in value):
        raise ValueError(f'{label} must be exactly five letters A-Z.')
    return value.upper()


class WordleGame:

    def __init__(self, target_word, ciphertext, allowed_words=None):
        self.target_word = _normalize_word(target_word, 'Target word')
        self.ciphertext = _normalize_word(ciphertext, 'Ciphertext')
        self.max_guesses = MAX_GUESSES
        self.guesses = []

        if allowed_words is None:
            from word_bank import ENGLISH_WORDS
            allowed_words = ENGLISH_WORDS
        if isinstance(allowed_words, (str, bytes)):
            raise ValueError('Word bank must be a collection of words.')

        # Filter malformed entries in the current bank and remove duplicates.
        # Spelling mistakes that are five ASCII letters still need manual review.
        cleaned = set()
        try:
            entries = iter(allowed_words)
        except TypeError as error:
            raise ValueError('Word bank must be a collection of words.') from error
        for entry in entries:
            try:
                cleaned.add(_normalize_word(entry, 'Word bank entry'))
            except ValueError:
                continue
        if not cleaned:
            raise ValueError('The word bank has no valid five-letter words.')
        self.allowed_words = frozenset(cleaned)
        if self.target_word not in self.allowed_words:
            raise ValueError('Target word must be in the word bank.')

    @property
    def won(self):
        return any(word == self.target_word for word, _ in self.guesses)

    @property
    def game_over(self):
        return self.won or len(self.guesses) >= self.max_guesses

    @property
    def remaining_guesses(self):
        return max(0, self.max_guesses - len(self.guesses))

    def evaluate_guess(self, guess):
        """Return (emoji_feedback, None) or (None, error), without recording.

        Exact matches consume letters first. Misplaced matches consume only
        the remaining occurrences, so repeated letters cannot score twice.
        """
        if self.game_over:
            return None, 'This game has already ended. Start a new game.'
        try:
            guess = _normalize_word(guess, 'Guess')
        except ValueError as error:
            return None, str(error)
        if guess not in self.allowed_words:
            return None, 'Guess must be in the word bank.'

        feedback = [GREY] * WORD_LENGTH
        remaining = list(self.target_word)
        for index, letter in enumerate(guess):
            if letter == self.target_word[index]:
                feedback[index] = GREEN
                remaining[index] = None
        for index, letter in enumerate(guess):
            if feedback[index] != GREEN and letter in remaining:
                feedback[index] = YELLOW
                remaining[remaining.index(letter)] = None
        return ''.join(feedback), None

    def submit_guess(self, guess):
        """Evaluate and record one valid attempt; return the same result format."""
        feedback, error = self.evaluate_guess(guess)
        if error is None:
            self.guesses.append((_normalize_word(guess, 'Guess'), feedback))
        return feedback, error
