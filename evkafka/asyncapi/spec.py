from collections import defaultdict
from typing import Annotated, Any, Type, cast

from pydantic import BaseModel, Field, RootModel
from pydantic.json_schema import models_json_schema

from evkafka.asyncapi.models import AsyncAPI
from evkafka.config import BrokerConfigModel
from evkafka.handle import Handle


def get_openapi_spec(
    *,
    title: str,
    version: str,
    asyncapi_version: str = "2.6.0",
    consumer_configs: dict[str, dict[str, Any]] = None,
    description: str | None = None,
    terms_of_service: str | None = None,
    contact: dict[str, str | Any] | None = None,
    license_info: dict[str, str | Any] | None = None,
    tags: list[dict[str, Any]] | None = None,

) -> str:
    info = {"title": title, "version": version}
    if description:
        info['description'] = description
    if terms_of_service:
        info['termsOfService'] = terms_of_service
    if contact:
        info['contact'] = contact
    if license_info:
        info['license'] = license_info

    type_models: dict[str, [Type[BaseModel], Handle]] = {}

    topic_channel_ids: dict[str, set[tuple[str, str]]] = defaultdict(set)
    topic_desc: dict[str, str] = {}
    channel_events: dict[tuple[str, str], list[str]] = defaultdict(list)

    brokers = {}
    broker_desc: dict[str, BrokerConfigModel] = {}
    broker_id = 0

    if consumer_configs:
        for _, params in consumer_configs.items():
            handler = params['handler']
            config = params['config']

            broker = BrokerConfigModel(config)
            broker_name = broker.root['bootstrap_servers']

            if broker_name not in brokers:
                broker_ref = broker.root.get('name') or f'broker-{broker_id}'
                brokers[broker_name] = broker_ref
                broker_id += 1

                broker_desc[broker_ref] = broker
            else:
                broker_ref = brokers[broker]

            topics_config = config['topics']
            topics = []
            for topic in topics_config:
                if isinstance(topic, dict):
                    name = topic['name']
                    topic_desc[name] = topic.get('description')
                else:
                    name = topic
                topic_channel_ids[name].add((name, broker_ref))
                topics.append(name)

            for handle in handler.handles:
                type_ = handle.endpoint_dependencies.payload_param_type
                event_name = handle.event_type

                if issubclass(type_, BaseModel):
                    type_models[event_name] = (type_, handle)
                else:
                    # maybe move to endpoint?
                    root_model = type(event_name, (RootModel[Annotated[type_, Field(...)]],), {})
                    type_models[event_name] = (cast(Type[BaseModel], root_model), handle)

                for topic in topics:
                    channel_events[topic, broker_ref].append(event_name)

    _, top_level_schema = models_json_schema(
        models=[(m, 'validation') for m,_ in type_models.values()],
        by_alias=True,
        ref_template='#/components/schemas/{model}'
    )
    schemas = top_level_schema['$defs']

    messages = {}
    message_refs = {}
    for event_name, (model, handle) in type_models.items():
        message = {
            "description": handle.description,
            "summary": handle.summary,
            "tags": [{"name": t} for t in handle.tags] if handle.tags else None,
            "name": event_name,  # machine friendly
            "title": event_name,  # visible title
            'payload': {"$ref": f"#/components/schemas/{model.__name__}"},
        }
        messages[event_name] = message
        message_refs[event_name] = {"$ref": f"#/components/messages/{event_name}"}

    channels = {}
    for topic, channel_ids in topic_channel_ids.items():
        if len(channel_ids) == 1:
            key_func = lambda x: x[0]
        else:
            key_func = lambda x: f'{x[1]}/{x[0]}'

        for topic_broker in channel_ids:
            channel_name = key_func(topic_broker)

            events = channel_events[topic_broker]
            event_refs = [message_refs[m] for m in events]

            channels[channel_name] = {
                'description': topic_desc.get(topic_broker[0], None),
                'servers': [topic_broker[1]],
                'subscribe': {
                    'message': {'oneOf': event_refs}
                }
            }

    servers = {}

    for broker_name, broker_ref in brokers.items():
        servers[broker_ref] = {
            'url': broker_name,
            'protocol': 'kafka',
            'description': broker_desc[broker_ref].root.get('description')
        }

    spec: dict[str, Any] = {
        "asyncapi": asyncapi_version,
        "info": info,
        "servers": servers,
        "channels": channels,
        "components": {
            "schemas": schemas,
            "messages": messages,
        }
    }
    if tags:
        spec['tags'] = tags

    return AsyncAPI(**spec).model_dump_json(exclude_none=True, by_alias=True)
