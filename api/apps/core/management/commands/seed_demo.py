"""Fill an empty database with the demo gym from the prototype: `python manage.py seed_demo` (add --reset to start over).

Every demo login uses the password `rackline-demo`:
  meera@rackline.demo (admin, account owner)   arjun@ / kavya@ (receptionists)   neha@ / neeraj@ / alex@ / imran@ (trainers)
  members sign in with their phone, e.g. 9800000001
"""
import random
from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.attendance.models import CheckIn, Device
from apps.attendance.services import check_in
from apps.core import clock
from apps.core.errors import RuleBroken
from apps.expenses.models import Expense
from apps.gyms.models import Branch, BranchSession, Gym, GymRole
from apps.members.models import Member, Offer, Plan
from apps.members.serializers import set_login
from apps.members.services import sell, take_payment
from apps.tasks.models import Task, TaskUpdate

User = get_user_model()
PASSWORD = "rackline-demo"

BRANCHES = {
    "Indiranagar": [("Morning", 5, 10), ("Afternoon", 12, 16), ("Evening", 17, 22)],
    "Koramangala": [("Morning", 5, 11), ("Evening", 16, 22)],
    "HSR Layout": [("Morning", 6, 10), ("Evening", 17, 21)],
    "Whitefield": [("Morning", 5, 10), ("Afternoon", 12, 16), ("Evening", 17, 22)],
}
STAFF = [
    ("Meera Iyer", "meera", GymRole.ADMIN, [], "", ""),
    ("Arjun Rao", "arjun", GymRole.RECEPTIONIST, ["Indiranagar", "Koramangala"], "Morning", ""),
    ("Kavya Nair", "kavya", GymRole.RECEPTIONIST, ["HSR Layout", "Whitefield"], "Evening", ""),
    ("Neha Sharma", "neha", GymRole.TRAINER, ["Indiranagar"], "Morning", "Strength, fat loss"),
    ("Neeraj Kumar", "neeraj", GymRole.TRAINER, ["Koramangala"], "Evening", "Bodybuilding"),
    ("Alex Fernandes", "alex", GymRole.TRAINER, ["HSR Layout", "Whitefield"], "Morning", "Mobility, yoga"),
    ("Imran Khan", "imran", GymRole.TRAINER, ["Whitefield"], "Evening", "CrossFit, conditioning"),
]
PLANS = [("Monthly", 1, 1500), ("Quarterly", 3, 4500), ("Premium 6 months", 6, 9000), ("Annual", 12, 15000)]
FIRST = "Aarav Vivaan Aditya Diya Ananya Ishaan Kabir Riya Saanvi Arnav Kiara Myra Reyansh Anika Vihaan Tara Dev Nisha Rohan Pooja Karan Sneha Rahul Meghna Siddharth Lakshmi Varun Zoya Nikhil Priya".split()
LAST = "Reddy Menon Gupta Shetty Pillai Das Joshi Patel Bose Hegde Kapoor Naidu".split()
GOALS = ["Weight loss", "Muscle gain", "General fitness", "Strength", "Endurance", ""]


