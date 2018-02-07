from typing import (
    Any,
    List,
    Text,
)

from .words import (
    Word,
)


class Claim(object):
    """
    Claim made on a word by a pretender. It means that the pretender thinks
    this word is his.
    """

    def __init__(self,
                 entity: Text,
                 value: Any,
                 score: float,
                 length: int,
                 seq: int) -> None:
        """
        Constructs the claim

        :param entity: Name of the claimed entity ("wine color")
        :param value: Value of the claimed entity ("red")
        :param score: Score from 0 to 1 of the confidence in this claim
        :param length: Number of words concerned by this claim
        :param seq: A sequence number unique for this entity
        """

        self.entity = entity
        self.value = value
        self.score = score
        self.length = length
        self.seq = seq
        self.proofs: List['Proof'] = []

    def __repr__(self):
        return f'Claim<{self.entity}={self.value} {self.score}>'

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
               and self.entity == other.entity \
               and self.value == other.value \
               and self.score == other.score \
               and self.length == other.length \
               and self.seq == other.seq

    def __hash__(self):
        return hash(self.id)

    @property
    def id(self):
        return f'{self.entity}#{self.seq}'


class Proof(object):
    def __init__(self, order: int, claim: Claim, word: Word, score: float):
        self.order = order
        self.claim = claim
        self.word = word
        self.score = score

    @classmethod
    def attach(cls, order: int, claim: Claim, word: Word, score: float) \
            -> 'Proof':
        o = cls(order, claim, word, score)
        claim.proofs.append(o)
        word.proofs.append(o)

        return o

    def __eq__(self, other):
        return self.__class__ == other.__class__ \
            and self.order == other.order \
            and self.claim == other.claim \
            and self.word == other.word \
            and self.score == other.score

    def __hash__(self):
        return hash(self.order) \
               ^ hash(self.claim) \
               ^ hash(self.word)

    def __repr__(self):
        return f'<Proof {self.claim}#{self.order} {self.word} {self.score}>'
