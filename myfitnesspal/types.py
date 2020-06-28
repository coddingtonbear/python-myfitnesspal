from typing import Callable, List

from typing_extensions import TypedDict


class CommandDefinition(TypedDict):
    function: Callable
    description: str
    is_alias: bool
    aliases: List[str]
