from __future__ import annotations

from typing import Sequence, Callable
from collections import defaultdict
from pydantic import BaseModel, ConfigDict, model_validator, ValidationError


class Poll[T](BaseModel):
    model_config = ConfigDict(extra="forbid")

    choices: Sequence[T] = None
    votes: dict[T, int] = defaultdict(int)
    # TODO: Add total_votes calculated argument

    @model_validator(mode='after')
    def check_votes_and_choices(self):
        assert (
            self.choices or self.votes
        ), 'choices or votes must be specified in poll creation'

        if self.choices and self.votes:
            assert (
                not (set(self.votes.keys()) - set(self.choices))
            ), 'if choices and votes are specified, votes keys must be in choices'

        return self

    def model_post_init(self, __context):
        if not isinstance(self.votes, defaultdict):
            self.votes = defaultdict(int, self.votes)

        if self.choices is None:
            self.choices = set(self.votes.keys())

        if set(self.choices) != set(self.votes.keys()):
            for c in self.choices:
                self.votes[c]

        self.choices = tuple(sorted(self.choices))

    def vote(self, choice: T, num_votes: int = 1):
        self.votes[choice] += num_votes

    def set_vote(self, choice: T, value: int):
        self.votes[choice] = value

    def set_votes(self, votes: dict[T, int]):
        if set(votes.keys()) - self.choices:
            raise ValidationError('vote choices do not match with poll choices')
        self.votes |= votes

    def winner(self, strategy: Callable[T] = min) -> T:
        return strategy(self.winners())

    def winners(self) -> list[T]:
        # TUNE: Probably this can be done more efficiently
        max_value = max(self.votes.values())
        return [k for k, v in self.votes.items() if v == max_value]

    def looser(self, strategy: Callable[T] = min) -> T:
        return strategy(self.loosers())

    def loosers(self) -> list[T]:
        # TUNE: Probably this can be done more efficiently
        min_value = min(self.votes.values())
        return [k for k, v in self.votes.items() if v == min_value]

    # TODO: Add top choices based on statistics method

    def __add__(self, other: Poll[T]) -> Poll[T]:
        if self.choices != other.choices:
            raise ValueError('added polls must contain the same choices')

        added_votes = {
            choice: self.votes[choice] + other.votes[choice] for choice in self.choices
        }
        return Poll(choices=self.choices, votes=added_votes)

    @classmethod
    def from_dict(cls, votes: dict[T, int]) -> Poll[T]:
        return cls(votes=votes)

    @classmethod
    def from_list(cls, votes: list[dict[str, T | int]],
                  choice_key: str = 'choice', votes_key: str = 'votes') -> Poll:
        votes_dict = {
            v[choice_key]: int(v[votes_key]) for v in votes
        }
        return cls(votes=votes_dict)


class MultilevelPoll[T, U](BaseModel):
    model_config = ConfigDict(extra="forbid")

    choices_1: Sequence[T] = None
    choices_2: Sequence[U] = None
    votes: dict[T, dict[U, int]] = defaultdict(lambda: defaultdict(int))
    # TODO: Add total_votes calculated argument

    @model_validator(mode='after')
    def check_votes_and_choices(self):
        assert (
            bool(self.choices_1) == bool(self.choices_2)
        ), 'if choices_1 or choices_2 is specified, the other parameter must be also specified'

        assert (
            (self.choices_1 and self.choices_2) or self.votes
        ), 'choices_1 and choices_2 or votes must be specified in poll creation'

        if self.choices_1 and self.votes:
            assert (
                not (set(self.votes.keys()) - set(self.choices_1))
            ), 'if choices_1 and votes are specified, votes keys must be in choices_1'

        if self.choices_2 and self.votes:
            for c1 in self.choices_1:
                assert (
                    not (set(self.votes[c1].keys()) - set(self.choices_2))
                ), 'if choices_2 and votes are specified, level 2 votes keys must be in choices_2'

        return self

    def model_post_init(self, __context):
        if not isinstance(self.votes, defaultdict):
            self.votes = defaultdict(lambda x: defaultdict(int), self.votes)

        if self.choices_1 is None:
            self.choices_1 = set(self.votes.keys())

        if self.choices_2 is None:
            self.choices_2 = set()
            for _, v in self.votes.items():
                self.choices_2 |= set(v.keys())

        if set(self.choices_1) != set(self.votes.keys()):
            for c1 in self.choices_1:
                self.votes[c1] = defaultdict(int, self.votes.get(c1, {}))
                if set(self.choices_2) != set(self.votes[c1].keys()):
                    for c2 in self.choices_2:
                        self.votes[c1][c2]

        self.choices_1 = tuple(sorted(self.choices_1))
        self.choices_2 = tuple(sorted(self.choices_2))

    def vote(self, choice_1: T, choice_2: U, num_votes: int = 1):
        self.votes[choice_1][choice_2] += num_votes

    def set_vote(self, choice_1: T, choice_2: U, value: int):
        self.votes[choice_1][choice_2] = value

    def set_votes(self, votes: dict[T, dict[U, int]]):
        if set(votes.keys()) - self.choices_1:
            raise ValidationError('vote choices_1 do not match with poll choices_1')

        for choice_1 in votes.keys():
            if set(votes[choice_1].keys()) - self.choices_2:
                raise ValidationError(f'vote {choice_1} choices_2 do not match with poll choices_2')
            self.votes[choice_1] |= votes[choice_1]

    def _choice_2_votes(self, choice_2: U) -> dict[T, int]:
        return {k: v.get(choice_2, 0) for k, v in self.votes.items()}

    def choice_2_poll(self, choice_2: U) -> Poll[T]:
        return Poll(votes=self._choice_2_votes(choice_2))

    def winner(self, choice_2: U, strategy: Callable[T] = min) -> T:
        return strategy(self.winners(choice_2))

    def winners(self, choice_2: U) -> list[T]:
        if choice_2 not in self.choices_2:
            raise ValueError('choice_2 value must be in mutilevel choices_2 values')

        # TUNE: Probably this can be done more efficiently
        choice_2_votes = self._choice_2_votes(choice_2)
        max_value = max(choice_2_votes.values())
        return [k for k, v in choice_2_votes.items() if v == max_value]

    def looser(self, choice_2: U, strategy: Callable[T] = min) -> T:
        return strategy(self.loosers(choice_2))

    def loosers(self, choice_2: U) -> list[T]:
        if choice_2 not in self.choices_2:
            raise ValueError('choice_2 value must be in mutilevel choices_2 values')

        # TUNE: Probably this can be done more efficiently
        choice_2_values = self._choice_2_votes(choice_2)
        min_value = min(choice_2_values.values())
        return [k for k, v in choice_2_values.items() if v == min_value]

    # TODO: Add top choices based on statistics method

    @classmethod
    def from_dict(cls, votes: dict[T, dict[U, int]]) -> MultilevelPoll:
        return cls(votes=votes)

    @classmethod
    def from_list(cls, votes: list[dict[str, T | list[dict[str, U | int]]]],
                  choice_1_key: str = 'choice_1', votes_1_key: str = 'votes_1',
                  choice_2_key: str = 'choice_2', votes_2_key: str = 'votes_2') -> MultilevelPoll:
        votes_dict = {
            v1[choice_1_key]: {
                v2[choice_2_key]: int(v2[votes_2_key]) for v2 in v1[votes_1_key]
            } for v1 in votes
        }
        return cls(votes=votes_dict)
