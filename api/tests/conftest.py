from datetime import date, time, timedelta

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.billing.models import PriceList
from apps.billing.services import open_plan
from apps.core import clock
from apps.gyms.models import Branch, BranchSession, Gym, GymRole
from apps.members.models import Member, Plan
from apps.members.serializers import set_login
from apps.members.services import sell, take_payment


PRICES = {
    "base_paise": 999_00, "per_branch_paise": 3_100_00, "whatsapp_setup_paise": 2_000_00, "machine_setup_paise": 1_500_00,
    "utility_message_paise": 15, "marketing_message_paise": 90, "authentication_message_paise": 15,
}


def price_list():
    """Dumbelo's prices since 2026: what a gym's Dumbelo plan copies when it opens."""
    return PriceList.objects.get_or_create(active_from=date(2026, 1, 1), defaults=PRICES)[0]


class World:
    """A small gym: two branches, an admin, a receptionist at branch A, a trainer at A, a member on a monthly plan.
    Its Dumbelo plan has room for the two branches and no more."""

    def __init__(self, slug="iron", n=0):
        self.gym = Gym.objects.create(name=f"Iron House {slug}", slug=slug, status="active")
        self.a = Branch.objects.create(gym=self.gym, name="A")
        self.b = Branch.objects.create(gym=self.gym, name="B")
        for br in (self.a, self.b):
            BranchSession.objects.create(branch=br, name="Morning", starts=time(5), ends=time(11))
            BranchSession.objects.create(branch=br, name="Evening", starts=time(16), ends=time(22))
        price_list()
        self.billing = open_plan(self.gym, quota=2, billing_day=1)
        self.admin = self.role(f"admin{n}@x.in", GymRole.ADMIN, [], owner=True)
        self.desk = self.role(f"desk{n}@x.in", GymRole.RECEPTIONIST, [self.a])
        self.desk_b = self.role(f"deskb{n}@x.in", GymRole.RECEPTIONIST, [self.b])
        self.trainer = self.role(f"trainer{n}@x.in", GymRole.TRAINER, [self.a])
        self.monthly = Plan.objects.create(gym=self.gym, name="Monthly", months=1, price_paise=150000)
        self.today = clock.today(self.gym)
        self.member = self.new_member("Asha", f"98{n}0000001", self.a, trainer=self.trainer)
        sub = sell(self.member, self.monthly, by=self.desk, starts=self.today - timedelta(days=3))
        take_payment(self.member, sub.price_paise, "upi", by=self.desk)

    def role(self, email, role, branches, owner=False):
        u = User.objects.create_user(email=email, password="pass12345", name=email.split("@")[0].title())
        r = GymRole.objects.create(user=u, gym=self.gym, role=role, is_owner=owner)
        r.branches.set(branches)
        return r

    def new_member(self, name, phone, branch, trainer=None):
        return Member.objects.create(gym=self.gym, code=f"M-{phone[-4:]}", name=name, phone="+91" + phone, home_branch=branch, trainer=trainer)

    def plan_ending_on(self, day, name, phone, paid=True):
        """A member at branch A whose monthly plan runs out on `day`, paid up unless the test says otherwise."""
        member = self.new_member(name, phone, self.a)
        sub = sell(member, self.monthly, by=self.desk, starts=day - timedelta(days=30))
        sub.ends = day
        sub.save(update_fields=["ends"])
        if paid:
            take_payment(member, sub.price_paise, "cash", by=self.desk)
        return member

    def client(self, role):
        c = APIClient()
        c.force_authenticate(role.user)
        c.credentials(HTTP_X_GYM=self.gym.slug)
        return c

    def member_client(self):
        """The gym's own member, signed in to the app: what a member can reach, and what they can't."""
        set_login(self.member, "secret12345")
        c = APIClient()
        c.force_authenticate(self.member.user)
        c.credentials(HTTP_X_GYM=self.gym.slug)
        return c


@pytest.fixture(autouse=True)
def fast_passwords(settings):
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture(autouse=True)
def fresh_throttles():
    """Rate-limit counts live in the cache; start every test with none."""
    from django.core.cache import cache

    cache.clear()


@pytest.fixture(autouse=True)
def empty_outbox():
    """The fake WhatsApp sender keeps what it would have sent; every test starts with nothing in it."""
    from apps.messages.senders import FakeSender

    FakeSender.outbox.clear()


@pytest.fixture(autouse=True)
def shared_number(request):
    """Dumbelo's shared WhatsApp number with an approved template for each message (the demo's words), as a real
    server has, for every test that uses the database. Messages go from it unless a test sets up a gym's own."""
    db = next((f for f in ("transactional_db", "db") if f in request.fixturenames), None)
    if db is None:
        return None
    request.getfixturevalue(db)
    from apps.core.management.commands.seed_demo import DEMO_TEMPLATES
    from apps.messages.models import WhatsAppAccount, WhatsAppTemplate

    shared = WhatsAppAccount(gym=None, waba_id="100000000000009", phone_number_id="200000000000009", display_number="+91 80000 00009")
    shared.set_credentials(access_token="EAAGshared-test-token-0000000000", app_secret="shared-test-app-secret-00")
    shared.save()
    WhatsAppTemplate.objects.bulk_create([
        WhatsAppTemplate(account=shared, kind=kind, name=f"{kind}_v1", body=body, parameters=params, status=WhatsAppTemplate.APPROVED)
        for kind, params, body in DEMO_TEMPLATES
    ])
    return shared


@pytest.fixture
def prices(db):
    return price_list()


@pytest.fixture
def w(db):
    return World()


@pytest.fixture
def other(db):
    return World("steel", 1)
