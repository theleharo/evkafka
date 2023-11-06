from typing import Annotated, Any, Literal, Union

from pydantic import AnyUrl, BaseModel, EmailStr, Field, StringConstraints


class Contact(BaseModel):
    name: str | None = None
    url: AnyUrl | None = None
    email: EmailStr | None = None

    model_config = {"extra": "allow"}


class License(BaseModel):
    name: str
    url: AnyUrl | None = None

    model_config = {"extra": "allow"}


class Info(BaseModel):
    title: str
    version: str
    description: str | None = None
    termsOfService: AnyUrl | None = None
    contact: Contact | None = None
    license: License | None = None

    model_config = {"extra": "allow"}


class ServerVariable(BaseModel):
    enum: list[str] | None = None
    default: str | None = None
    description: str | None = None
    examples: list[str] | None = None

    model_config = {"extra": "allow"}


class ExternalDocumentation(BaseModel):
    description: str | None = None
    url: AnyUrl

    model_config = {"extra": "allow"}


class Tag(BaseModel):
    name: str
    description: str | None = None
    externalDocs: ExternalDocumentation | None = None

    model_config = {"extra": "allow"}


class KafkaServerBinding(BaseModel):
    schemaRegistryUrl: AnyUrl | None = None
    schemaRegistryVendor: str | None = None
    bindingVersion: str | None = "latest"


class ServerBindings(BaseModel):
    # only https://github.com/asyncapi/bindings/tree/master/kafka#server
    kafka: KafkaServerBinding | None = None

    model_config = {"extra": "allow"}


class Reference(BaseModel):
    ref: str = Field(alias="$ref")


class Server(BaseModel):
    url: AnyUrl
    protocol: str
    protocolVersion: str | None = None
    description: str | None = None
    variables: dict[str, ServerVariable | Reference] | None = None
    # TBD SecurityRequirement https://www.asyncapi.com/docs/reference/specification/v2.6.0#securityRequirementObject
    security: list[dict[str, list[str]]] | None = None
    tags: list[Tag] | None = None
    bindings: ServerBindings | Reference | None = None

    model_config = {"extra": "allow"}


class TopicConfiguration(BaseModel):
    cleanup_policy: list[str] | None = Field(alias="cleanup.policy")
    retention_ms: int | None = Field(alias="retention.ms")
    retention_bytes: int | None = Field(alias="retention.bytes")
    delete_retention_ms: int | None = Field(alias="delete.retention.ms")
    max_message_bytes: int | None = Field(alias="max.message.bytes")


# Schema definition is taken from fastapi.openapi.models


class Discriminator(BaseModel):
    propertyName: str
    mapping: dict[str, str] | None = None


class XML(BaseModel):
    name: str | None = None
    namespace: str | None = None
    prefix: str | None = None
    attribute: bool | None = None
    wrapped: bool | None = None

    model_config = {"extra": "allow"}


