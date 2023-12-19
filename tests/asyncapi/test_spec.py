import json

import pytest
from pydantic import BaseModel

from evkafka import EVKafkaApp, Sender
from evkafka.asyncapi.spec import get_asyncapi_spec, get_brokers, get_channels


@pytest.fixture()
def consumer_app():
    app = EVKafkaApp(
        config={
            "bootstrap_servers": "url",
            "topics": ["topic"],
        }
    )

    class SomeEvent(BaseModel):
        x: str

    @app.event("SomeEvent")
    def event_handler(e: SomeEvent):
        assert e

    @app.event("RawEvent")
    def raw_event_handler(e: str):
        assert e

    return app


@pytest.fixture()
def producer_app():
    app = EVKafkaApp()
    sender = Sender()

    class SomeEvent(BaseModel):
        x: str

    @sender.event("SomeEvent")
    async def event_handler(e: SomeEvent):
        assert e

    @sender.event("RawEvent", topic="raw-topic")
    async def raw_event_handler(e: str):
        assert e

    app.add_producer(
        config={
            "bootstrap_servers": "url",
            "topic": "topic",
        },
        sender=sender,
    )

    return app


def test_get_asyncapi_spec_info():
    spec = get_asyncapi_spec(
        title="title",
        version="version",
        configs={},
        description="description",
        terms_of_service="http://example.com",
        contact={"name": "contact_name"},
        license_info={"name": "MIT"},
        tags=[{"name": "a tag"}],
    )

    assert json.loads(spec) == {
        "asyncapi": "2.6.0",
        "info": {
            "title": "title",
            "version": "version",
            "description": "description",
            "termsOfService": "http://example.com/",
            "contact": {"name": "contact_name"},
            "license": {"name": "MIT"},
        },
        "servers": {},
        "channels": {},
        "components": {"messages": {}},
        "tags": [{"name": "a tag"}],
    }


def test_get_brokers_unnamed():
    config = {"default": {"config": {"bootstrap_servers": "url"}}}

    assert get_brokers(config) == (
        {"default": "broker-0"},
        {"broker-0": {"url": "url", "protocol": "kafka", "description": None}},
    )


def test_get_brokers_single_broker():
    config = {
        "default": {
            "config": {
                "bootstrap_servers": "url",
                "cluster_name": "broker",
                "cluster_description": "Description",
            }
        }
    }

    assert get_brokers(config) == (
        {"default": "broker"},
        {"broker": {"url": "url", "protocol": "kafka", "description": "Description"}},
    )


def test_get_brokers_many_brokers():
    config = {
        "default": {
            "config": {
                "bootstrap_servers": "url",
                "cluster_name": "broker",
                "cluster_description": "Description",
            }
        },
        "alt": {
            "config": {
                "bootstrap_servers": "url2",
                "cluster_name": "broker2",
                "cluster_description": "Description2",
            }
        },
    }

    assert get_brokers(config) == (
        {
            "default": "broker",
            "alt": "broker2",
        },
        {
            "broker": {"url": "url", "protocol": "kafka", "description": "Description"},
            "broker2": {
                "url": "url2",
                "protocol": "kafka",
                "description": "Description2",
            },
        },
    )


def test_get_brokers_merge_same_broker():
    config = {
        "default": {
            "config": {
                "bootstrap_servers": "url",
                "cluster_name": "broker",
                "cluster_description": "Description",
            }
        },
        "alt": {
            "config": {
                "bootstrap_servers": "url",
                "cluster_name": "broker",
                "cluster_description": "Description",
            }
        },
    }

    assert get_brokers(config) == (
        {
            "default": "broker",
            "alt": "broker",
        },
        {"broker": {"url": "url", "protocol": "kafka", "description": "Description"}},
    )


def test_get_channels_single_topic_for_consumer():
    config = {
        "default": {
            "config": {"topics": [{"name": "a-topic", "description": "desc"}]},
            "kind": "consumer",
        }
    }

    assert get_channels(config, {"default": "broker_ref"}) == (
        {
            "a-topic": {
                "description": "desc",
                "publish": {"message": {"oneOf": []}},
                "servers": {
                    "broker_ref",
                },
            }
        }
    )


def test_get_channels_set_topic_from_producer_config(mocker):
    config = {
        "default": {
            "config": {"topic": {"name": "a-topic", "description": "desc"}},
            "kind": "producer",
            "sender": mocker.Mock(sources=[mocker.Mock(topic=None)]),
        }
    }

    assert get_channels(config, {"default": "broker_ref"}) == (
        {
            "a-topic": {
                "description": "desc",
                "subscribe": {"message": {"oneOf": []}},
                "servers": {
                    "broker_ref",
                },
            }
        }
    )


