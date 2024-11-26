import pytest

from pytest_unordered import unordered

from pydantic import ValidationError

from carton.models.poll import Poll, MultilevelPoll


def test_poll_validations():
    with pytest.raises(ValidationError):
        Poll()

    with pytest.raises(ValidationError):
        Poll(choices=('a', 'b'), votes={'c': 1})

    poll = Poll(choices=('a', 'b'), votes={'b': 1})
    assert dict(poll.votes) == {'a': 0, 'b': 1}

    poll = Poll(votes={'a': 1, 'b': 0, 'c': 3})
    assert list(poll.choices) == unordered(['a', 'b', 'c'])


def test_poll_calculations():
    poll = Poll(
        choices=['a', 'b', 'c'],
        votes={
            'a': 3,
            'b': 5
        }
    )

    assert poll.votes['a'] == 3
    assert poll.votes['c'] == 0
    assert poll.winner() == 'b'

    poll.set_vote('c', 5)
    assert poll.winner() == 'b'
    assert poll.winner(max) == 'c'
    assert poll.winners() == unordered(['b', 'c'])

    poll.vote('a', 3)
    assert poll.winner() == 'a'
    assert poll.winner(max) == 'a'
    assert poll.winners() == ['a']

    assert poll.looser() == 'b'
    assert poll.looser(max) == 'c'
    assert poll.loosers() == ['b', 'c']


def test_poll_from():
    poll_dict = Poll.from_dict(votes={
        'a': 1,
        'b': 2,
        'c': 3
    })
    poll_list = Poll.from_list(votes=[
        {'value': 'a', 'number': 1},
        {'value': 'b', 'number': 2},
        {'value': 'c', 'number': 3}
    ], choice_key='value', votes_key='number')

    assert poll_list == poll_dict


def test_multilevel_poll_validations():
    with pytest.raises(ValidationError):
        MultilevelPoll()

    with pytest.raises(ValidationError):
        MultilevelPoll(choices_1=('a', 'b'), choices_2=('1', '2', '3'),
                       votes={'c': {'3': 1}})

    with pytest.raises(ValidationError):
        MultilevelPoll(choices_1=('a', 'b', 'c'), choices_2=('1', '2'),
                       votes={'c': {'3': 1}})

    poll = MultilevelPoll(choices_1=('a', 'b'), choices_2=('1', '2', '3'),
                          votes={'a': {'2': 1}})
    assert dict(poll.votes) == {
        'a': {'1': 0, '2': 1, '3': 0},
        'b': {'1': 0, '2': 0, '3': 0},
    }
    poll = MultilevelPoll(votes={
        'a': {'1': 0, '2': 1},
        'b': {'1': 1, '2': 0}})
    assert list(poll.choices_1) == unordered(['a', 'b'])
    assert list(poll.choices_2) == unordered(['1', '2'])


def test_multilevel_poll_calculations():
    poll = MultilevelPoll(
        choices_1=['a', 'b', 'c'],
        choices_2=['good', 'bad', 'ugly'],
        votes={
            'a': {
                'good': 3,
                'bad': 2
            },
            'b': {
                'good': 5,
                'ugly': 6
            }
        }
    )

    assert poll._choice_2_votes('good') == {
        'a': 3,
        'b': 5,
        'c': 0
    }
    assert poll._choice_2_votes('ugly') == {
        'a': 0,
        'b': 6,
        'c': 0
    }

    assert poll.votes['a']['good'] == 3
    assert poll.votes['c']['ugly'] == 0
    assert poll.winner('good') == 'b'
    assert poll.winner('ugly') == 'b'

    poll.set_vote('c', 'good', 5)
    assert poll.winner('good') == 'b'
    assert poll.winner('good', max) == 'c'
    assert poll.winners('good') == unordered(['b', 'c'])

    with pytest.raises(ValueError):
        poll.winner('goos')

    poll.vote('a', 'good', 3)
    assert poll.winner('good') == 'a'
    assert poll.winner('good', max) == 'a'
    assert poll.winners('good') == ['a']

    assert poll.looser('ugly') == 'a'
    assert poll.looser('ugly', max) == 'c'
    assert poll.loosers('ugly') == unordered(['a', 'c'])


def test_multilevel_poll_from():
    poll_dict = MultilevelPoll.from_dict(votes={
        'a': {
            '1': 1,
        },
        'b': {
            '2': 2,
        },
        'c': {
            '1': 2,
            '2': 1,
        },
    })
    poll_list = MultilevelPoll.from_list(
        votes=[
            {
                'value': 'a',
                'result': [
                    {'value': '1', 'votes': 1},
                ]
            },
            {
                'value': 'b',
                'result': [
                    {'value': '2', 'votes': 2},
                ]
            },
            {
                'value': 'c',
                'result': [
                    {'value': '1', 'votes': 2},
                    {'value': '2', 'votes': 1},
                ]
            }
        ],
        choice_1_key='value', votes_1_key='result',
        choice_2_key='value', votes_2_key='votes')

    assert poll_list == poll_dict
