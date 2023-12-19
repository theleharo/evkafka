import re
from collections import defaultdict
from typing import Annotated, Any, Type, cast

from pydantic import BaseModel, Field, RootModel
from pydantic.json_schema import models_json_schema

from evkafka.asyncapi.models import AsyncAPI
from evkafka.config import BrokerConfigModel
from evkafka.handle import Handle
from evkafka.handler import Handler
from evkafka.sender import Sender, Source


def name_to_ref(name: str | None) -> str | None:
    if not name:
        return name
    return re.sub(r"[^A-Za-z0-9_\-]", "-", name)


def topic_to_topic_desc(topic: dict | str) -> tuple[str, str | None]:
    if isinstance(topic, dict):
        return topic["name"], topic.get("description")
    return topic, None


def get_brokers(configs: dict[str, Any]) -> tuple[dict[str, str], dict[str, Any]]:
    refs = {}
    brokers = {}

    refs_by_url = {}
    broker_id = 0
    for name, params in configs.items():
        config = BrokerConfigModel(params["config"])
        broker_url = config.root["bootstrap_servers"]

        if broker_url not in refs_by_url:
            broker_ref = (
                name_to_ref(config.root.get("cluster_name")) or f"broker-{broker_id}"
            )
            broker_id += 1

            brokers[broker_ref] = {
                "url": broker_url,
                "protocol": "kafka",
                "description": config.root.get("cluster_description"),
            }
            refs_by_url[broker_url] = broker_ref
            refs[name] = broker_ref
        else:
            broker_ref = refs_by_url[broker_url]
            broker = brokers[broker_ref]
            assert (
                config.root.get("cluster_name", broker_ref) == broker_ref
            ), "Brokers with the same url have different name"
            assert broker["description"] == config.root.get(
                "cluster_description"
            ), "Brokers with the same url have different description"
            refs[name] = broker_ref

    return refs, brokers


def get_channels(
    configs: dict[str, Any],
    broker_refs: dict[str, str],
) -> dict[str, Any]:
    consumer_refs = defaultdict(set)
    producer_refs = defaultdict(set)
    topics: dict[str, dict[str, Any]] = {}

    for name, params in configs.items():
        broker_ref = broker_refs[name]
        kind = params["kind"]
        config = params["config"]

        if kind == "consumer":
            topics_config = config["topics"]
            assert topics_config, "Topics cannot be empty"

            for topic in topics_config:
                topic_ref, description = topic_to_topic_desc(topic)

                if topic_ref in topics:
                    assert (
                        topics[topic_ref]["description"] == description
                    ), "Same topics have different description"
                    consumer_refs[name].add(topic_ref)
                    topics[topic_ref]["publish"] = {"message": {"oneOf": []}}
                    topics[topic_ref]["servers"].add(broker_ref)
                    continue

                topics[topic_ref] = {
                    "description": description,
                    "publish": {"message": {"oneOf": []}},
                    "servers": {
                        broker_ref,
                    },
                }
                consumer_refs[name].add(topic_ref)
        else:
            default_topic = config.get("topic")
            sender: Sender = params["sender"]
            for source in sender.sources:
                topic = source.topic or default_topic
                assert topic is not None  # FIXME topic should be defined

                topic_ref, description = topic_to_topic_desc(topic)

                if topic_ref in topics:
                    assert (
                        topics[topic_ref]["description"] == description
                    ), "Same topics have different description"
                    producer_refs[name].add(topic_ref)
                    topics[topic_ref]["subscribe"] = {"message": {"oneOf": []}}
                    topics[topic_ref]["servers"].add(broker_ref)
                    continue

                topics[topic_ref] = {
                    "description": description,
                    "subscribe": {"message": {"oneOf": []}},
                    "servers": {
                        broker_ref,
                    },
                }
                producer_refs[name].add(topic_ref)

    return topics


