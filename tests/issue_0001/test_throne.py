from itertools import (
    product,
)

from iron_throne import (
    IronThrone,
)
from iron_throne.claim import (
    Claim,
)
from iron_throne.constraints import (
    AllowedSets,
    ClaimScores,
    EntitySet,
    FullMatches,
    LargestClaim,
)
from iron_throne.pretenders import (
    Expression,
    ExpressionPretender,
)
from iron_throne.tourney import (
    IronThroneSolver,
)
from iron_throne.words import (
    tokenize,
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

PHRASE_1 = 'I like potato salad'


def test_largest_claim():
    words = list(tokenize(PHRASE_1))
    ExpressionPretender(expressions).claim(words)

    potato_idx = None
    salad_idx = None
    bad_salad_idx = None

    for idx, proof in enumerate(words[2].proofs):
        if proof.claim.value == 'potato-salad':
            potato_idx = idx

    for idx, proof in enumerate(words[3].proofs):
        if proof.claim.value == 'potato-salad':
            salad_idx = idx

    for idx, proof in enumerate(words[3].proofs):
        if proof.claim.value == 'salad':
            bad_salad_idx = idx

    assert potato_idx is not None
    assert salad_idx is not None
    assert bad_salad_idx is not None

    solver = IronThroneSolver(words, [LargestClaim()])

    solver.state = [None, None, None, None]
    assert solver.energy() == 4.0

    solver.state = [None, None, potato_idx, salad_idx]
    assert solver.energy() == 2.0

    solver.state = [None, None, None, bad_salad_idx]
    assert solver.energy() == 4.0


def test_claim_scores():
    words = list(tokenize(PHRASE_1))
    ExpressionPretender(expressions).claim(words)

    potato_idx = None
    salad_idx = None
    bad_salad_idx = None

    for idx, proof in enumerate(words[2].proofs):
        if proof.claim.value == 'potato-salad':
            potato_idx = idx

    for idx, proof in enumerate(words[3].proofs):
        if proof.claim.value == 'potato-salad':
            salad_idx = idx

    for idx, proof in enumerate(words[3].proofs):
        if proof.claim.value == 'salad':
            bad_salad_idx = idx

    assert potato_idx is not None
    assert salad_idx is not None
    assert bad_salad_idx is not None

    solver = IronThroneSolver(words, [ClaimScores()])

    solver.state = [None, None, None, None]
    assert solver.energy() == 20.

    solver.state = [None, None, potato_idx, salad_idx]
    assert solver.energy() == 10.

    solver.state = [None, None, None, bad_salad_idx]
    assert solver.energy() == 15.


def test_full_matches():
    words = list(tokenize(PHRASE_1))
    ExpressionPretender(expressions).claim(words)

    potato_idx = None
    salad_idx = None
    bad_salad_idx = None

    for idx, proof in enumerate(words[2].proofs):
        if proof.claim.value == 'potato-salad':
            potato_idx = idx

    for idx, proof in enumerate(words[3].proofs):
        if proof.claim.value == 'potato-salad':
            salad_idx = idx

    for idx, proof in enumerate(words[3].proofs):
        if proof.claim.value == 'salad':
            bad_salad_idx = idx

    assert potato_idx is not None
    assert salad_idx is not None
    assert bad_salad_idx is not None

    solver = IronThroneSolver(words, [FullMatches()])

    solver.state = [None, None, None, None]
    assert solver.energy() == 0.

    solver.state = [None, None, potato_idx, salad_idx]
    assert solver.energy() == 0.

    solver.state = [None, None, None, salad_idx]
    assert solver.energy() == 10.

    solver.state = [None, None, potato_idx, None]
    assert solver.energy() == 10.


def test_allowed_sets():
    words = list(tokenize('salad turtle'))
    ExpressionPretender(expressions).claim(words)

    solver = IronThroneSolver(words, [AllowedSets([
        EntitySet(0, {'food'}, set()),
    ])])
    solver.configure()

    solver.state = [None, None]
    assert solver.energy() == 0.

    solver.state = [0, None]
    assert solver.energy() == 0.

    solver.state = [0, 0]
    assert solver.energy() == 10.


def test_energy_scoring():
    i = IronThrone([
        ExpressionPretender(expressions),
    ], [
        FullMatches(),
        LargestClaim(),
        ClaimScores(),
    ])

    words = list(tokenize(PHRASE_1))

    for pretender in i.pretenders:
        pretender.claim(words)

    solver = IronThroneSolver(words, i.constraints)
    potato_idx = None
    salad_idx = None

    for idx, proof in enumerate(words[2].proofs):
        if proof.claim.value == 'potato-salad':
            potato_idx = idx

    for idx, proof in enumerate(words[3].proofs):
        if proof.claim.value == 'potato-salad':
            salad_idx = idx

    assert potato_idx is not None
    assert salad_idx is not None

    def score_options():
        indices = [
            [None] + list(range(0, len(word.proofs)))
            for word in words
        ]

        for state in product(*indices):
            solver.state = state
            yield solver.energy(), state

    energy, best_state = min(score_options(), key=lambda x: x[0])

    assert energy == 12.
    assert best_state == (None, None, potato_idx, salad_idx)


def test_case_1():
    i = IronThrone([
        ExpressionPretender(expressions),
    ], [
        FullMatches(),
        LargestClaim(),
        ClaimScores(),
    ])

    entities, score = i.get_entities(PHRASE_1)

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


def test_case_2():
    i = IronThrone([
        ExpressionPretender(expressions),
    ], [
        FullMatches(),
        LargestClaim(),
        ClaimScores(),
        AllowedSets([
            EntitySet(0, {'food'}, set()),
        ]),
    ])

    entities, score = i.get_entities('salad turtle')

    assert entities == [
        Claim(
            entity='food',
            value='salad',
            score=1.,
            length=1,
            seq=0,
        ),
    ]
    assert score == 1.