class Schema(BaseModel):
    schema_: str | None = Field(default=None, alias="$schema")
    id: str | None = Field(default=None, alias="$id")
    ref: str | None = Field(default=None, alias="$ref")
    comment: str | None = Field(default=None, alias="$comment")

    # https://json-schema.org/draft-07/json-schema-validation
    type: str | None = None
    enum: list[Any] | None = None
    const: Any | None = None
    multipleOf: float | None = Field(default=None, gt=0)
    maximum: float | None = None
    exclusiveMaximum: float | None = None
    minimum: float | None = None
    exclusiveMinimum: float | None = None
    maxLength: int | None = Field(default=None, ge=0)
    minLength: int | None = Field(default=None, ge=0)
    pattern: str | None = None

    items: Union[
        "SchemaOrBool", list["SchemaOrBool"]
    ] | None = None  # 2020-12 new meaning
    additionalItems: Union["SchemaOrBool", None] = None  # 2020-12 new meaning
    maxItems: int | None = Field(default=None, ge=0)
    minItems: int | None = Field(default=None, ge=0)
    uniqueItems: bool | None = None
    contains: Union["SchemaOrBool", None] = None

    maxProperties: int | None = Field(default=None, ge=0)
    minProperties: int | None = Field(default=None, ge=0)
    required: list[str] | None = None
    properties: dict[str, "SchemaOrBool"] | None = None
    patternProperties: dict[str, "SchemaOrBool"] | None = None
    additionalProperties: Union["SchemaOrBool", None] = None
    dependencies: dict[
        str, Union[set[str], "SchemaOrBool"]
    ] | None = None  # 2019-09: split
    propertyNames: Union["SchemaOrBool", None] = None

    if_: Union["SchemaOrBool", None] = Field(default=None, alias="if")
    then: Union["SchemaOrBool", None] = None
    else_: Union["SchemaOrBool", None] = Field(default=None, alias="else")
    allOf: list["SchemaOrBool"] | None = None
    anyOf: list["SchemaOrBool"] | None = None
    oneOf: list["SchemaOrBool"] | None = None
    not_: Union["SchemaOrBool", None] = Field(default=None, alias="not")

    format: str | None = None

    contentEncoding: str | None = None
    contentMediaType: str | None = None

    definitions: dict[
        str, "SchemaOrBool"
    ] | None = None  # renamed to $defs, see 2019-09

    title: str | None = None
    description: str | None = None
    default: Any | None = None
    readOnly: bool | None = None
    writeOnly: bool | None = None
    examples: list[Any] | None = None

    # asyncapi 2.6.0
    discriminator: Discriminator | None = None
    externalDocs: ExternalDocumentation | None = None

    #  from 2019-09
    # new
    # anchor: str | None = Field(default=None, alias="$anchor")

    # definitions renamed to $defs
    # defs: dict[str, "SchemaOrBool"] | None = Field(default=None, alias="$defs")

    # dependencies  are splitted:
    # dependentSchemas: dict[str, "SchemaOrBool"] | None = None
    # dependentRequired: dict[str, set[str]] | None = None

    # new
    # vocabulary: str | None = Field(default=None, alias="$vocabulary")

    # new
    #
    # maxContains: int | None = Field(default=None, ge=0)
    # minContains: int | None = Field(default=None, ge=0)

    # new
    #     deprecated: bool | None = None

    # new
    # unevaluatedItems: Union["SchemaOrBool", None] = None
    # unevaluatedProperties: Union["SchemaOrBool", None] = None

    # new
    # contentSchema: Union["SchemaOrBool", None] = None

    # from 2020-12
    # items -> prefixItems      arrays
    # additionalItems -> items  # new syntax

    #     items: Union["SchemaOrBool", list["SchemaOrBool"]] | None = None
    #     prefixItems: list["SchemaOrBool"] | None = None

    # new
    # dynamicAnchor: str | None = Field(default=None, alias="$dynamicAnchor")
    # dynamicRef: str | None = Field(default=None, alias="$dynamicRef")

    model_config = {"extra": "allow"}


SchemaOrBool = Schema | bool


class KafkaOperationBinding(BaseModel):
    groupId: SchemaOrBool | Reference | None = None
    clientId: SchemaOrBool | Reference | None = None
    bindingVersion: str | None = "latest"


class OperationBindings(BaseModel):
    # only https://github.com/asyncapi/bindings/blob/master/kafka/README.md#channel
    kafka: KafkaOperationBinding | None = None

    model_config = {"extra": "allow"}


class OperationTrait(BaseModel):
    operationId: str | None = None
    summary: str | None = None
    description: str | None = None
    security: list[dict[str, list[str]]] | None = None
    tags: list[Tag] | None = None
    externalDocs: ExternalDocumentation | None = None
    bindings: OperationBindings | Reference | None = None

    model_config = {"extra": "allow"}


class CorrelationId(BaseModel):
    description: str | None = None
    location: str

    model_config = {"extra": "allow"}


