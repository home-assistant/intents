"""Tests for HassILExpressionListener"""
from hassil import (
    ListReference,
    Number,
    NumberRange,
    RuleReference,
    Sentence,
    Sequence,
    SequenceType,
    Word,
    parse_sentences,
)


def test_just_words():
    assert parse_sentences(["this is a test"]) == [
        s([w("this"), w("is"), w("a"), w("test")])
    ]


def test_group():
    assert parse_sentences(["(this is a test)"]) == [
        s(
            [
                grp(
                    [w("this"), w("is"), w("a"), w("test")],
                )
            ]
        )
    ]


def test_optional():
    assert parse_sentences(["this is [a] test"]) == [
        s(
            [
                w("this"),
                w("is"),
                alt(
                    [w("a"), Word.empty()],
                ),
                w("test"),
            ]
        )
    ]


def test_optional_nested():
    assert parse_sentences(["this [is [a]] test"]) == [
        s(
            [
                w("this"),
                alt(
                    [
                        grp([w("is"), alt([w("a"), Word.empty()])]),
                        Word.empty(),
                    ]
                ),
                w("test"),
            ]
        )
    ]


def test_alternative():
    assert parse_sentences(["this is (a | the) test"]) == [
        s(
            [
                w("this"),
                w("is"),
                alt(
                    [grp([w("a")]), grp([w("the")])],
                ),
                w("test"),
            ]
        )
    ]


def test_alternative_multiple_words():
    assert parse_sentences(["this is (a bigger | the biggest) test"]) == [
        s(
            [
                w("this"),
                w("is"),
                alt(
                    [
                        grp(
                            [w("a"), w("bigger")],
                        ),
                        grp(
                            [w("the"), w("biggest")],
                        ),
                    ],
                ),
                w("test"),
            ]
        )
    ]


def test_alternative_what():
    assert parse_sentences(["(what | what's | whats | what is)"]) == [
        s(
            [
                alt(
                    [
                        grp(
                            [w("what")],
                        ),
                        grp(
                            [w("what's")],
                        ),
                        grp(
                            [w("whats")],
                        ),
                        grp(
                            [w("what"), w("is")],
                        ),
                    ],
                ),
            ]
        )
    ]


def test_list_reference():
    assert parse_sentences(["this is a {test}"]) == [
        s([w("this"), w("is"), w("a"), ListReference("test")])
    ]


def test_list_reference_prefix_suffix():
    assert parse_sentences(["this is a pre'{test}-post"]) == [
        s(
            [
                w("this"),
                w("is"),
                w("a"),
                ListReference("test", prefix="pre'", suffix="-post"),
            ]
        )
    ]


def test_rule_reference():
    assert parse_sentences(["this is a <test>"]) == [
        s([w("this"), w("is"), w("a"), RuleReference("test")])
    ]


def test_escape():
    assert parse_sentences(["this \\[is\\] a \\{test\\}"]) == [
        s([w("this"), w("[is]"), w("a"), w("{test}")])
    ]


def test_quotes():
    assert parse_sentences(['this "[is]" a "{test}"']) == [
        s([w("this"), w("[is]"), w("a"), w("{test}")])
    ]


def test_escape_in_quotes():
    """Test escaped double quotes inside double quotes"""
    assert parse_sentences(['this is a "\\"test\\""']) == [
        s([w("this"), w("is"), w("a"), w('"test"')])
    ]


def test_number():
    assert parse_sentences(["this is 1 test"]) == [
        s([w("this"), w("is"), Number(1), w("test")])
    ]


def test_number_range():
    assert parse_sentences(["these are 1..100 tests"]) == [
        s([w("these"), w("are"), NumberRange(1, 100), w("tests")])
    ]


def test_number_range_step():
    assert parse_sentences(["these are 1..100,2 odd tests"]) == [
        s([w("these"), w("are"), NumberRange(1, 100, 2), w("odd"), w("tests")])
    ]


# -----------------------------------------------------------------------------


def s(items):
    return Sentence(items=items)


def w(text):
    return Word(text)


def grp(items):
    return Sequence(type=SequenceType.GROUP, items=items)


def alt(items):
    return Sequence(type=SequenceType.ALTERNATIVE, items=items)
