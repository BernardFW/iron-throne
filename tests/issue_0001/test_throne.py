from iron_throne import (
    IronThrone,
)
from iron_throne.claim import (
    Claim,
)
from iron_throne.constraints import (
    ClaimScores,
    FullMatches,
    LargestClaim,
    NoTwice,
)
from iron_throne.pretenders import (
    Expression,
    ExpressionPretender,
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


def test_case_1():
    i = IronThrone([
        ExpressionPretender(expressions),
    ], [
        NoTwice(),
        FullMatches(),
        LargestClaim(),
        ClaimScores(),
    ])

    entities, score = i.get_entities('I like potato salad')

    assert entities == [
        Claim(
            entity='food',
            value='potato-salad',
            score=1.,
            length=2,
            seq=1,
        ),
    ]
    assert score == 1.