class KafkaMesssageBinding(BaseModel):
    key: SchemaOrBool | Reference
    schemaIdLocation: str | None = None
    schemaIdPayloadEncoding: str | None = None
    schemaLookupStrategy: str | None = None


class MessageBindings(BaseModel):
    kafka: KafkaMesssageBinding | None = None

    model_config = {"extra": "allow"}


class MessageExample(BaseModel):
    headers: dict[str, Any] | None = None
    payload: Any
    name: str | None = None
    summary: str | None = None

    model_config = {"extra": "allow"}


class MessageTrait(BaseModel):
    messageId: str | None = None
    headers: SchemaOrBool | Reference | None = None
    correlationId: CorrelationId | Reference | None = None
    schemaFormat: str | None = None
    contentType: str | None = None
    name: str | None = None
    title: str | None = None
    summary: str | None = None
    description: str | None = None
    tags: list[Tag] | None = None
    externalDocs: ExternalDocumentation | None = None
    bindings: MessageBindings | Reference | None = None
    examples: list[MessageExample] | None = None


class Message(BaseModel):
    messageId: str | None = None
    headers: SchemaOrBool | Reference | None = None
    payload: Any
    correlationId: CorrelationId | Reference | None = None
    schemaFormat: str | None = None
    contentType: str | None = None
    name: str | None = None
    title: str | None = None
    summary: str | None = None
    description: str | None = None
    tags: list[Tag] | None = None
    externalDocs: ExternalDocumentation | None = None
    bindings: MessageBindings | Reference | None = None
    examples: list[MessageExample] | None = None
    traits: list[MessageTrait | Reference] | None = None

    model_config = {"extra": "allow"}


class MultipleMessages(BaseModel):
    oneOf: list[Message | Reference]


class Operation(BaseModel):
    operationId: str | None = None
    summary: str | None = None
    description: str | None = None
    security: list[dict[str, list[str]]] | None = None
    tags: list[Tag] | None = None
    externalDocs: ExternalDocumentation | None = None
    bindings: OperationBindings | Reference | None = None
    traits: list[OperationTrait | Reference] | None = None
    message: Message | Reference | MultipleMessages | None = None

    model_config = {"extra": "allow"}


class Parameter(BaseModel):
    description: str | None = None
    schema_: SchemaOrBool | Reference | None = Field(default=None, alias="schema")
    location: str | None = None


class KafkaChannelBinding(BaseModel):
    topic: str | None = None
    partitions: int | None = None
    replicas: int | None = None
    topicConfiguration: TopicConfiguration | None = None
    bindingVersion: str | None = "latest"


class ChannelBindings(BaseModel):
    # only https://github.com/asyncapi/bindings/blob/master/kafka/README.md#channel
    kafka: KafkaChannelBinding | None = None

    model_config = {"extra": "allow"}


class ChannelItem(BaseModel):
    ref: str = Field(default=None, alias="$ref")
    description: str | None = None
    servers: list[str] | None = None
    subscribe: Operation | None = None
    publish: Operation | None = None
    parameters: dict[
        Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_\-]+$")],
        Parameter | Reference,
    ] | None = None
    bindings: ChannelBindings | Reference | None = None

    model_config = {"extra": "allow"}


class SecuritySchemas(BaseModel):
    type: Literal[
        "userPassword",
        "apiKey",
        "oauth2",
        "plain",
        "scramSha256",
        "scramSha512",
        "gssapi",
    ] | None = None
    description: str | None = None

    model_config = {"extra": "allow"}


class Components(BaseModel):
    schemas: dict[str, SchemaOrBool | Reference]
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
    asyncapi: str = "2.6.0"
    id: str | None = None
    info: Info
    servers: dict[
        Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_\-]+$")],
        Server | Reference,
    ]
    defaultContentType: str | None = None
    channels: dict[str, ChannelItem]
    components: Components | None = None
    tags: list[Tag] | None = None
    externalDocs: ExternalDocumentation | None = None


Schema.model_rebuild()
