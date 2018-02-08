from collections import (
    defaultdict,
)
from typing import (
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

from .claim import (
    Claim,
    Proof,
)
from .utils import (
    is_contiguous,
)
from .words import (
    Word,
)


class Constraint(object):
    def energy_bounds(self, words: List[Word]) -> Tuple[float, float]:
        """
        Given those words, compute the lowest and highest bound of energy.
        Anything under the lowest can be considered as good while anything
        above the highest is completely crazy.
        """

        raise NotImplementedError

    def energy(self, proofs: List[Optional[Proof]]) -> float:
        """
        The further we are from a good solution the higher the energy level
        must be.

        This energy level must be consistent with the results returned by
        `score_bounds()`.
        """

        raise NotImplementedError

    def score(self, proofs: List[Optional[Proof]]) -> float:
        """
        Given a list of proofs, evaluates from 0 to 1 how much this constraint
        is respected.

        * 0 - The constraint is completely failed
        * 1 - The constraint is perfectly respected
        """

        raise NotImplementedError


class FullMatches(Constraint):
    """
    All claims should have their parts in order and have all their parts around
    """

    WRONG_CLAIM_WEIGHT = 10

    def energy_bounds(self, words: List[Word]) -> Tuple[float, float]:
        return 0, len(words) * self.WRONG_CLAIM_WEIGHT

    def check_claims(self, proofs: List[Optional[Proof]]) -> Dict[Claim, bool]:
        claims = defaultdict(lambda: [])

        for pos, proof in enumerate(proofs):
            if proof is not None:
                claims[proof.claim].append((pos, proof))

        return {
            claim: self.is_consistent(claim, proofs)
            for claim, proofs in claims.items()
        }

    def energy(self, proofs: List[Optional[Proof]]) -> float:
        claims = self.check_claims(proofs)
        e = .0

        for is_good in claims.values():
            if not is_good:
                e += self.WRONG_CLAIM_WEIGHT

        return e

    def score(self, proofs: List[Optional[Proof]]) -> float:
        return 1. if self.energy(proofs) == .0 else .0

    def is_consistent(self, claim: Claim, proofs: List[Tuple[int, Proof]]):
        try:
            assert proofs[0][1].order == 0
            assert proofs[-1][1].order == claim.length - 1
            assert is_contiguous([p for p, _ in proofs])
            assert is_contiguous([p.order for _, p in proofs])
        except AssertionError:
            return False
        else:
            return True


class AllowedSets(Constraint):
    def __init__(self, sets: List[Tuple[Set, Set]]):
        """
        A list, by order of priority, of sets of entities that are allowed to
        be together.

        The list is a list of tuples, like this:

        >>> AllowedSets([
        >>>     ({'activity', 'interest'}, {'city', 'age', 'gratis'}),
        >>>     ({'sanitary'}, set()),
        >>> ])

        The first set of the tuple is the mandatory entities. At least one of
        these has to be present.

        The second set is a list of other entities that are allowed to be
        found.
        """

        self.sets = sets

    def score_hint(self, proofs: List[Optional[Proof]]):
        """
        Basically, add a penalty if some things are out of place (if two sets
        are mixed up). If things are ok, just return 0.
        """

        score = 100 - len(self.sets)
        present = set(p.claim.entity for p in proofs)
        all_mandatory = set()

        for priority, (mandatory, extra) in enumerate(reversed(self.sets)):
            if present & mandatory:
                score -= 100
                score += priority

            all_mandatory += mandatory

            score -= len(present - mandatory - extra) * 10

        if present - all_mandatory == present:
            score -= 1000

        return score

    def score(self, proofs: List[Optional[Proof]]):
        return 1. if self.score_hint(proofs) >= 0 else .0


class LargestClaim(Constraint):
    CLAIM_WEIGHT = 1.

    def energy_bounds(self, words: List[Word]) -> Tuple[float, float]:
        return len(words) * self.CLAIM_WEIGHT, len(words) * self.CLAIM_WEIGHT

    def score(self, proofs: List[Optional[Proof]]) -> float:
        return 1.0

    def energy(self, proofs: List[Optional[Proof]]) -> float:
        score = .0

        for proof in proofs:
            if proof is None:
                score += self.CLAIM_WEIGHT
                continue

            d: Optional[Claim] = None
            longest: Optional[Proof] = max(
                proof.word.proofs,
                key=lambda p: p.claim.length,
                default=d,
            )

            if longest is not None:
                if proof.claim.length < longest.claim.length:
                    score += self.CLAIM_WEIGHT

        return score


class ClaimScores(Constraint):
    WORD_WEIGHT = 50.

    def energy_bounds(self, words: List[Word]) -> Tuple[float, float]:
        return len(words) * self.WORD_WEIGHT, len(words) * self.WORD_WEIGHT

    def energy(self, proofs: List[Optional[Proof]]) -> float:
        return sum(
            (1 - (p.claim.score if p is not None else .0)) * self.WORD_WEIGHT
            for p in proofs
        )

    def score(self, proofs: List[Optional[Proof]]):
        scores = [p.claim.score for p in proofs if p is not None]

        if not scores:
            return .0

        total = sum(scores)
        return float(total) / float(len(scores))
