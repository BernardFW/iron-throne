from random import (
    SystemRandom,
)
from typing import (
    List,
    Optional,
    Set,
    Text,
    Tuple,
)

from simanneal import (
    Annealer,
)

from .claim import (
    Claim,
    Proof,
)
from .constraints import (
    Constraint,
)
from .pretenders import (
    Pretender,
)
from .words import (
    Word,
    tokenize,
)

random = SystemRandom()


class IronThroneSolver(Annealer):
    def __init__(self, words: List[Word], constraints: List[Constraint]):
        super().__init__()

        self.words = words
        self.constraints = constraints
        self.state: List[Optional[int]] = [None] * len(words)

    def move(self):
        word_idx = random.randint(0, len(self.words) - 1)
        word = self.words[word_idx]
        proof_idx = random.randint(0, len(word.proofs)) - 1

        if proof_idx < 0:
            self.state[word_idx] = None
        else:
            self.state[word_idx] = proof_idx

    def proofs(self) -> List[Optional[Proof]]:
        for word_idx, proof_idx in enumerate(self.state):
            if proof_idx is None:
                yield None
            else:
                yield self.words[word_idx].proofs[proof_idx]

    def energy(self):
        proofs = list(self.proofs())
        score = .0

        for constraint in self.constraints:
            score += constraint.score_hint(proofs)

        return score


class IronThrone(object):
    def __init__(self,
                 pretenders: List[Pretender],
                 constraints: List[Constraint]) -> None:
        super().__init__()
        self.pretenders = pretenders
        self.constraints = constraints

    def get_entities(self, text: Text) -> Tuple[List[Claim], float]:
        words = list(tokenize(text))

        for pretender in self.pretenders:
            pretender.claim(words)

        solver = IronThroneSolver(words, self.constraints)
        solver.anneal()

        proofs = list(solver.proofs())
        score = min((c.score(proofs) for c in self.constraints), default=.0)
        claims: Set[Claim] = set(p.claim for p in proofs if proofs is not None)

        return list(claims), score
