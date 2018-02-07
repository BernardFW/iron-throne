from typing import (
    List,
    Optional,
    Set,
    Tuple,
)

from .claim import (
    Claim,
    Proof,
)


class Constraint(object):
    def score(self, proofs: List[Optional[Proof]]) -> float:
        """
        Given a list of proofs, evaluates from 0 to 1 how much this constraint
        is respected.

        * 0 - The constraint is completely failed
        * 1 - The constraint is perfectly respected
        """

        raise NotImplementedError

    def score_hint(self, proofs: List[Optional[Proof]]) -> float:
        """
        If this constraint is binary (aka if any error triggers a 0.0 score),
        then we need to help the guessing algorithm. This scoring function
        will indicate how "hot" the answer is. It's a number as big as you
        want, just try to keep it balanced in comparison to other constraints
        and to make sure that a bigger number means a better solution.
        """

        raise NotImplementedError


class NoTwice(Constraint):
    """
    Makes sure that the same entity does not appear twice
    """

    def _score(self, proofs: List[Optional[Proof]]) -> Tuple[float, float]:
        """
        Internal scoring function. The first returned item is the number of
        entities found and the second one is the number of unique entities
        found.
        """

        if not proofs:
            return 0, 0

        entities = [proofs[0].claim.entity]

        for proof in proofs[1:]:
            entity = proof.claim.entity

            if entity != entities[-1]:
                entities.append(entity)

        unique = set(entities)

        return len(entities), len(unique)

    def score(self, proofs: List[Optional[Proof]]):
        e, u = self._score(proofs)
        return 1.0 if e == u else 0.0

    def score_hint(self, proofs: List[Optional[Proof]]):
        e, u = self._score(proofs)
        return e-u


class FullMatches(Constraint):
    """
    All claims should have their parts in order and have all their parts around
    """

    def _score(self, proofs: List[Optional[Proof]]) -> Tuple[float, float]:
        """
        Make sure that all claims are complete and in order. Returns (in that
        order) the number of checks passed and the number of checks made.
        """

        could = 1
        did = 0

        if not proofs:
            return .0, .0

        if proofs[0].order == 0:
            did += 1

        for i in range(1, len(proofs)):
            last, proof = proofs[i - 1], proofs[i]
            could += 1

            if proof.claim.id == last.claim.id:
                if proof.order == last.order + 1:
                    did += 1
            else:
                if proof.order == 0:
                    did += 1

                could += 1

                if last.order + 1 == last.claim.length:
                    did += 1

        if len(proofs) > 1:
            could += 1
            last = proofs[-1]

            if last.order + 1 == last.claim.length:
                did += 1

        return float(did), float(could)

    def score(self, proofs: List[Optional[Proof]]) -> float:
        d, c = self._score(proofs)
        return 1. if d == c else .0

    def score_hint(self, proofs: List[Optional[Proof]]) -> float:
        d, c = self._score(proofs)
        return d / c


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
    def score(self, proofs: List[Optional[Proof]]):
        return 1.0

    def score_hint(self, proofs: List[Optional[Proof]]):
        score = 0

        for proof in proofs:
            # noinspection PyNoneFunctionAssignment
            longest: Optional[Claim] = max(
                proof.word.proofs,
                key=lambda p: p.claim.length,
                default=None,
            )

            if longest is not None:
                score -= 1

                if proof.claim.length >= longest.length:
                    score += 2

        return score


class ClaimScores(Constraint):
    def score(self, proofs: List[Optional[Proof]]):
        total = sum(p.claim.score for p in proofs)
        return float(total) / float(len(proofs))

    def score_hint(self, proofs: List[Optional[Proof]]):
        return sum(p.claim.score for p in proofs)
