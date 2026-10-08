import sys, importlib.util
sys.path.insert(0, "src")
from repositories.user_repository import UserRepository
from repositories.listing_repository import ListingRepository
from repositories.review_repository import ReviewRepository
from repositories.transaction_repository import TransactionRepository
from repositories import auth_gateway as gw
from controllers.auth_controller import AuthController as New

spec = importlib.util.spec_from_file_location("old_auth", "old_auth_controller.py")
old_mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(old_mod)
Old = old_mod.AuthController

def build():
    u = UserRepository.seeded()
    repos = (u, ListingRepository.seeded(), ReviewRepository.seeded(), TransactionRepository.seeded())
    return repos, u

def summarize(r): return (r.ok, r.error, getattr(r.user, "email", None))

def run(ctrl_factory):
    repos, users = build()
    c = ctrl_factory(repos, users)
    out = []
    out.append(summarize(c.login("", "")))
    out.append(summarize(c.login("demo@mmcm.edu.ph", "wrong")))
    out.append(summarize(c.login("nobody@mmcm.edu.ph", "x")))
    out.append(summarize(c.login("demo@mmcm.edu.ph", "demo1234")))
    for args in [("", "a@b.edu.ph", "pw123456", "pw123456"), ("A", "bad", "pw123456", "pw123456"),
                 ("A", "a@gmail.com", "pw123456", "pw123456"), ("A", "a@b.edu.ph", "short", "short"),
                 ("A", "a@b.edu.ph", "pw123456", "different"), ("A", "demo@mmcm.edu.ph", "pw123456", "pw123456"),
                 ("New Kid", "kid@mmcm.edu.ph", "pw123456", "pw123456")]:
        out.append(summarize(c.register(*args)))
    out.append(summarize(c.login("kid@mmcm.edu.ph", "pw123456")))
    for args in [("kid@mmcm.edu.ph", "", "n", "n"), ("kid@mmcm.edu.ph", "pw123456", "short", "short"),
                 ("kid@mmcm.edu.ph", "pw123456", "newpass99", "other"), ("kid@mmcm.edu.ph", "pw123456", "pw123456", "pw123456"),
                 ("kid@mmcm.edu.ph", "WRONG", "newpass99", "newpass99")]:
        out.append(c.validate_password_change(*args))
    out.append(summarize(c.change_password("kid@mmcm.edu.ph", "pw123456", "newpass99", "newpass99")))
    out.append(summarize(c.login("kid@mmcm.edu.ph", "pw123456")))     # old password now fails
    out.append(summarize(c.login("kid@mmcm.edu.ph", "newpass99")))
    out.append(summarize(c.delete_account("kid@mmcm.edu.ph", "nope")))
    out.append(summarize(c.delete_account("ghost@mmcm.edu.ph", "DELETE")))
    out.append(summarize(c.delete_account("kid@mmcm.edu.ph", "DELETE")))
    out.append(summarize(c.login("kid@mmcm.edu.ph", "newpass99")))
    out.append(users.exists("kid@mmcm.edu.ph"))
    return out

old = run(lambda repos, users: Old(*repos))
new = run(lambda repos, users: New(*repos, gw.InMemoryAuthGateway(users)))
assert old == new, [(i, a, b) for i, (a, b) in enumerate(zip(old, new)) if a != b]
print("in-memory behavior identical to old controller across", len(old), "steps")

# ---- Supabase-mode with a scripted fake gateway ----
class Fake:
    in_memory = False
    def __init__(self, **o): self.o = o; self.calls = []
    def __getattr__(self, n):
        def f(*a):
            self.calls.append((n, a)); r = self.o[n]; return r(*a) if callable(r) else r
        return f
O = gw.AuthOutcome
repos, users = build()
# register with confirmation ON
c = New(*repos, Fake(sign_up=O(ok=True, needs_confirmation=True)))
r = c.register("Z", "z@school.edu.ph", "pw123456", "pw123456")
assert r.ok and r.needs_confirmation and r.user is None and r.tokens is None
# duplicate hidden by Supabase
r = New(*repos, Fake(sign_up=O.failure(gw.ALREADY_REGISTERED))).register("Z", "z@school.edu.ph", "pw123456", "pw123456")
assert (not r.ok) and r.error == "An account with this email already exists."
# login ok -> tokens pass through, profile loaded from the repo
r = New(*repos, Fake(sign_in=O(ok=True, access_token="a", refresh_token="r"))).login("demo@mmcm.edu.ph", "x")
assert r.ok and r.tokens == ("a", "r") and r.user.email == "demo@mmcm.edu.ph"
# unconfirmed / network / rate-limit messages
assert New(*repos, Fake(sign_in=O.failure(gw.EMAIL_NOT_CONFIRMED))).login("demo@mmcm.edu.ph","x").error.startswith("Please confirm your email")
assert New(*repos, Fake(sign_in=O.failure(gw.NETWORK, "boom"))).login("demo@mmcm.edu.ph","x").error == "Something went wrong. Please try again."
# signed in but no profile row
assert New(*repos, Fake(sign_in=O(ok=True))).login("ghost@mmcm.edu.ph","x").error == "Invalid email or password."
# delete: uses the signed-in uuid, never the typed email
f = Fake(current_user_id="uuid-123", admin_delete_user=O(ok=True))
r = New(*repos, f).delete_account("demo@mmcm.edu.ph", "DELETE")
assert r.ok and ("admin_delete_user", ("uuid-123",)) in f.calls
# admin failure is reported, cascade errors are not
assert not New(*repos, Fake(current_user_id="u", admin_delete_user=O.failure(gw.NOT_CONFIGURED))).delete_account("ana.r@mmcm.edu.ph","DELETE").ok
print("supabase-mode controller checks passed")