def test_get_channels_set_topic_from_source_config(mocker):
    config = {
        "default": {
            "config": {},
            "kind": "producer",
            "sender": mocker.Mock(sources=[mocker.Mock(topic="src-topic")]),
        }
    }

    assert get_channels(config, {"default": "broker_ref"}) == (
        {
            "src-topic": {
                "description": None,
                "subscribe": {"message": {"oneOf": []}},
                "servers": {
                    "broker_ref",
                },
            }
        }
    )


def test_get_channels_for_consumer_combined():
    config = {
        "default": {"config": {"topics": ["a-topic"]}, "kind": "consumer"},
        "alt": {"config": {"topics": ["a-topic", "b-topic"]}, "kind": "consumer"},
    }

    assert get_channels(config, {"default": "broker_ref", "alt": "alt_broker_ref"}) == (
        {
            "a-topic": {
                "description": None,
                "publish": {"message": {"oneOf": []}},
                "servers": {"broker_ref", "alt_broker_ref"},
            },
            "b-topic": {
                "description": None,
                "publish": {"message": {"oneOf": []}},
                "servers": {
                    "alt_broker_ref",
                },
            },
        }
    )


def test_get_channels_for_consumer_producer(mocker):
    config = {
        "default": {"config": {"topics": ["a-topic", "b-topic"]}, "kind": "consumer"},
        "producer": {
            "config": {},
            "kind": "producer",
            "sender": mocker.Mock(sources=[mocker.Mock(topic="a-topic")]),
        },
    }

    assert get_channels(
        config, {"default": "broker_ref", "producer": "prod_broker_ref"}
    ) == (
        {
            "a-topic": {
                "description": None,
                "publish": {"message": {"oneOf": []}},
                "subscribe": {"message": {"oneOf": []}},
                "servers": {"broker_ref", "prod_broker_ref"},
            },
            "b-topic": {
                "description": None,
                "publish": {"message": {"oneOf": []}},
                "servers": {"broker_ref"},
            },
        }
    )


def test_asyncapi_int_consumer(consumer_app):
    assert json.loads(consumer_app.asyncapi()) == {
        "asyncapi": "2.6.0",
        "channels": {
            "topic": {
                "servers": ["broker-0"],
                "publish": {
                    "message": {
                        "oneOf": [
                            {"$ref": "#/components/messages/SomeEvent"},
                            {"$ref": "#/components/messages/RawEvent"},
                        ]
                    }
                },
            }
        },
        "components": {
            "messages": {
                "RawEvent": {
                    "name": "RawEvent",
                    "payload": {"$ref": "#/components/schemas/RawEventPayload"},
                    "title": "RawEvent",
                },
                "SomeEvent": {
                    "name": "SomeEvent",
                    "payload": {"$ref": "#/components/schemas/SomeEvent"},
                    "title": "SomeEvent",
                },
            },
            "schemas": {
                "RawEventPayload": {"title": "RawEventPayload", "type": "string"},
                "SomeEvent": {
                    "properties": {"x": {"title": "X", "type": "string"}},
                    "required": ["x"],
                    "title": "SomeEvent",
                    "type": "object",
                },
            },
        },
        "info": {"title": "EVKafka", "version": "0.1.0"},
        "servers": {"broker-0": {"protocol": "kafka", "url": "url"}},
    }


def test_asyncapi_int_producer(producer_app):
    assert json.loads(producer_app.asyncapi()) == {
        "asyncapi": "2.6.0",
        "channels": {
            "raw-topic": {
                "servers": ["broker-0"],
                "subscribe": {
                    "message": {"oneOf": [{"$ref": "#/components/messages/RawEvent"}]}
                },
            },
            "topic": {
                "servers": ["broker-0"],
                "subscribe": {
                    "message": {"oneOf": [{"$ref": "#/components/messages/SomeEvent"}]}
                },
            },
        },
        "components": {
            "messages": {
                "RawEvent": {
                    "name": "RawEvent",
                    "payload": {"$ref": "#/components/schemas/RawEventPayload"},
                    "title": "RawEvent",
                },
                "SomeEvent": {
                    "name": "SomeEvent",
                    "payload": {"$ref": "#/components/schemas/SomeEvent"},
                    "title": "SomeEvent",
                },
            },
            "schemas": {
                "RawEventPayload": {"title": "RawEventPayload", "type": "string"},
                "SomeEvent": {
                    "properties": {"x": {"title": "X", "type": "string"}},
                    "required": ["x"],
                    "title": "SomeEvent",
                    "type": "object",
                },
            },
        },
        "info": {"title": "EVKafka", "version": "0.1.0"},
        "servers": {"broker-0": {"protocol": "kafka", "url": "url"}},
    }
