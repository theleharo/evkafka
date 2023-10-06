import typing

F = typing.TypeVar("F", bound=typing.Callable[..., typing.Any])

Wrapped = typing.Callable[[F], F]

Lifespan = typing.Callable[[], typing.AsyncContextManager[dict[str, typing.Any] | None]]
