import json

import pytest
from pydantic import BaseModel

from evkafka import EVKafkaApp
from evkafka.asyncapi.spec import get_asyncapi_spec, get_brokers, get_topics


@pytest.fixture()
def app():
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


def test_get_asyncapi_spec_info():
    spec = get_asyncapi_spec(
        title="title",
        version="version",
        consumer_configs={},
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


def test_get_topics_single_topic():
    config = {
        "default": {"config": {"topics": [{"name": "a topic", "description": "desc"}]}}
    }

    assert get_topics(config) == (
        {
            "default": {
                "a topic",
            },
        },
        {"a topic": {"description": "desc", "publish": {"message": {"oneOf": []}}}},
    )


def test_get_topics_combined():
    config = {
        "default": {"config": {"topics": ["a topic"]}},
        "alt": {"config": {"topics": ["a topic", "b topic"]}},
    }

    assert get_topics(config) == (
        {
            "default": {
                "a topic",
            },
            "alt": {"a topic", "b topic"},
        },
        {
            "a topic": {"description": None, "publish": {"message": {"oneOf": []}}},
            "b topic": {"description": None, "publish": {"message": {"oneOf": []}}},
        },
    )


def test_asyncapi_int(app):
    assert json.loads(app.asyncapi()) == {
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
