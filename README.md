# StudentHive

## Project Description
StudentHive is a Python OOP application for Mapúa Malayan Colleges Mindanao (MMCM) students. It is a student-only marketplace where students can offer and book freelance services (Gigs) and rent out or borrow items (Rentals) in one place. Students sign up with their school email, build a profile, post listings, request bookings, track each booking from request to completion, and leave reviews.

It replaces informal Facebook groups and Discord servers, where postings get buried, nobody is accountable, and there is no shared record of who agreed to what and when.

## High-Priority Features
1. Student registration with an `mcm.edu.ph` email, confirmed with a 6-digit code
2. Profile onboarding (major, bio, skills, links, profile photo) and public student profiles
3. Listing creation wizard for Gigs (Service or Project) and Rentals, priced per hour, per day or one-time, with up to 10 photos
4. Marketplace with search and Gig or Rental filters
5. Booking requests with dates and times, and a lifecycle of Pending, Active, Completed or Cancelled (shown as the Requests, My, Completed and Cancelled tabs)
6. Rental pickup and drop-off confirmations
7. Dashboard with the student's listings, a calendar of accepted bookings and a "Next up" list
8. Reviews (1 to 5 stars with a comment, within 14 days of completion)
9. Account deletion and password change

## Technologies Used
- Python
- Streamlit (user interface)
- Supabase Auth (sign up, sign in, session restore)
- Supabase PostgreSQL with row-level security
- Supabase Storage (listing and profile images)
- Pillow (photo compression)
- Brevo SMTP (confirmation code emails)
- Streamlit Community Cloud (hosting)

## OOP Implementation
- **Encapsulation:** A `Transaction` (`src/models/transaction.py`) guards its own status. Only its methods (`accept`, `reject`, `withdraw`, `complete`, `cancel`, `confirm_pickup`, `confirm_dropoff`) change it, and each one calls `_require` first, which raises `InvalidTransition` when the action is not allowed.
- **Inheritance:** `ConflictError` and `NotFoundError` extend `RepositoryError` (`src/repositories/errors.py`), `InvalidTransition` extends `ValueError`, and enums such as `Role`, `Action`, `TransactionKind` and `TransactionStatus` extend `str` and `Enum`.
- **Polymorphism:** The repository interfaces (`UserRepository`, `ListingRepository`, `ReviewRepository`, `TransactionRepository`) are `Protocol` classes, and controllers only call the methods those protocols define. Any class with the same methods can be passed to a controller; the Supabase classes are the ones used in the app. In addition, `Transaction.allowed_actions(email, today)` returns different actions depending on whether the viewer is the provider or the requester.
- **Abstraction:** Controllers hide the processing steps from the views (for example `BookingController.submit` validates, prices and builds the `Transaction`), and the repository interfaces and `SupabaseAuthGateway` hide where data lives, so controllers never call Supabase or `st.session_state` directly.
- **Composition:** A `User` has a `Profile`, a `ListingEntry` is a `Listing` plus an `OwnerInfo`, and a `TransactionEntry` is a `Transaction` plus a `Counterpart`.

## Project Structure
- `src/App.py`: Entry point (page config, navigation, session restore)
- `src/models/`: Application classes and rules (`Transaction`, `Listing`, `Profile`, `User`, `Review`, `BookingForm`, ...)
- `src/views/`: User interface (`pages/`, `components/`, `styles/`, `session.py`)
- `src/controllers/`: Application operations (`AuthController`, `BookingController`, `TransactionController`, `MarketplaceController`, ...). They never import Streamlit.
- `src/repositories/`: Database access (repository interfaces, Supabase implementations, auth gateway)
- `src/utils/`: Helpers (Manila clock, dates, image compression, token expiry)
- `supabase/migrations/`: SQL files to run in order (`001` to `007`)
- `supabase/email_templates/`: The confirmation code email
- `scripts/`: Seed scripts for development projects

## Installation
1. Download or clone the repository.
2. Create a Supabase project, then run every file in `supabase/migrations/` in order (`001` to `007`) in the Supabase SQL editor.
3. In Supabase Authentication, turn on email confirmation and use `supabase/email_templates/confirm_signup.html` so the email contains the 6-digit code. Set up SMTP (the project used Brevo).
4. Create and activate a Python environment and install the packages.

   On Windows Command Prompt:

   ```
   python -m venv .lara
   .lara\Scripts\activate

   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

   On macOS or Linux:

   ```
   python3 -m venv .lara
   source .lara/bin/activate

   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```

5. Configure the application. Copy `src/.streamlit/secrets.toml.example` to `src/.streamlit/secrets.toml` and fill in your project's values (Supabase dashboard, Project Settings, API):

   ```
   [supabase]
   url = "https://YOUR-PROJECT-REF.supabase.co"
   anon_key = "YOUR-ANON-KEY"
   service_key = "YOUR-SERVICE-ROLE-KEY"
   ```

   Never commit `secrets.toml`. The service key is only used to delete accounts and by the seed scripts.

6. (Optional, development projects only) Add sample data:

   ```
   python scripts/seed_users.py
   python scripts/seed_market.py
   ```

7. Run the main file from inside the `src` folder:

   ```
   cd src
   python -m streamlit run App.py
   ```

## Developers
- Elizabeth Maude M. Lara
- Arem Kein I. Maraño
