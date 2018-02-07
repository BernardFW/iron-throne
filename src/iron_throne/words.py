import re
from typing import (
    TYPE_CHECKING,
    Iterator,
    List,
    Text,
)

from iron_throne.trigram import (
    Trigram,
)

from .trigram import (
    normalize,
)

if TYPE_CHECKING:
    from .claim import Proof


def tokenize(text: Text) -> Iterator['Word']:
    """
    Transform a string into a bunch of words. Those words can get an expression
    attached if required.
    """

    for order, word in enumerate(re.split(r'\W+', text)):
        yield Word(word, order)


class Word(object):
    """
    A word is a single of text. If it is part of an expression, it gets both
    the expression and an order of occurrence within this expression.
    """

    def __init__(self,
                 text: Text,
                 order: int=0):
        self.text = text
        self.order = order
        self.proofs: List['Proof'] = []

        self._norm = normalize(text)
        self._trigram = Trigram(text)

    def __hash__(self):
        return hash(self.text)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.text == other.text

    def __repr__(self):
        return f'Word<{self.text}>'

    @property
    def trigram(self):
        return self._trigram

    @property
    def trigrams(self):
        """
        Trigrams of the word are automatically generated at init so there you
        can only access them read-only.
        """

        # noinspection PyProtectedMember
        return self._trigram._trigrams

    @property
    def normalized(self):
        return self._norm
