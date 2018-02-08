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
    MAX_ATTENUATION = 0.9

    def __init__(self, words: List[Word], constraints: List[Constraint]):
        super().__init__([None] * len(words))

        self.words = words
        self.constraints = constraints

        self.penalty = 0
        self.bounds = []

    def configure(self):
        """
        Guess the configuration for the annealing. Please note that this is
        completely speculative... Moreover, the "steps" value calculation is
        really based on nothing but intuition.
        """

        t_mins = []
        t_maxs = []
        self.bounds = []

        for constraint in self.constraints:
            t_min, t_max = constraint.energy_bounds(self.words)
            t_mins.append(t_min)
            t_maxs.append(t_max)

            self.bounds.append((t_min, t_max))

        self.Tmin = float(sum(t_mins))
        self.Tmax = sum(t_maxs) * self.MAX_ATTENUATION
        self.updates = 0
        self.steps = 10000

    def move(self):
        valid_word_idx = [i for i, w in enumerate(self.words) if w.proofs]

        if not valid_word_idx:
            return

        word_idx = random.choice(valid_word_idx)

        valid_proof_idx = [
            x for x
            in [None] + list(range(0, len(self.words[word_idx].proofs)))
            if self.state[word_idx] != x
        ]

        if not valid_proof_idx:
            return

        self.state[word_idx] = random.choice(valid_proof_idx)

    def proofs(self) -> List[Optional[Proof]]:
        for word_idx, proof_idx in enumerate(self.state):
            if proof_idx is None:
                yield None
            else:
                yield self.words[word_idx].proofs[proof_idx]

    def energy(self):
        """
        All scores found are added up to the energy. If a constraint is outside
        of its acceptable bounds, then the Tmin is added to the energy so it
        won't be authorized to finish.
        """

        proofs = list(self.proofs())
        score = .0

        for (min_s, max_s), constraint in zip(self.bounds, self.constraints):
            s = constraint.energy(proofs)
            score += s

            if s >= min_s:
                score += self.Tmin

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

        for constraint in self.constraints:
            constraint.cleanup(words)

        solver = IronThroneSolver(words, self.constraints)
        solver.configure()
        solver.anneal()

        proofs = list(solver.proofs())
        score = min((c.score(proofs) for c in self.constraints), default=.0)
        claims: Set[Claim] = set(p.claim for p in proofs if p is not None)

        return list(claims), score
