from typing import Annotated, Any, Literal

from pydantic import AnyUrl, BaseModel, EmailStr, Field, StringConstraints


class Contact(BaseModel):
    name: str | None
    url: AnyUrl | None
    email: EmailStr | None

    model_config = {"extra": "allow"}


class License(BaseModel):
    name: str
    url: AnyUrl | None

    model_config = {"extra": "allow"}


class Info(BaseModel):
    title: str
    version: str
    description: str
    termsOfService: AnyUrl | None
    contact: Contact | None
    license: License | None

    model_config = {"extra": "allow"}


class ServerVariable(BaseModel):
    enum: list[str] | None
    default: str | None
    description: str | None
    examples: list[str] | None

    model_config = {"extra": "allow"}


class ExternalDocumentation(BaseModel):
    description: str | None
    url: AnyUrl

    model_config = {"extra": "allow"}


class Tag(BaseModel):
    name: str
    description: str | None
    externalDocs: ExternalDocumentation | None

    model_config = {"extra": "allow"}


class KafkaServerBinding(BaseModel):
    schemaRegistryUrl: AnyUrl | None
    schemaRegistryVendor: str | None
    bindingVersion: str | None = 'latest'


class ServerBindings(BaseModel):
    # only https://github.com/asyncapi/bindings/tree/master/kafka#server
    kafka: KafkaServerBinding | None

    model_config = {"extra": "allow"}


class Reference(BaseModel):
    ref: str = Field(alias="$ref")


class Server(BaseModel):
    url: AnyUrl
    protocol: str
    protocolVersion: str | None
    description: str | None
    variables: dict[str, ServerVariable | Reference] | None
    # TBD SecurityRequirement https://www.asyncapi.com/docs/reference/specification/v2.6.0#securityRequirementObject
    security: list[dict[str, list[str]]] | None
    tags: list[Tag] | None
    bindings: ServerBindings | Reference | None

    model_config = {"extra": "allow"}


class TopicConfiguration(BaseModel):
    cleanup_policy: list[str] | None = Field(alias="cleanup.policy")
    retention_ms: int | None = Field(alias="retention.ms")
    retention_bytes: int | None = Field(alias="retention.bytes")
    delete_retention_ms: int | None = Field(alias="delete.retention.ms")
    max_message_bytes: int | None = Field(alias="max.message.bytes")


class _Schema(BaseModel):
    # TODO
    pass


Schema = _Schema | bool


class KafkaOperationBinding(BaseModel):
    groupId: Schema | Reference | None
    clientId: Schema | Reference | None
    bindingVersion: str | None = 'latest'


class OperationBindings(BaseModel):
    # only https://github.com/asyncapi/bindings/blob/master/kafka/README.md#channel
    kafka: KafkaOperationBinding | None

    model_config = {"extra": "allow"}


class OperationTrait(BaseModel):
    operationId: str | None
    summary: str | None
    description: str | None
    security: list[dict[str, list[str]]] | None
    tags: list[Tag] | None
    externalDocs: ExternalDocumentation | None
    bindings: OperationBindings | Reference | None

    model_config = {"extra": "allow"}


class CorrelationId(BaseModel):
    description: str | None
    location: str

    model_config = {"extra": "allow"}


class KafkaMesssageBinding(BaseModel):
    key: Schema | Reference
    schemaIdLocation: str | None
    schemaIdPayloadEncoding: str | None
    schemaLookupStrategy: str | None


class MessageBindings(BaseModel):
    kafka: KafkaMesssageBinding | None

    model_config = {"extra": "allow"}


class MessageExample(BaseModel):
    headers: dict[str, Any] | None
    payload: Any
    name: str | None
    summary: str | None

    model_config = {"extra": "allow"}


class MessageTrait(BaseModel):
    messageId: str | None
    headers: Schema | Reference | None
    correlationId: CorrelationId | Reference | None
    schemaFormat: str | None
    contentType: str | None
    name: str | None
    title: str | None
    summary: str | None
    description: str | None
    tags: list[Tag] | None
    externalDocs: ExternalDocumentation | None
    bindings: MessageBindings | Reference | None
    examples: list[MessageExample] | None


class Message(BaseModel):
    messageId: str | None
    headers: Schema | Reference | None
    payload: Any
    correlationId: CorrelationId | Reference | None
    schemaFormat: str | None
    contentType: str | None
    name: str | None
    title: str | None
    summary: str | None
    description: str | None
    tags: list[Tag] | None
    externalDocs: ExternalDocumentation | None
    bindings: MessageBindings | Reference | None
    examples: list[MessageExample] | None
    traits: list[MessageTrait | Reference] | None

    model_config = {"extra": "allow"}


class MultipleMessages(BaseModel):
    oneOf: list[Message | Reference]


class Operation(BaseModel):
    operationId: str | None
    summary: str | None
    description: str | None
    security: list[dict[str, list[str]]] | None
    tags: list[Tag] | None
    externalDocs: ExternalDocumentation | None
    bindings: OperationBindings | Reference | None
    traits: list[OperationTrait | Reference] | None
    message: Message | Reference | MultipleMessages | None

    model_config = {"extra": "allow"}


class Parameter(BaseModel):
    description: str | None
    schema: Schema | Reference | None
    location: str | None


class KafkaChannelBinding(BaseModel):
    topic: str | None
    partitions: int | None
    replicas: int | None
    topicConfiguration: TopicConfiguration | None
    bindingVersion: str | None = 'latest'


class ChannelBindings(BaseModel):
    # only https://github.com/asyncapi/bindings/blob/master/kafka/README.md#channel
    kafka: KafkaChannelBinding | None

    model_config = {"extra": "allow"}


class ChannelItem(BaseModel):
    ref: str = Field(alias="$ref")
    description: str | None
    servers: list[str] | None
    subscribe: Operation | None
    publish: Operation | None
    parameters: dict[Annotated[str, StringConstraints(pattern=r'^[A-Za-z0-9_\-]+$')], Parameter | Reference]
    bindings: ChannelBindings | Reference | None

    model_config = {"extra": "allow"}


class SecuritySchemas(BaseModel):
    type: Literal["userPassword", "apiKey", "oauth2", "plain", "scramSha256", "scramSha512", "gssapi"] | None
    description: str | None

    model_config = {"extra": "allow"}

class Components(BaseModel):
    schemas: dict[str, Schema | Reference]
    servers: dict[str, Server | Reference]
    serverVariables: dict[str, ServerVariable | Reference]
    channels: dict[str, ChannelItem]
    messages: dict[str, Message | Reference]
    securitySchemas: dict[str, SecuritySchemas | Reference]
    parameters: dict[str, Parameter | Reference]
    correlationIds: dict[str, CorrelationId | Reference]
    operationTraits: dict[str, OperationTrait | Reference]
    messageTraits: dict[str, MessageTrait | Reference]
    serverBindings: dict[str, ServerBindings | Reference]
    channelBindings: dict[str, ChannelBindings | Reference]
    operationBindings: dict[str, OperationBindings | Reference]
    messageBindings: dict[str, MessageBindings | Reference]

    model_config = {"extra": "allow"}


class AsyncAPI(BaseModel):
    asyncapi: str = '2.6.0'
    id: str | None
    info: Info
    servers: dict[Annotated[str, StringConstraints(pattern=r'^[A-Za-z0-9_\-]+$')], Server | Reference]
    defaultContentType: str | None
    channels: dict[str, ChannelItem]
    components: Components | None
    tags: list[Tag]
    externalDocs: ExternalDocumentation | None