def get_handle_event(handle: Handle) -> tuple[str, Type[BaseModel], str | None]:
    event_name = handle.event_type
    event_ref = event_name  # should there be smth more complex?
    type_ = handle.endpoint_dependencies.payload_param_type

    # todo: register topic per Handle?
    if issubclass(type_, BaseModel):
        return event_ref, type_, None

    root_model = type(
        event_name + "Payload", (RootModel[Annotated[type_, Field(...)]],), {}  # type: ignore[valid-type]
    )
    return event_ref, cast(Type[BaseModel], root_model), None


def get_source_event(source: Source) -> tuple[str, Type[BaseModel], str | None]:
    event_name = source.event_type
    event_ref = event_name
    type_ = source.endpoint_dependencies.payload_param_type
    topic = source.topic

    if issubclass(type_, BaseModel):
        return event_ref, type_, topic

    root_model = type(
        event_name + "Payload", (RootModel[Annotated[type_, Field(...)]],), {}  # type: ignore[valid-type]
    )
    return event_ref, cast(Type[BaseModel], root_model), topic


def get_messages(
    type_models: dict[str, tuple[Type[BaseModel], Handle | Source]]
) -> dict[str, Any]:
    messages = {}
    for event_ref, (model, ep) in type_models.items():
        message = {
            "description": ep.description,
            "summary": ep.summary,
            "tags": [{"name": t} for t in ep.tags] if ep.tags else None,
            "name": event_ref,
            "title": event_ref,
            "payload": {"$ref": f"#/components/schemas/{model.__name__}"},
        }
        messages[event_ref] = message
    return messages


def get_schemas(
    type_models: dict[str, tuple[Type[BaseModel], Handle | Source]]
) -> dict[str, Any] | None:
    types = (t for t, _ in type_models.values())
    _, top_level_schema = models_json_schema(
        models=[(type_, "validation") for type_ in types],
        by_alias=True,
        ref_template="#/components/schemas/{model}",
    )
    return top_level_schema.get("$defs", None)


def get_asyncapi_spec(
    *,
    title: str,
    version: str,
    asyncapi_version: str = "2.6.0",
    configs: dict[str, dict[str, Any]],
    description: str | None = None,
    terms_of_service: str | None = None,
    contact: dict[str, str | Any] | None = None,
    license_info: dict[str, str | Any] | None = None,
    tags: list[dict[str, Any]] | None = None,
) -> str:
    info: dict[str, Any] = {
        "title": title,
        "version": version,
        "description": description,
        "termsOfService": terms_of_service,
        "contact": contact,
        "license": license_info,
    }

    broker_refs, servers = get_brokers(configs)
    channels = get_channels(configs, broker_refs)

    type_models: dict[str, tuple[Type[BaseModel], Handle | Source]] = {}
    for params in configs.values():
        if params["kind"] == "consumer":
            handler: Handler = params["handler"]
            for handle in handler.handles:
                event_ref, event_model, event_topic = get_handle_event(handle)
                type_models[event_ref] = event_model, handle

                event_topics = []
                if event_topic:
                    event_topics = [event_topic]
                else:
                    topics_config = params["config"]["topics"]

                    for topic in topics_config:
                        topic_ref, _ = topic_to_topic_desc(topic)
                        event_topics.append(topic_ref)

                for topic in event_topics:
                    channels[topic]["publish"]["message"]["oneOf"].append(
                        {"$ref": f"#/components/messages/{event_ref}"}
                    )
        else:
            sender: Sender = params["sender"]
            for source in sender.sources:
                event_ref, event_model, event_topic = get_source_event(source)
                type_models[event_ref] = event_model, source

                if event_topic is None:
                    event_topic, _ = topic_to_topic_desc(params["config"]["topic"])

                channels[event_topic]["subscribe"]["message"]["oneOf"].append(
                    {"$ref": f"#/components/messages/{event_ref}"}
                )

    messages = get_messages(type_models)
    schemas = get_schemas(type_models)

    spec: dict[str, Any] = {
        "asyncapi": asyncapi_version,
        "info": info,
        "servers": servers,
        "channels": channels,
        "components": {
            "schemas": schemas,
            "messages": messages,
        },
        "tags": tags,
    }

    return AsyncAPI(**spec).model_dump_json(exclude_none=True, by_alias=True)
