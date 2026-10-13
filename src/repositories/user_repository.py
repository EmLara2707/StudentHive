"""What the controllers need from user storage. The only implementation is
SupabaseUserRepository (the `profiles` table); this file is just the interface, so
controllers can name the type without importing Supabase code."""
from typing import Protocol

from models.user import User


class UserRepository(Protocol):
    def get_by_email(self, email: str) -> User | None: ...

    def get_many(self, emails) -> "dict[str, User]":
        """{lower-cased email: User}. Emails that match nobody are missing."""
        ...

    def exists(self, email: str) -> bool: ...

    def add(self, user: User) -> None: ...

    def save(self, user: User) -> None: ...

    def set_photo(self, email: str, data: bytes, mime: str) -> bool: ...
