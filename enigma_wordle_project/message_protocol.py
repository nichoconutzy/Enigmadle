from dataclasses import dataclass

from enigma_machine import _letters, _triple


@dataclass(frozen=True)
class Transmission:
    open_group: str
    indicator: str
    ciphertext: str

    def __post_init__(self):
        object.__setattr__(self, 'open_group', _letters(self.open_group, 3, 'Open group'))
        object.__setattr__(self, 'indicator', _letters(self.indicator, 3, 'Indicator'))
        if not isinstance(self.ciphertext, str):
            raise ValueError('Ciphertext must be text.')


def send_message(machine, plaintext, open_group, message_key):
    """Encrypt the key at the open group, then reset to it for the body.

    Work on a copy so repeat attempts never alter the caller's windows.
    Only the open group, encrypted indicator, and body are transmitted.
    """
    open_group = ''.join(_triple(open_group, 'Open group'))
    message_key = ''.join(_triple(message_key, 'Message key'))
    worker = machine.copy()
    worker.set_windows(open_group)
    indicator = worker.encrypt_string(message_key)
    worker.set_windows(message_key)
    return Transmission(open_group, indicator, worker.encrypt_string(plaintext))


def receive_message(machine, transmission):
    """Recover the key at the open group, reset to it, and decode the body."""
    if not isinstance(transmission, Transmission):
        raise ValueError('Expected a Transmission object.')
    worker = machine.copy()
    worker.set_windows(transmission.open_group)
    message_key = worker.encrypt_string(transmission.indicator)
    worker.set_windows(message_key)
    return worker.encrypt_string(transmission.ciphertext)
