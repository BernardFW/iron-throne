import json
from os import (
    path,
)
from typing import (
    Text,
)

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
)
from iron_throne.pretenders import (
    Expression,
    ExpressionPretender,
)

expressions = [
    Expression('LA ROCHELLE', 'city', 'la-rochelle'),
]

PHRASE_1 = 'activity in La Rochelle'
CITIES_FILE = path.join(
    path.dirname(__file__),
    'assets/cities_france.json',
)


def make_city_expressions():
    """
    Generates a list of city expressions from the cities DB of La Poste.
    """

    aliases = {}

    def expand(name, entity):
        yield Expression(name, 'city', entity)

        if 'ST ' in name:
            yield Expression(
                name.replace('ST ', 'SAINT '),
                'city',
                entity,
            )
        elif 'STE ' in name:
            yield Expression(
                name.replace('STE ', 'SAINTE '),
                'city',
                entity,
            )

        for a in aliases.get(name, []):
            yield from expand(a, entity)

    with open(CITIES_FILE, 'r', encoding='utf-8') as f:
        for city in json.load(f):
            try:
                name: Text = city['fields']['nom_de_la_commune']
                alias: Text = city['fields']['libell_d_acheminement']
                zip_code: Text = city['fields']['code_postal']
            except KeyError:
                pass
            else:
                entity = f'{zip_code}/{name}'
                yield from expand(name, entity)

                if alias != name:
                    yield from expand(alias, entity)


def test_la_rochelle_simple():
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
            entity='city',
            value='la-rochelle',
            score=1.,
            length=2,
            seq=0,
        ),
    ]
    assert score == 1.


def test_la_rochelle_full():
    i = IronThrone([
        ExpressionPretender(list(make_city_expressions())),
    ], [
        FullMatches(),
        LargestClaim(),
        ClaimScores(),
    ])

    entities, score = i.get_entities(PHRASE_1)

    assert score == 1.
    assert [c.value for c in entities] == ['17000/LA ROCHELLE']
