class WordleGame:
    def __init__(self, target_word, ciphertext):
        self.target_word = target_word.upper()
        self.ciphertext = ciphertext.upper()
        self.guesses = []
        self.max_guesses = 6

    def evaluate_guess(self, guess):
        guess = guess.upper()
        if len(guess) != 5:
            return None, "Error: Word must be exactly 5 letters."
        
        feedback = ['⬛'] * 5
        target_chars = list(self.target_word)
        guess_chars = list(guess)
        
        # Check greens
        for i in range(5):
            if guess_chars[i] == target_chars[i]:
                feedback[i] = '🟩'
                target_chars[i] = None
                guess_chars[i] = None

        # Check yellows
        for i in range(5):
            if guess_chars[i] is not None:
                if guess_chars[i] in target_chars:
                    feedback[i] = '🟨'
                    target_chars[target_chars.index(guess_chars[i])] = None
                else:
                    feedback[i] = '⬛'
                    
        return "".join(feedback), None