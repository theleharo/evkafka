import re
from collections import defaultdict
from typing import Annotated, Any, Iterable, Type, cast

from pydantic import BaseModel, Field, RootModel
from pydantic.json_schema import models_json_schema

from evkafka.asyncapi.models import AsyncAPI
from evkafka.config import BrokerConfigModel
from evkafka.handle import Handle


def get_schemas_from_model_types(
    types: Iterable[Type[BaseModel]],
) -> dict[str, Any] | None:
    _, top_level_schema = models_json_schema(
        models=[(type_, "validation") for type_ in types],
        by_alias=True,
        ref_template="#/components/schemas/{model}",
    )
    return top_level_schema.get("$defs", None)


def to_ref(name: str | None) -> str | None:
    if not name:
        return name
    return re.sub(r"[^A-Za-z0-9_\-]", "-", name)


def get_brokers(
    consumer_configs: dict[str, Any]
) -> tuple[dict[str, str], dict[str, Any]]:
    refs = {}
    brokers = {}

    refs_by_url = {}
    broker_id = 0
    for name, params in consumer_configs.items():
        config = BrokerConfigModel(params["config"])
        broker_url = config.root["bootstrap_servers"]

        if broker_url not in refs_by_url:
            broker_ref = (
                to_ref(config.root.get("cluster_name")) or f"broker-{broker_id}"
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
                config.root.get("name", broker_ref) == broker_ref
            ), "Brokers with the same url have different name"
            assert broker["description"] == config.root.get(
                "cluster_description"
            ), "Brokers with the same url have different description"
            refs[name] = broker_ref

    return refs, brokers


def get_topics(
    consumer_configs: dict[str, Any]
) -> tuple[dict[str, set[str]], dict[str, Any]]:
    refs = defaultdict(set)
    topics: dict[str, dict[str, Any]] = {}

    for name, params in consumer_configs.items():
        config = params["config"]

        topics_config = config["topics"]
        assert topics_config, "Topics cannot be empty"

        for topic in topics_config:
            if isinstance(topic, dict):
                topic_ref = topic["name"]
                description = topic.get("description")
            else:
                topic_ref = topic
                description = None

            if topic_ref in topics:
                assert (
                    topics[topic_ref]["description"] == description
                ), "Same topics have different description"
                refs[name].add(topic_ref)
                continue

            topics[topic_ref] = {
                "description": description,
                "publish": {"message": {"oneOf": []}},
            }
            refs[name].add(topic_ref)

    return refs, topics


def get_handle_event(
    handle: Handle, default_topics: set[str]
) -> tuple[str, Type[BaseModel], set[str]]:
    event_name = handle.event_type
    event_ref = event_name  # should there be smth more complex?
    type_ = handle.endpoint_dependencies.payload_param_type

    # todo topics from Handle
    if issubclass(type_, BaseModel):
        return event_ref, type_, default_topics

    root_model = type(
        event_name + "Payload", (RootModel[Annotated[type_, Field(...)]],), {}  # type: ignore[valid-type]
    )
    return event_ref, cast(Type[BaseModel], root_model), default_topics


def get_asyncapi_spec(
    *,
    title: str,
    version: str,
    asyncapi_version: str = "2.6.0",
    consumer_configs: dict[str, dict[str, Any]],
    description: str | None = None,
    terms_of_service: str | None = None,
    contact: dict[str, str | Any] | None = None,
    license_info: dict[str, str | Any] | None = None,
    tags: list[dict[str, Any]] | None = None,
) -> str:
    info: dict[str, Any] = {"title": title, "version": version}
    if description:
        info["description"] = description
    if terms_of_service:
        info["termsOfService"] = terms_of_service
    if contact:
        info["contact"] = contact
    if license_info:
        info["license"] = license_info

    broker_refs, servers = get_brokers(consumer_configs)
    topic_refs, channels = get_topics(consumer_configs)

    type_models: dict[str, tuple[Type[BaseModel], Handle]] = {}

    for name, params in consumer_configs.items():
        broker_ref = broker_refs[name]
        consumer_topics = topic_refs[name]
        for topic in consumer_topics:
            channels[topic].setdefault("servers", []).append(broker_ref)

        handler = params["handler"]
        for handle in handler.handles:
            event_ref, event_model, event_topics = get_handle_event(
                handle, consumer_topics
            )

            # is it ok to overwrite?
            type_models[event_ref] = event_model, handle

            for topic in event_topics:
                channels[topic]["publish"]["message"]["oneOf"].append(
                    {"$ref": f"#/components/messages/{event_ref}"}
                )

    messages = {}
    for event_ref, (model, handle) in type_models.items():
        message = {
            "description": handle.description,
            "summary": handle.summary,
            "tags": [{"name": t} for t in handle.tags] if handle.tags else None,
            "name": event_ref,
            "title": event_ref,
            "payload": {"$ref": f"#/components/schemas/{model.__name__}"},
        }
        messages[event_ref] = message

    schemas = get_schemas_from_model_types([t for t, _ in type_models.values()])

    spec: dict[str, Any] = {
        "asyncapi": asyncapi_version,
        "info": info,
        "servers": servers,
        "channels": channels,
        "components": {
            "schemas": schemas,
            "messages": messages,
        },
    }
    if tags:
        spec["tags"] = tags

    return AsyncAPI(**spec).model_dump_json(exclude_none=True, by_alias=True)
