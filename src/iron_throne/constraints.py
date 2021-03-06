from collections import (
    defaultdict,
)
from typing import (
    Dict,
    List,
    NamedTuple,
    Optional,
    Set,
    Text,
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
    def cleanup(self, words: List[Word]) -> None:
        """
        Given a list of words, remove the proofs that we can know in advance
        won't ever provide a good solution
        """

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

    def follow_claim(self,
                     claim: Claim,
                     words: List[Word],
                     idx: int,
                     no_delete: Set[Proof]) -> None:
        """
        When a starting proof is found we follow it until it's out of order.
        If from this starting point we can find the whole match then all the
        valid proofs are added to the `no_delete` list of proofs that won't
        be deleted.
        """

        to_keep: List[Proof] = []

        for word in words[idx:]:
            for proof in word.proofs:
                if proof.claim == claim:
                    is_first = not to_keep and proof.order == 0
                    is_next = to_keep and to_keep[-1].order + 1 == proof.order

                    if is_first or is_next:
                        to_keep.append(proof)
                    else:
                        break

        if not to_keep or to_keep[-1].order != claim.length - 1:
            return

        no_delete.update(to_keep)

    def cleanup(self, words: List[Word]):
        """
        Some pretenders, in particular the expressions pretender, can generate
        a lot of proofs which are in fact completely stupid (basically, all the
        common words like "the" match a lot of times). This cleanup function
        will only keep the proofs that have a chance of being selected in the
        end, drastically reducing the complexity of finding a solution.
        """

        no_delete: Set[Proof] = set()
        claims: Set[Claim] = set()

        for i, word in enumerate(words):
            for proof in word.proofs:
                if proof.order == 0:
                    self.follow_claim(proof.claim, words, i, no_delete)
                claims.add(proof.claim)

        for claim in claims:
            claim.proofs = [p for p in claim.proofs if p in no_delete]

        for word in words:
            word.proofs = [p for p in word.proofs if p in no_delete]

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


class EntitySet(NamedTuple):
    penalty: int
    needs_one_of: Set[Text]
    also_allowed: Set[Text]


class AllowedSets(Constraint):
    EXTRA_ENTITY_WEIGHT = 100.

    def __init__(self, sets: List[EntitySet]):
        """
        A list, by order of priority, of sets of entities that are allowed to
        be together.

        The list is a list of tuples, like this:

        >>> AllowedSets([
        >>>     EntitySet(50, {'activity', 'interest'}, {'city', 'age'}),
        >>>     EntitySet(0, {'sanitary'}, set()),
        >>> ])

        The first int in the tuple is the penalty for choosing this set. The
        highest the least priority this set will get.

        The first set of the tuple is the mandatory entities. At least one of
        these has to be present.

        The second set is a list of other entities that are allowed to be
        found.
        """

        self.sets: List[EntitySet] = sets

    def energy_bounds(self, words: List[Word]):
        max_penalty = min(self.sets, key=lambda s: s.penalty).penalty
        return max_penalty, max_penalty + len(words) * self.EXTRA_ENTITY_WEIGHT

    def extract_entities(self, proofs: List[Optional[Proof]]) -> Set[Text]:
        entities = set()

        for proof in (p for p in proofs if p is not None):
            entities.add(proof.claim.entity)

        return entities

    def choose_set(self, entities: Set[Text]) -> Optional[EntitySet]:
        def list_options():
            for es in self.sets:
                if es.needs_one_of & entities:
                    yield es

        # noinspection PyTypeChecker
        return min(list_options(), key=lambda es: es.penalty, default=None)

    def energy(self, proofs: List[Optional[Proof]]):
        allowed = set()
        penalty = 0
        present = self.extract_entities(proofs)
        current_set = self.choose_set(present)

        if current_set:
            allowed = current_set.needs_one_of | current_set.also_allowed
            penalty = current_set.penalty

        return len(present - allowed) * self.EXTRA_ENTITY_WEIGHT + penalty

    def score(self, proofs: List[Optional[Proof]]):
        allowed = set()
        present = self.extract_entities(proofs)
        current_set = self.choose_set(present)

        if current_set:
            allowed = current_set.needs_one_of | current_set.also_allowed

        if present - allowed:
            return .0

        return 1.


class LargestClaim(Constraint):
    CLAIM_WEIGHT = 5.

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
