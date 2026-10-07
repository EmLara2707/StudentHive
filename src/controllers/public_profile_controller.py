"""Viewing another student's profile. Never imports streamlit."""
from models.public_profile import PublicProfile
from models.review import RatingSummary


class PublicProfileController:
    def __init__(self, users, reviews, listings) -> None:
        self._users = users          # UserRepository
        self._reviews = reviews      # ReviewRepository
        self._listings = listings    # ListingRepository

    def get(self, email: str) -> PublicProfile | None:
        """The public view of a profile, or None if the user no longer exists."""
        user = self._users.get_by_email(email or "")
        if user is None:
            return None
        reviews = self._reviews.get_for_user(user.email)
        open_listings = [l for l in self._listings.get_by_owner(user.email) if not l.is_closed]
        return PublicProfile(
            name=user.name,
            email=user.email,
            profile=user.profile,
            rating=RatingSummary.from_reviews(reviews),
            reviews=reviews,
            listings=open_listings,
        )

    def find_email_by_name(self, name: str) -> str | None:
        """Display name -> email, for the old Gigs/Rentals sample data. TEMP."""
        user = self._users.find_by_name(name)
        return user.email if user else None
