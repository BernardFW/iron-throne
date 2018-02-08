from collections import (
    defaultdict,
)
from typing import (
    Any,
    Dict,
    Iterator,
    List,
    NamedTuple,
    Optional,
    Text,
    Tuple,
)

from iron_throne.claim import (
    Proof,
)

from .claim import (
    Claim,
)
from .words import (
    Word,
    tokenize,
)


class Pretender(object):
    """
    What if I say I'm not like the others?

    A pretender is an object capable of claiming words within a list of words.
    """

    def claim(self, words: List['Word']) -> None:
        """
        Iterate the list of words in order to claim them. Claimed words will
        get a claim appended to their claims list.
        """
        raise NotImplementedError


class Expression(object):
    """
    Several words that come together. Like a wine name or multi-word color
    name.
    """

    def __init__(self, text: Text, entity: Text, value: Any):
        self.text = text
        self.entity = entity
        self.value = value

        self._words = list(tokenize(text))

    def __hash__(self):
        return hash(self.text) ^ hash(self.entity) ^ hash(self.value)

    def __eq__(self, other):
        return self.text == other.text and \
               self.entity == other.entity and \
               self.value == other.value

    def __repr__(self):
        return f'Expression<{self.entity}={self.value} "{self.text}">'

    @property
    def words(self) -> List['Word']:
        """
        Provide a read-only access to the words list, because it is generated
        automatically at init.
        """

        return self._words


class ExpressionMatch(NamedTuple):
    expression: Expression
    word: Word
    seq: int
    order: int


TrigramIndex = Dict[
    Tuple[Optional[Text], Optional[Text], Optional[Text]],
    List[ExpressionMatch]
]


class ExpressionPretender(Pretender):
    MIN_SCORE = .6

    def __init__(self, expressions: List[Expression], seq: int = 0):
        self.expressions = expressions
        self.seq = seq

        self.index: TrigramIndex = self.build_index()

    def build_index(self) -> TrigramIndex:
        index: TrigramIndex = defaultdict(lambda: [])

        for seq, expression in enumerate(self.expressions):
            for order, word in enumerate(expression.words):
                for t in word.trigrams:
                    index[t].append(ExpressionMatch(
                        expression,
                        word,
                        self.seq + seq,
                        order,
                    ))

        return index

    def claim_word(self, word: Word, claims: Dict[Expression, Claim]) -> None:
        matches: Dict[ExpressionMatch, int] = defaultdict(lambda: 0)
        len2 = float(len(word.trigrams))

        for t in word.trigrams:
            for match in self.index[t]:
                matches[match] += 1

        def compute_scores() -> Iterator[Tuple[ExpressionMatch, float]]:
            for m, count in matches.items():
                count = float(count)
                len1 = float(len(m.word.trigrams))
                s = count / (len1 + len2 - count)

                if s > self.MIN_SCORE:
                    yield m, s

        for match, score in compute_scores():
            claim = self.get_claim(claims, match)
            Proof.attach(
                order=match.order,
                claim=claim,
                word=word,
                score=score,
            )

    def get_claim(self,
                  claims: Dict[Expression, Claim],
                  match: ExpressionMatch) -> Claim:
        if match.expression not in claims:
            claims[match.expression] = Claim(
                entity=match.expression.entity,
                value=match.expression.value,
                score=0,
                length=len(match.expression.words),
                seq=match.seq,
            )

        return claims[match.expression]

    def claim(self, words: List[Word]) -> None:
        claims: Dict[Expression, Claim] = {}

        for word in words:
            self.claim_word(word, claims)

        for claim in claims.values():
            total = sum(p.score for p in claim.proofs)
            claim.score = float(total) / float(len(claim.proofs))
