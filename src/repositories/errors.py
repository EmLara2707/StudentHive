"""Errors the repositories raise, so controllers and views never see raw database
exceptions. No Streamlit."""


class RepositoryError(Exception):
    """Storage failed (network, database, permissions). The message is safe to show
    to a student; the original exception, if any, is chained as __cause__."""

    DEFAULT_MESSAGE = "Something went wrong. Please try again."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.DEFAULT_MESSAGE)


class ConflictError(RepositoryError):
    """A row changed since it was read (for example two people answering the same
    pending request at once). Nothing was written."""

    DEFAULT_MESSAGE = "That isn't available right now."


class NotFoundError(RepositoryError):
    """The row does not exist (any more)."""

    DEFAULT_MESSAGE = "That could not be found."
