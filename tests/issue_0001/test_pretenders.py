from typing import (
    List,
)

from iron_throne.claim import (
    Claim,
    Proof,
)
from iron_throne.pretenders import (
    Expression,
    ExpressionMatch,
    ExpressionPretender,
)
from iron_throne.words import (
    Word,
)

expressions = [
    Expression('salad', 'food', 'salad'),
    Expression('potato salad', 'food', 'potato-salad'),
    Expression('cheese', 'food', 'cheese'),
    Expression('ham', 'food', 'ham'),

    Expression('turtle', 'animal', 'turtle'),
    Expression('fox', 'animal', 'fox'),
    Expression('elephant', 'animal', 'elephant'),
]


def test_ep_index():
    ep = ExpressionPretender(expressions)
    assert ep.index[(' ', ' ', 'c')] == [
        ExpressionMatch(
            expression=expressions[2],
            word=Word('cheese'),
            seq=2,
            order=0,
        )
    ]


def test_claim_words():
    words: List[Word] = [
        Word('elephant'),
        Word('eats'),
        Word('potato'),
        Word('salad'),
    ]

    ep = ExpressionPretender(expressions)
    ep.claim(words)

    elephant, eats, potato, salad = words

    assert elephant.proofs == [
        Proof(
            claim=Claim(
                entity='animal',
                value='elephant',
                length=1,
                score=1.0,
                seq=6,
            ),
            order=0,
            score=1.,
            word=Word('elephant'),
        ),
    ]

    assert set(salad.proofs) == {
        Proof(
            claim=Claim(
                entity='food',
                value='salad',
                length=1,
                score=1.0,
                seq=0,
            ),
            order=0,
            score=1.,
            word=Word('salad'),
        ),
        Proof(
            claim=Claim(
                entity='food',
                value='potato-salad',
                length=2,
                score=1.0,
                seq=1,
            ),
            order=1,
            score=1.,
            word=Word('salad'),
        ),
    }
