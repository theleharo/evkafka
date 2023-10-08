from evkafka.state import State


def test_state_unknown_attr():
    state = State({"some": "val"})

    assert not hasattr(state, "val")


def test_state_attr_access():
    state = State({"some": "val"})

    assert state.some == "val"


def test_state_is_equal_when_keys_and_values_are_equal():
    state1 = State({"a": "b"})
    state2 = State({"a": "b"})

    assert state1 == state2


def test_state_not_equal_diff_keys():
    state1 = State({"a": "b"})
    state2 = State({"c": "b"})

    assert state1 != state2


def test_state_not_equal_diff_values():
    state1 = State({"a": "b"})
    state2 = State({"a": "c"})

    assert state1 != state2


def test_state_not_equal_compared_to_dict():
    state1 = State({"a": "b"})
    state2 = {"a": "c"}

    assert state1 != state2
