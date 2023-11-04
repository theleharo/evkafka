from typing import Annotated

from pydantic import BaseModel, AnyUrl, EmailStr, constr, StringConstraints


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

    model_config = {"extra": "allow"}


class KafkaServerBindings(BaseModel):
    # only https://github.com/asyncapi/bindings/tree/master/kafka#server
    kafka: KafkaServerBinding | None

    model_config = {"extra": "allow"}


class Server(BaseModel):
    url: AnyUrl
    protocol: str
    protocolVersion: str | None
    description: str | None
    variables: dict[str, ServerVariable | str] | None
    # TBD SecurityRequirement https://www.asyncapi.com/docs/reference/specification/v2.6.0#securityRequirementObject
    security: list[dict[str, list[str]]] | None
    tags: list[Tag] | None
    bindings: KafkaServerBindings | str | None

    model_config = {"extra": "allow"}


class AsyncAPI(BaseModel):
    asyncapi: str = '2.6.0'
    id: str | None
    info: Info
    servers: dict[Annotated[str, StringConstraints(pattern=r'^[A-Za-z0-9_\-]+$')], Server | str]
