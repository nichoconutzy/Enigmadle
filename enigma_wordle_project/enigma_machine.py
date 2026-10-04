from collections.abc import Mapping
from math import factorial

from enigma_constants import ALPHABET, ROTOR_SPECS, REFLECTOR_B


def _letters(value, length, label):
    if not isinstance(value, str):
        raise ValueError(f'{label} requires {length} letters A-Z.')
    value = value.upper()
    if len(value) != length or any(c not in ALPHABET for c in value):
        raise ValueError(f'{label} requires {length} letters A-Z.')
    return value


def _triple(value, label):
    if isinstance(value, str):
        value = value.split() if any(c.isspace() for c in value) else list(value)
    try:
        values = tuple(value)
    except TypeError as exc:
        raise ValueError(f'{label} requires three letters.') from exc
    if len(values) != 3:
        raise ValueError(f'{label} requires three letters.')
    return tuple(_letters(c, 1, label) for c in values)


def _order(value):
    if isinstance(value, str):
        value = value.split()
    try:
        names = tuple(str(c).upper() for c in value)
    except TypeError as exc:
        raise ValueError('Choose three distinct rotors from I-V.') from exc
    if len(names) != 3 or len(set(names)) != 3 or any(n not in ROTOR_SPECS for n in names):
        raise ValueError('Choose three distinct rotors from I-V.')
    return names


def _plugboard(pairs):
    """Accept 'AB CD', 'A-B C-D', a list, or a one-way/symmetric mapping."""
    mapping = {}
    if pairs is None:
        pairs = []
    if isinstance(pairs, Mapping):
        for a, b in pairs.items():
            a, b = _letters(a, 1, 'Plugboard'), _letters(b, 1, 'Plugboard')
            if a == b or (a in mapping and mapping[a] != b) or (b in mapping and mapping[b] != a):
                raise ValueError('Each cable must join two different, unused letters.')
            mapping[a], mapping[b] = b, a
    else:
        if isinstance(pairs, str):
            pairs = pairs.split()
        try:
            pairs = list(pairs)
        except TypeError as exc:
            raise ValueError('Use plugboard pairs such as A-B X-Y.') from exc
        for pair in pairs:
            if not isinstance(pair, str):
                raise ValueError('Use plugboard pairs such as A-B X-Y.')
            if len(pair) == 3 and pair[1] == '-':
                pair = pair[0] + pair[2]
            a, b = _letters(pair, 2, 'Plugboard pair')
            if a == b or a in mapping or b in mapping:
                raise ValueError('Each cable must join two different, unused letters.')
            mapping[a], mapping[b] = b, a
    if len(mapping) > 20:
        raise ValueError('This simulator supports at most ten plugboard cables.')
    return mapping


def plugboard_combinations(pair_count=10):
    if type(pair_count) is not int or not 0 <= pair_count <= 10:
        raise ValueError('Pair count must be an integer from 0 to 10.')
    return factorial(26) // (factorial(26 - 2 * pair_count) * factorial(pair_count) * 2**pair_count)


QUOTED_KEYSPACE = 60 * 26**3 * plugboard_combinations(10)


class EnigmaMachine:
    """Reciprocal three-rotor Enigma I using reflector B.

    Legacy GUI calls still work. 'rotors' means window positions; rotor_order
    selects the actual rotor identities. Encryption advances the windows.
    Reset to the same starting windows before decrypting the same message.
    Punctuation passes through without stepping; non-ASCII letters fail.
    """
    def __init__(self, rotors=('A', 'A', 'A'), plugboard=None,
                 rotor_order=('I', 'II', 'III'), ring_settings=('A', 'A', 'A')):
        self.set_rotor_order(rotor_order)
        self.set_ring_settings(ring_settings)
        self.set_windows(rotors)
        self.set_plugboard(plugboard)

    @property
    def windows(self):
        return ''.join(ALPHABET[p] for p in self.rotors)

    def set_windows(self, windows):
        letters = _triple(windows, 'Windows')
        self.rotors = [ALPHABET.index(c) for c in letters]
        self._initial_windows = letters

    def set_rotors(self, r1, r2, r3):
        self.set_windows((r1, r2, r3))

    def reset(self, windows=None):
        self.set_windows(self._initial_windows if windows is None else windows)

    def set_rotor_order(self, rotor_order):
        names = _order(rotor_order)
        forward, inverse = [], []
        for name in names:
            wiring = [ALPHABET.index(c) for c in ROTOR_SPECS[name][0]]
            backward = [0] * 26
            for i, out in enumerate(wiring):
                backward[out] = i
            forward.append(wiring)
            inverse.append(backward)
        self.rotor_order = names
        self._forward, self._inverse = forward, inverse

    def set_ring_settings(self, ring_settings):
        self.ring_settings = tuple(ALPHABET.index(c) for c in _triple(ring_settings, 'Rings'))

    def set_plugboard(self, pairs):
        # Validate completely before replacing the previous configuration.
        self.plugboard = _plugboard(pairs)

    def copy(self):
        return EnigmaMachine(self.windows, self.plugboard, self.rotor_order,
                             tuple(ALPHABET[p] for p in self.ring_settings))

    def _step(self):
        # Test notches BEFORE stepping. Notches are fixed to the index ring;
        # changing ring settings does not change the visible turnover letter.
        middle = ALPHABET[self.rotors[1]] == ROTOR_SPECS[self.rotor_order[1]][1]
        right = ALPHABET[self.rotors[2]] == ROTOR_SPECS[self.rotor_order[2]][1]
        if middle:
            self.rotors[0] = (self.rotors[0] + 1) % 26
        if middle or right:
            self.rotors[1] = (self.rotors[1] + 1) % 26
        self.rotors[2] = (self.rotors[2] + 1) % 26

    def _through_rotor(self, number, index, reverse=False):
        offset = self.rotors[index] - self.ring_settings[index]
        wiring = self._inverse[index] if reverse else self._forward[index]
        return (wiring[(number + offset) % 26] - offset) % 26

    def encrypt_char(self, char):
        if not isinstance(char, str) or len(char) != 1:
            raise ValueError('encrypt_char requires one character.')
        original, char = char, char.upper()
        if len(char) != 1 or char not in ALPHABET:
            if original.isalpha():
                raise ValueError('Enigma accepts only letters A-Z.')
            return original
        self._step()
        number = ALPHABET.index(self.plugboard.get(char, char))
        for index in (2, 1, 0):
            number = self._through_rotor(number, index)
        number = ALPHABET.index(REFLECTOR_B[number])
        for index in (0, 1, 2):
            number = self._through_rotor(number, index, reverse=True)
        out = ALPHABET[number]
        return self.plugboard.get(out, out)

    def encrypt_string(self, text):
        if not isinstance(text, str):
            raise ValueError('Message must be text.')
        # Validate before any rotor movement.
        for c in text:
            if c.isalpha() and (len(c.upper()) != 1 or c.upper() not in ALPHABET):
                raise ValueError('Enigma accepts only letters A-Z.')
        return ''.join(self.encrypt_char(c) for c in text)

    def send_message(self, plaintext, open_group, message_key):
        """Compatibility shortcut for message_protocol.send_message()."""
        from message_protocol import send_message
        return send_message(self, plaintext, open_group, message_key)

    def receive_message(self, transmission):
        """Compatibility shortcut for message_protocol.receive_message()."""
        from message_protocol import receive_message
        return receive_message(self, transmission)
