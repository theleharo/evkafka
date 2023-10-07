from evkafka.state import State


def test_state_unknown_attr():
    state = State({"some": "val"})

    assert not hasattr(state, "val")


def test_state_attr_access():
    state = State({"some": "val"})

    assert state.some == "val"
