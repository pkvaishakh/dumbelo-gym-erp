from datetime import time, timedelta

import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.core import clock
from apps.gyms.models import Branch, BranchSession, Gym, GymRole
from apps.members.models import Member, Plan
from apps.members.services import sell, take_payment


class World:
    """A small gym: two branches, an admin, a receptionist at branch A, a trainer at A, a member on a monthly plan."""

    def __init__(self, slug="iron", n=0):
        self.gym = Gym.objects.create(name=f"Iron House {slug}", slug=slug, status="active")
        self.a = Branch.objects.create(gym=self.gym, name="A")
        self.b = Branch.objects.create(gym=self.gym, name="B")
        for br in (self.a, self.b):
            BranchSession.objects.create(branch=br, name="Morning", starts=time(5), ends=time(11))
            BranchSession.objects.create(branch=br, name="Evening", starts=time(16), ends=time(22))
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

    def client(self, role):
        c = APIClient()
        c.force_authenticate(role.user)
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


@pytest.fixture
def w(db):
    return World()


@pytest.fixture
def other(db):
    return World("steel", 1)