class Command(BaseCommand):
    help = "Create the Rackline Fitness demo gym with branches, staff, members, payments, check-ins and tasks."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete the demo gym first")
        parser.add_argument("--members", type=int, default=60)

    @transaction.atomic
    def handle(self, *args, reset=False, members=60, **kw):
        rnd = random.Random(7)
        old = Gym.objects.filter(slug="rackline-fitness").first()
        if old and not reset:
            self.stdout.write("The demo gym already exists. Run with --reset to rebuild it.")
            return
        if old:
            self._wipe(old)

        gym = Gym.objects.create(name="Rackline Fitness", slug="rackline-fitness", status="active", billing_email="meera@rackline.demo")
        today = clock.today(gym)

        branches = {}
        for i, (name, sessions) in enumerate(BRANCHES.items()):
            b = Branch.objects.create(gym=gym, name=name, address=f"{name}, Bengaluru", phone=f"+9180410000{i}", days_open="every_day")
            BranchSession.objects.bulk_create([BranchSession(branch=b, name=n, starts=time(s), ends=time(e)) for n, s, e in sessions])
            Device.objects.create(branch=b, name="Front turnstile", serial=f"DEMO-{i + 1:03d}")
            branches[name] = b

        staff = {}
        for i, (name, key, role, where, shift, spec) in enumerate(STAFF):
            user = User.objects.filter(email=f"{key}@rackline.demo").first() or User.objects.create_user(email=f"{key}@rackline.demo", password=PASSWORD, name=name, phone=f"97000000{i:02d}")
            r = GymRole.objects.create(user=user, gym=gym, role=role, is_owner=key == "meera", shift=shift, specialities=spec, day_off="Sunday" if role != GymRole.ADMIN else "", device_user_id=str(900 + i))
            r.branches.set([branches[w] for w in where])
            staff[key] = r
        meera = staff["meera"]
        trainers_at = {b: [r for r in staff.values() if r.role == GymRole.TRAINER and branches[b] in r.branches.all()] for b in branches}

        plans = [Plan.objects.create(gym=gym, name=n, months=m, price_paise=p * 100, includes="Gym floor, lockers" + (", diet plan" if m >= 6 else "")) for n, m, p in PLANS]
        Plan.objects.create(gym=gym, name="Personal training · 12 sessions", kind=Plan.PT, months=3, sessions=12, price_paise=6000 * 100, includes="12 one-on-one sessions")
        diwali = Offer.objects.create(gym=gym, name="Diwali 15% off", percent_off=15, starts=today - timedelta(days=10), ends=today + timedelta(days=20))
        diwali.plans.set(plans[1:])
        Offer.objects.create(gym=gym, name="₹500 off for students", amount_off_paise=50000, starts=today - timedelta(days=60), ends=today + timedelta(days=120))

        desk = {b: (staff["arjun"] if b in ("Indiranagar", "Koramangala") else staff["kavya"]) for b in branches}
        people = []
        for i in range(members):
            bname = list(branches)[i % 4]
            name = f"{FIRST[i % len(FIRST)]} {LAST[(i * 5) % len(LAST)]}"
            m = Member.objects.create(
                gym=gym, code=f"RF-{1001 + i}", name=name, phone=f"98000000{i + 1:02d}" if i < 99 else f"9800{i:06d}",
                home_branch=branches[bname], trainer=rnd.choice(trainers_at[bname]) if rnd.random() < 0.7 else None,
                goal=rnd.choice(GOALS), joined_on=today - timedelta(days=rnd.randint(20, 400)), device_user_id=str(1001 + i),
            )
            m.phone = f"+91{m.phone}" if not m.phone.startswith("+") else m.phone
            m.save(update_fields=["phone"])
            plan = rnd.choice(plans)
            # spread plan ends so the demo shows every status: some ended, some ending this week, most running
            shape = i % 10
            if shape == 0:
                starts = clock.add_months(today, -plan.months) - timedelta(days=rnd.randint(3, 25))  # expired
            elif shape == 1:
                starts = clock.add_months(today, -plan.months) + timedelta(days=rnd.randint(1, 6))  # expiring
            else:
                starts = today - timedelta(days=rnd.randint(0, max(1, plan.months * 28 - 10)))
            offer = diwali if plan in plans[1:] and rnd.random() < 0.25 and diwali.starts <= starts <= diwali.ends else None
            sub = sell(m, plan, by=desk[bname], offer=offer, starts=starts)
            price = sub.price_paise
            paid = price if shape not in (2, 5) else price // 2  # a few with dues
            p = take_payment(m, paid, rnd.choice(["upi", "upi", "cash", "card"]), by=desk[bname], subscription=sub)
            p.taken_at = datetime.combine(min(starts, today), time(rnd.randint(6, 20), rnd.choice([0, 15, 30, 45])), tzinfo=clock.tz(gym))
            p.save(update_fields=["taken_at"])
            if shape == 3 and i % 20 == 3:
                sub.frozen_from, sub.frozen_until = today - timedelta(days=2), today + timedelta(days=12)
                sub.ends += timedelta(days=15)
                sub.save()
            if i < 10:
                set_login(m, PASSWORD)
            people.append(m)

        # a few payments taken today, for the desk's collection
        for m in people[2::10][:4]:
            owed = m.balance_paise()
            if owed:
                take_payment(m, owed, "upi", by=desk[m.home_branch.name])

        # check-ins for the last week: members and staff, spread over the sessions
        tz = clock.tz(gym)
        for back in range(7, -1, -1):
            day = today - timedelta(days=back)
            for m in people:
                if rnd.random() > 0.45:
                    continue
                sessions = BRANCHES[m.home_branch.name]
                n, s, e = rnd.choice(sessions)
                at = datetime.combine(day, time(rnd.randint(s, e - 1), rnd.randint(0, 59)), tzinfo=tz)
                if back == 0 and at > clock.local(gym):
                    continue
                self._try(m.home_branch, at, member=m, source=rnd.choice(["device", "device", "qr", "desk"]), status_day=day)
            for r in staff.values():
                if r.role == GymRole.ADMIN or day.weekday() == 6:
                    continue
                for b in r.branches.all()[:1]:
                    n, s, e = BRANCHES[b.name][0 if r.shift == "Morning" else -1]
                    at = datetime.combine(day, time(max(0, s - 1), 40 + rnd.randint(0, 19)), tzinfo=tz)
                    if back == 0 and at > clock.local(gym):
                        continue
                    self._try(b, at, staff=r, source="device")

        tasks = [
            ("Call members whose plan ends this week", "arjun", 0, Task.DOING, "Called 6 of 11 so far"),
            ("Restock towels and sanitiser at the desk", "kavya", 0, Task.TODO, None),
            ("Update diet plans for new Premium members", "neha", 2, Task.TODO, None),
            ("Check the leg press cable", "neeraj", -1, Task.TODO, None),
            ("Plan Saturday mobility class", "alex", 3, Task.DONE, "Class plan shared on the notice board"),
            ("Collect pending dues at Whitefield", "kavya", 1, Task.DOING, "3 paid, 2 promised by Friday"),
            ("Assess new members' starting weights", "imran", 1, Task.TODO, None),
        ]
        for title, who, due, status, note in tasks:
            t = Task.objects.create(gym=gym, title=title, assignee=staff[who], created_by=meera, due_date=today + timedelta(days=due), due_time=time(18) if due == 0 else None, status=status)
            if status != Task.TODO:
                TaskUpdate.objects.create(task=t, author=staff[who], kind=TaskUpdate.STATUS, text="Started")
            if note:
                TaskUpdate.objects.create(task=t, author=staff[who], text=note)
            if status == Task.DONE:
                TaskUpdate.objects.create(task=t, author=staff[who], kind=TaskUpdate.STATUS, text="Marked done")

        for b in branches.values():
            Expense.objects.create(gym=gym, branch=b, category="rent", amount_paise=rnd.choice([85000, 120000, 95000]) * 100, method="bank", paid_to="Landlord", spent_on=today.replace(day=1), created_by=meera)
            Expense.objects.create(gym=gym, branch=b, category="utilities", amount_paise=rnd.randint(8, 18) * 1000 * 100, method="upi", paid_to="BESCOM", spent_on=today.replace(day=min(5, today.day)), created_by=meera)
        Expense.objects.create(gym=gym, branch=branches["Whitefield"], category="equipment", amount_paise=42000 * 100, method="card", paid_to="Cult Equipment", note="2 adjustable benches", spent_on=today, created_by=meera)

        self.stdout.write(self.style.SUCCESS(
            f"Demo gym ready: {len(branches)} branches, {len(staff)} staff, {len(people)} members, "
            f"{CheckIn.objects.filter(gym=gym).count()} check-ins. Sign in as meera@rackline.demo / {PASSWORD} (X-Gym: rackline-fitness)."
        ))

    def _try(self, branch, at, status_day=None, **kw):
        try:
            check_in(branch, at=at, **kw)
        except RuleBroken:
            pass  # expired or frozen members get turned away, as at the door

    def _wipe(self, gym):
        from apps.audit.models import AuditLog
        from apps.members.models import Payment, Subscription

        AuditLog.objects.filter(gym=gym).delete()
        TaskUpdate.objects.filter(task__gym=gym).delete()
        Task.objects.filter(gym=gym).delete()
        CheckIn.objects.filter(gym=gym).delete()
        Expense.objects.filter(gym=gym).delete()
        Payment.objects.filter(gym=gym).delete()
        Subscription.objects.filter(member__gym=gym).delete()
        Member.objects.filter(gym=gym).delete()
        Offer.objects.filter(gym=gym).delete()
        Plan.objects.filter(gym=gym).delete()
        users = list(GymRole.objects.filter(gym=gym).values_list("user_id", flat=True))
        gym.delete()
        User.objects.filter(id__in=users, gym_roles__isnull=True, is_staff=False).delete()
