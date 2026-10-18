"""Fill an empty database with the demo gym from the prototype: `python manage.py seed_demo` (add --reset to start over).

Every demo login uses the password `rackline-demo`:
  meera@rackline.demo (admin, account owner)   arjun@ / kavya@ (receptionists)   neha@ / neeraj@ / alex@ / imran@ (trainers)
  members sign in with their phone, e.g. 9800000001
  rackline@rackline.demo (a Rackline admin: the Console at /console, no role in the gym)
"""
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.attendance.models import CheckIn, Device
from apps.attendance.services import check_in
from apps.billing import invoicing
from apps.billing.models import Invoice, InvoiceLine, InvoicePayment, PriceList
from apps.billing.services import open_plan
from apps.core import clock
from apps.core.errors import RuleBroken
from apps.expenses.models import Expense, ExpenseDue, RecurringExpense
from apps.finance import services as money
from apps.finance.models import Account, DrawerClose, MoneyMove, Reconciliation, StatementTick
from apps.expenses.services import pay_due, sync_dues
from apps.gyms.models import Branch, BranchSession, Gym, GymRole
from apps.members.models import Member, Offer, Plan, Refund
from apps.members.serializers import set_login
from apps.members.services import sell, take_payment
from apps.messages.models import Message, WhatsAppAccount, WhatsAppTemplate
from apps.messages.services import send_due
from apps.payroll import services as payroll
from apps.payroll.models import Payslip, PayslipLine, SalaryItem, SalaryPayment, SalaryRule
from apps.reminders.services import queue_for
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
# The words of each message as a WhatsApp template, with the details that fill it (WhatsAppTemplate.PARAMETERS).
DEMO_TEMPLATES = [
    ("plan_ending", ["first_name", "plan", "gym", "end_date", "days_left"], "Hi {{1}}, your {{2}} at {{3}} ends on {{4}}, {{5}}. Renew it at the front desk to keep checking in."),
    ("plan_ends_today", ["first_name", "plan", "gym"], "Hi {{1}}, your {{2}} at {{3}} ends today. Renew it at the front desk to keep checking in."),
    ("payment_due", ["first_name", "amount", "plan", "gym"], "Hi {{1}}, {{2}} is still to pay on your {{3}} at {{4}}. You can pay it at the front desk the next time you come in."),
    ("payment_received", ["first_name", "amount", "gym", "paid_on"], "Hi {{1}}, thank you: {{3}} received {{2}} from you on {{4}}."),
    ("task_assigned", ["first_name", "task", "gym", "due_date"], "Hi {{1}}, you have a new task at {{3}}: {{2}}, due {{4}}."),
    ("rackline_invoice_due", ["first_name", "invoice_number", "gym", "amount", "due_date"], "Hi {{1}}, Rackline invoice {{2}} for {{3}} has {{4}} to pay by {{5}}."),
    ("rackline_payment_received", ["first_name", "amount", "gym", "receipt_number"], "Hi {{1}}, Rackline received {{2}} from {{3}}. Your receipt is {{4}}."),
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
        self._rackline_admin()
        self._prices()
        self._whatsapp()
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
        open_plan(gym, quota=len(BRANCHES) + 1, billing_day=1)  # room for one more, so Add Branch works in the demo

        staff = {}
        for i, (name, key, role, where, shift, spec) in enumerate(STAFF):
            user = User.objects.filter(email=f"{key}@rackline.demo").first() or User.objects.create_user(email=f"{key}@rackline.demo", password=PASSWORD, name=name, phone=f"97000000{i:02d}")
            r = GymRole.objects.create(user=user, gym=gym, role=role, is_owner=key == "meera", shift=shift, specialities=spec, day_off="Sunday" if role != GymRole.ADMIN else "", device_user_id=str(900 + i))
            r.branches.set([branches[w] for w in where])
            staff[key] = r
        meera = staff["meera"]
        accounts = self._accounts(gym, branches, meera, today)  # before any money is taken, so every payment lands in one
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

        self._bills(gym, branches, meera, today, rnd)
        self._payroll(gym, staff, branches, meera, today)
        Expense.objects.create(gym=gym, branch=branches["Whitefield"], category="equipment", amount_paise=42000 * 100, method="card", paid_to="Cult Equipment", note="2 adjustable benches", spent_on=today,
                               created_by=meera, account=Account.objects.for_money(branches["Whitefield"].id, "card", on=today))
        self._moves(gym, accounts, meera, today)
        self._rackline_invoices(gym, today)

        # Yesterday's and today's reminders, sent by the fake sender, so the Reminders card has something in it.
        for day in (today - timedelta(days=1), today):
            queue_for(gym, day)
            send_due(gym, day)

        self.stdout.write(self.style.SUCCESS(
            f"Demo gym ready: {len(branches)} branches, {len(staff)} staff, {len(people)} members, "
            f"{CheckIn.objects.filter(gym=gym).count()} check-ins, {Message.objects.filter(gym=gym).count()} reminders sent. "
            f"Sign in as meera@rackline.demo / {PASSWORD} (X-Gym: rackline-fitness)."
        ))

    def _rackline_admin(self):
        """Rackline's own login for the Console. Kept across --reset: it belongs to no gym."""
        if not User.objects.filter(email="rackline@rackline.demo").exists():
            User.objects.create_superuser(email="rackline@rackline.demo", password=PASSWORD, name="Rackline Admin")

    def _prices(self):
        """Rackline's prices, kept across --reset like the Rackline admin: they belong to no gym."""
        if not PriceList.objects.exists():
            PriceList.objects.create(
                active_from=clock.add_months(date.today(), -6).replace(day=1), base_paise=999 * 100, per_branch_paise=3100 * 100,
                whatsapp_setup_paise=2000 * 100, machine_setup_paise=1500 * 100, utility_message_paise=15,
                marketing_message_paise=90, authentication_message_paise=15, note="Launch prices",
            )

    def _whatsapp(self):
        """Rackline's shared number with a template for each message, kept across --reset like the prices. Its
        credentials are made up, so Test Connection says Meta turned them down: that's the demo working."""
        if WhatsAppAccount.objects.filter(gym=None).exists():
            return
        shared = WhatsAppAccount(gym=None, waba_id="100000000000001", phone_number_id="200000000000001", display_number="+91 80000 12345")
        shared.set_credentials(access_token="demo-not-a-real-meta-token-0000", app_secret="demo-not-a-real-app-secret")
        shared.save()
        T = WhatsAppTemplate
        WhatsAppTemplate.objects.bulk_create([T(account=shared, kind=kind, name=f"{kind}_v1", body=body, parameters=params, status=T.APPROVED)
                                              for kind, params, body in DEMO_TEMPLATES])

    def _rackline_invoices(self, gym, today):
        """Three months of Rackline invoices: the first two paid by bank transfer, this month's half paid, and the
        machine setup for the turnstiles waiting for the next invoice."""
        ops = User.objects.get(email="rackline@rackline.demo")
        this_month = today.replace(day=1)
        for back in (2, 1, 0):
            inv = invoicing.write_invoice(gym, clock.add_months(this_month, -back))
            amount = inv.total_paise if back else inv.total_paise // 200 * 100  # half, in whole rupees
            invoicing.record_payment(inv, amount_paise=amount, method="bank", paid_on=min(inv.issued_on + timedelta(days=3), today),
                                     reference=f"HDFC{inv.issued_on:%y%m}0042", by=ops)
        invoicing.add_charge(gym, kind=InvoiceLine.MACHINE_SETUP, quantity=Device.objects.filter(branch__gym=gym).count(), by=ops)

    def _accounts(self, gym, branches, meera, today):
        """Cash in hand at every branch; one HDFC account shared by Indiranagar and Koramangala, its own account for
        each of the other two, and the owner's reserve, which no branch uses."""
        since = today - timedelta(days=420)  # before the oldest payment the demo writes
        new = lambda **kw: Account.objects.create(gym=gym, opened_on=since, created_by=meera, **kw)  # noqa: E731
        out = {f"{name} cash": new(kind=Account.CASH, branch=b, opening_balance_paise=10000 * 100) for name, b in branches.items()}
        for name, bank, number, ifsc, opening, uses in (
            ("HDFC current", "HDFC Bank", "50200012345678", "HDFC0001234", 900000, ["Indiranagar", "Koramangala"]),
            ("ICICI current", "ICICI Bank", "000405012345", "ICIC0000004", 400000, ["HSR Layout"]),
            ("Axis savings", "Axis Bank", "917010012340911", "UTIB0000123", 300000, ["Whitefield"]),
            ("Owner's reserve", "Kotak Mahindra Bank", "4612343307", "KKBK0000431", 300000, []),
        ):
            out[name] = new(kind=Account.BANK, name=name, bank_name=bank, account_number=number, ifsc=ifsc, opening_balance_paise=opening * 100)
            money.set_branches(out[name], [branches[u] for u in uses])
        return out

    def _moves(self, gym, accounts, meera, today):
        """Each branch banks its cash but a float, the owner adds funds from the reserve and draws from HDFC."""
        for name, a in accounts.items():
            if a.kind == Account.CASH and (spare := money.balance_of(a) - 5000 * 100) > 0:
                to = Account.objects.for_money(a.branch_id, "bank", on=today)
                money.move(gym, kind=MoneyMove.TRANSFER, from_account=a, to_account=to, amount_paise=spare, moved_on=today - timedelta(days=1), by=meera,
                           note="Banked the week's cash")
        money.move(gym, kind=MoneyMove.TRANSFER, from_account=accounts["Owner's reserve"], to_account=accounts["Axis savings"], amount_paise=60000 * 100,
                   moved_on=today - timedelta(days=5), by=meera, note="For Whitefield's new equipment")
        # A share of what HDFC holds, not a fixed sum: what it holds depends on the bills and salaries due this month.
        if (drawings := money.balance_of(accounts["HDFC current"]) // 10 // 100_000 * 100_000) > 0:
            money.move(gym, kind=MoneyMove.WITHDRAWAL, from_account=accounts["HDFC current"], amount_paise=drawings, moved_on=today - timedelta(days=3), by=meera,
                       note="Owner's drawings")
        money.move(gym, kind=MoneyMove.DEPOSIT, to_account=accounts["Owner's reserve"], amount_paise=1250 * 100, moved_on=today - timedelta(days=2), by=meera,
                   note="Interest")

    def _bills(self, gym, branches, meera, today, rnd):
        """Rent and electricity as recurring expenses since two months ago: paid, except this month's rent at
        Whitefield, which is late, so Dues and Home have something to show."""
        first = clock.add_months(today.replace(day=1), -2)
        for name, b in branches.items():
            rent = RecurringExpense.objects.create(gym=gym, branch=b, name="Rent", category="rent", amount_paise=rnd.choice([85000, 120000, 95000]) * 100,
                                                   method="bank", paid_to="Landlord", frequency="monthly", starts=first, remind_days=5, created_by=meera)
            power = RecurringExpense.objects.create(gym=gym, branch=b, name="Electricity", category="utilities", amount_paise=rnd.randint(8, 18) * 1000 * 100,
                                                    method="upi", paid_to="BESCOM", frequency="monthly", starts=first.replace(day=10), remind_days=3, created_by=meera)
            sync_dues(gym, today)
            for due in ExpenseDue.objects.filter(recurring__in=[rent, power], due_on__lte=today):
                if name == "Whitefield" and due.recurring == rent and due.due_on.month == today.month:
                    continue
                pay_due(due, amount_paise=due.amount_paise if due.recurring == rent else due.amount_paise + rnd.randint(-20, 20) * 10000,
                        method=due.recurring.method, paid_on=due.due_on, by=meera)
        RecurringExpense.objects.create(gym=gym, branch=branches["Indiranagar"], name="Gym software", category="other", amount_paise=2499 * 100, method="card",
                                        paid_to="Rackline", frequency="monthly", starts=today + timedelta(days=2), remind_days=3, created_by=meera)
        sync_dues(gym, today)

    def _payroll(self, gym, staff, branches, meera, today):
        """A salary for every staff member: last month worked out, approved and paid; this month a draft."""
        home = next(iter(branches.values()))
        pay = {"meera": ("fixed", 60000), "arjun": ("attendance", 22000), "kavya": ("attendance", 21000), "neha": ("attendance", 28000),
               "neeraj": ("daily", 900), "alex": ("hourly", 250), "imran": ("fixed", 25000)}
        for key, role in staff.items():
            kind, rupees_ = pay.get(key, ("fixed", 20000))
            rule = SalaryRule.objects.create(gym=gym, staff=role, branch=role.branches.first() or home, pay_type=kind, rate_paise=rupees_ * 100,
                                             hours_per_day=Decimal(6) if kind == "hourly" else Decimal(0))
            if role.role != GymRole.ADMIN:
                SalaryItem.objects.create(rule=rule, kind="allowance", label="Travel", amount_paise=1000 * 100)
            if kind in ("fixed", "attendance") and rupees_ >= 22000:
                SalaryItem.objects.create(rule=rule, kind="deduction", label="PF", amount_paise=1800 * 100)
        last = clock.add_months(today.replace(day=1), -1)
        rnd = random.Random(7)
        for slip in payroll.generate(gym, last):
            # The demo's check-ins cover the last few weeks only, so last month's days are set as the admin would.
            if slip.pay_type != "fixed":
                slip = payroll.set_days(slip, max(slip.working_days - rnd.randint(0, 3), 0))
            payroll.approve(slip, meera)
            if slip.net_paise:
                payroll.pay(slip, amount_paise=slip.net_paise, method="bank", paid_on=today.replace(day=1), by=meera)
        payroll.generate(gym, today.replace(day=1))

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
        SalaryPayment.objects.filter(gym=gym).delete()
        PayslipLine.objects.filter(payslip__gym=gym).delete()
        Payslip.objects.filter(gym=gym).delete()
        SalaryRule.objects.filter(gym=gym).delete()  # its items go with it
        ExpenseDue.objects.filter(gym=gym).delete()
        RecurringExpense.objects.filter(gym=gym).delete()
        Expense.objects.filter(gym=gym).delete()
        StatementTick.objects.filter(gym=gym).delete()
        Reconciliation.objects.filter(gym=gym).delete()
        DrawerClose.objects.filter(gym=gym).delete()
        Refund.objects.filter(gym=gym).delete()
        Payment.objects.filter(gym=gym).delete()
        MoneyMove.objects.filter(gym=gym).delete()
        Account.objects.filter(gym=gym).delete()  # the branches they serve go with them
        Subscription.objects.filter(member__gym=gym).delete()
        Member.objects.filter(gym=gym).delete()
        InvoicePayment.objects.filter(gym=gym).delete()
        InvoiceLine.objects.filter(gym=gym).delete()
        Invoice.objects.filter(gym=gym).delete()
        Offer.objects.filter(gym=gym).delete()
        Plan.objects.filter(gym=gym).delete()
        users = list(GymRole.objects.filter(gym=gym).values_list("user_id", flat=True))
        gym.delete()
        User.objects.filter(id__in=users, gym_roles__isnull=True, is_staff=False).delete()
