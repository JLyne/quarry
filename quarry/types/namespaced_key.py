import re
from dataclasses import dataclass

valid_namespace = re.compile("[a-z0-9._-]+")
valid_key = re.compile("[a-z0-9._\-/]+")


@dataclass(frozen=True)
class NamespacedKey:
    namespace: str
    key: str

    def __post_init__(self):
        if not valid_namespace.match(self.namespace):
            raise TypeError("Invalid namespace, must match [a-z0-9._-]+")

        if not valid_key.match(self.key):
            raise TypeError(f"Invalid key, must match [a-z0-9._-]+: {self.key}")

    @classmethod
    def minecraft(cls, key: str):
        return cls("minecraft", key)

    @classmethod
    def from_string(cls, string: str):
        split = string.split(":")

        if len(split) != 2:
            raise ValueError("String is not a valid namespaced id")

        return cls(split[0], split[1])

    def __str__(self):
        return f"{self.namespace}:{self.key}"


