"""Profile page use-cases. No Streamlit, no session_state."""
from models.profile import Profile
from models.review import RatingSummary, Review
from models.user import User
from repositories.errors import RepositoryError
from repositories.review_repository import ReviewRepository
from repositories.user_repository import UserRepository
from utils.images import compress_image

_LIST_FIELDS = {"skills", "socials"}


class ProfileController:
    MAX_PHOTO_MB = 10
    MAX_PHOTO_BYTES = MAX_PHOTO_MB * 1024 * 1024

    def __init__(self, users: UserRepository, reviews: ReviewRepository) -> None:
        self._users = users
        self._reviews = reviews

    def get_user(self, email: str) -> User | None:
        return self._users.get_by_email(email)

    # ---- single fields ----
    def update_name(self, email: str, value: str) -> bool:
        value = (value or "").strip()
        user = self._users.get_by_email(email)
        if user is None or not value:       # a blank display name is ignored
            return False
        user.name = value
        self._users.save(user)
        return True

    def update_major(self, email: str, value: str) -> bool:
        return self._update_profile(email, major=(value or "").strip())

    def update_bio(self, email: str, value: str) -> bool:
        return self._update_profile(
            email, bio=(value or "").strip()[: Profile.MAX_BIO_EDIT_LENGTH]
        )

    def update_links(self, email: str, portfolio: str, linkedin: str, github: str) -> bool:
        return self._update_profile(
            email,
            portfolio=(portfolio or "").strip(),
            linkedin=(linkedin or "").strip(),
            github=(github or "").strip(),
        )

    def _update_profile(self, email: str, **changes) -> bool:
        user = self._users.get_by_email(email)
        if user is None:
            return False
        for key, value in changes.items():
            setattr(user.profile, key, value)
        self._users.save(user)
        return True

    # ---- skills / socials ----
    @staticmethod
    def parse_entries(raw: str) -> list[str]:
        """'a, b ,,c' -> ['a', 'b', 'c']"""
        return [v.strip() for v in (raw or "").split(",") if v.strip()]

    def add_entries(self, draft: list[str], raw: str) -> None:
        """Add every comma-separated entry to the draft, skipping duplicates."""
        for value in self.parse_entries(raw):
            if value not in draft:
                draft.append(value)

    def save_list(self, email: str, field_name: str, items: list[str]) -> bool:
        if field_name not in _LIST_FIELDS:
            raise ValueError(f"Unknown list field: {field_name}")
        cleaned: list[str] = []
        for item in items:
            item = item.strip()
            if item and item not in cleaned:
                cleaned.append(item)
        return self._update_profile(email, **{field_name: cleaned})

    # ---- photo ----
    def photo_error(self, size_bytes: int) -> str | None:
        if size_bytes > self.MAX_PHOTO_BYTES:
            return f"File is larger than {self.MAX_PHOTO_MB}MB. Please choose a smaller image."
        return None

    def update_photo(self, email: str, data: bytes, mime: str) -> str | None:
        """Returns an error message, or None on success."""
        error = self.photo_error(len(data))
        if error:
            return error
        data, mime = compress_image(data, mime)     # 1200px JPEG, before any upload
        try:
            if not self._users.set_photo(email, data, mime):
                return RepositoryError.DEFAULT_MESSAGE
        except RepositoryError as exc:
            return str(exc)
        return None

    # ---- reviews ----
    def get_reviews(self, email: str) -> list[Review]:
        return self._reviews.get_for_user(email)

    def get_rating_summary(self, email: str) -> RatingSummary:
        return RatingSummary.from_reviews(self._reviews.get_for_user(email))
