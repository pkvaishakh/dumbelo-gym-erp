"""Where the gym's money sits: each branch's cash in hand, and the bank accounts its branches pay into."""
from datetime import date

from django.core.validators import MinValueValidator
from django.db import connections, models
from django.db.models import Q

from apps.core.models import GymScoped

#: How a payment or an expense moved money that isn't cash: these land in, or come out of, the branch's bank account.
CASH = "cash"


class AccountQuerySet(models.QuerySet):
    def for_money(self, branch_id: int, method: str, *, on: date):
        """The account money taken or paid at a branch on day `on` moves: its cash in hand for cash, its bank account
        for UPI, card and bank transfer. None when the gym hasn't set that one up, so the money is in no balance, and
        None when the account was added after `on`: its opening balance already counts that money.

        Call it inside the transaction that records the money: it holds the account until then (see `_hold`)."""
        if method == CASH:
            found = self.filter(kind=Account.CASH, branch_id=branch_id, is_active=True, opened_on__lte=on).first()
        else:
            found = self.filter(kind=Account.BANK, links__branch_id=branch_id, is_active=True, opened_on__lte=on).first()
        return found if found is not None and self._hold(found.pk) else None

    def _hold(self, pk: int) -> bool:
        """Key-share lock the account until the transaction ends, and answer whether it is still in use.

        An admin deactivating it holds it for update, so the two wait for each other: either this money is recorded
        first and `deactivate` then finds the account isn't empty, or the deactivation goes first and this finds it
        deactivated, so the money goes in no balance (its branch has no account then, as for money a moment later).
        A key-share lock is the one a payment's own foreign key already takes, so payments at the same desk never
        wait for each other. Django has no FOR KEY SHARE, hence the SQL. SQLite has no row locks; it runs one write
        at a time anyway."""
        conn = connections[self.db]
        if conn.vendor != "postgresql":
            return True
        table = conn.ops.quote_name(Account._meta.db_table)
        with conn.cursor() as cur:
            cur.execute(f"SELECT is_active FROM {table} WHERE id = %s FOR KEY SHARE", [pk])
            row = cur.fetchone()
        return bool(row and row[0])


class Account(GymScoped):
    """Cash in hand at one branch, or a bank account that one or more branches use.

    Its balance is the opening balance plus everything recorded against it since it was added: payments taken in,
    expenses paid out, and money moved in or out (`services.with_balance`). Payments and expenses keep the account
    they hit, so moving a branch to another bank account changes where new money goes, never where old money went.
    Never deleted: deactivated instead.
    """

    CASH, BANK = "cash", "bank"
    KINDS = [(CASH, "Cash in hand"), (BANK, "Bank account")]

    kind = models.CharField(max_length=4, choices=KINDS)
    name = models.CharField(max_length=80, blank=True, help_text="Bank accounts: what the gym calls it, like HDFC current account")
    branch = models.ForeignKey("gyms.Branch", null=True, blank=True, on_delete=models.PROTECT, related_name="cash_accounts",
                               help_text="Cash in hand only: the branch whose cash it is")
    branches = models.ManyToManyField("gyms.Branch", through="BranchAccount", blank=True, related_name="bank_accounts",
                                      help_text="Bank accounts only: the branches whose money goes in and out of it")
    bank_name = models.CharField(max_length=80, blank=True)
    account_number = models.CharField(max_length=20, blank=True)
    ifsc = models.CharField(max_length=11, blank=True)
    opening_balance_paise = models.BigIntegerField(default=0, validators=[MinValueValidator(0)], help_text="What it held the day it was added")
    opened_on = models.DateField(help_text="The day it was added to Rackline: money recorded from then on moves its balance")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="+")

    objects = AccountQuerySet.as_manager()

    class Meta:
        ordering = ["kind", "name", "id"]
        constraints = [
            models.UniqueConstraint(fields=["branch"], condition=Q(kind="cash"), name="one_cash_account_per_branch"),
            models.UniqueConstraint(fields=["gym", "account_number"], condition=Q(kind="bank"), name="bank_account_number_unique_in_gym"),
            models.CheckConstraint(condition=Q(kind="cash", branch__isnull=False) | Q(kind="bank", branch__isnull=True), name="only_cash_has_a_branch"),
            models.CheckConstraint(condition=Q(opening_balance_paise__gte=0), name="opening_balance_not_negative"),
        ]
        indexes = [models.Index(fields=["gym", "kind", "is_active"], name="account_gym_kind_active")]

    def __str__(self):
        return self.label

    @property
    def label(self) -> str:
        """The name people read: "HDFC current account", or "Koramangala cash". Load `branch` with the row."""
        return f"{self.branch.name} cash" if self.kind == self.CASH else self.name


class BranchAccount(models.Model):
    """The bank account a branch uses: its UPI, card and bank-transfer payments go in, its bank expenses come out.
    One per branch; several branches can share one account. Changing it moves new money only."""

    branch = models.OneToOneField("gyms.Branch", on_delete=models.CASCADE, related_name="bank_link")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="links")

    def __str__(self):
        return f"{self.branch} → {self.account}"


class MoneyMove(GymScoped):
    """Money that is neither a payment nor an expense, so it never counts as income or spending: put in from outside
    (the owner adds funds), taken out (the owner draws some, bank charges), or moved between two of the gym's
    accounts (cash banked, cash drawn, one branch's cash sent to another). Voided with a reason, never deleted."""

    DEPOSIT, WITHDRAWAL, TRANSFER = "deposit", "withdrawal", "transfer"
    KINDS = [(DEPOSIT, "Deposit"), (WITHDRAWAL, "Withdrawal"), (TRANSFER, "Transfer")]

    kind = models.CharField(max_length=10, choices=KINDS)
    from_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.PROTECT, related_name="moves_out")
    to_account = models.ForeignKey(Account, null=True, blank=True, on_delete=models.PROTECT, related_name="moves_in")
    amount_paise = models.PositiveBigIntegerField()
    moved_on = models.DateField()
    note = models.CharField(max_length=200, blank=True)
    created_by = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="+")
    voided = models.BooleanField(default=False)
    void_reason = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-moved_on", "-id"]
        constraints = [
            models.CheckConstraint(condition=Q(amount_paise__gt=0), name="money_move_positive"),
            models.CheckConstraint(
                condition=Q(kind="deposit", from_account__isnull=True, to_account__isnull=False)
                | Q(kind="withdrawal", from_account__isnull=False, to_account__isnull=True)
                | (Q(kind="transfer", from_account__isnull=False, to_account__isnull=False) & ~Q(from_account=models.F("to_account"))),
                name="money_move_accounts_match_kind",
            ),
        ]
        indexes = [models.Index(fields=["gym", "moved_on"], name="moneymove_gym_moved_on")]


class DrawerClose(GymScoped):
    """The desk's count of a branch's cash at the end of a day, against what its cash in hand should hold then.

    One per branch per day; counting again the same day replaces it until an admin settles it. A difference is
    settled by an admin as a deposit (more cash than expected) or a withdrawal (less), so the balance stays the sum of
    what was recorded and the count never edits it. Voiding that move un-settles the count."""

    branch = models.ForeignKey("gyms.Branch", on_delete=models.PROTECT, related_name="drawer_closes")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="drawer_closes", help_text="The branch's cash in hand, as counted")
    day = models.DateField(help_text="The gym's local day it closes")
    counted_paise = models.BigIntegerField(validators=[MinValueValidator(0)])
    expected_paise = models.BigIntegerField(help_text="The cash in hand's balance when it was counted")
    note = models.CharField(max_length=200, blank=True)
    counted_by = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="+")
    counted_at = models.DateTimeField()
    settled_by = models.ForeignKey("gyms.GymRole", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    settled_at = models.DateTimeField(null=True, blank=True)
    settle_reason = models.CharField(max_length=200, blank=True)
    settle_move = models.OneToOneField(MoneyMove, null=True, blank=True, on_delete=models.PROTECT, related_name="drawer_close",
                                       help_text="The deposit or withdrawal that settled the difference")

    class Meta:
        ordering = ["-day", "branch__name"]
        constraints = [
            models.UniqueConstraint(fields=["branch", "day"], name="one_drawer_close_per_branch_per_day"),
            models.CheckConstraint(condition=Q(counted_paise__gte=0), name="drawer_counted_not_negative"),
        ]
        indexes = [models.Index(fields=["gym", "day"], name="drawerclose_gym_day")]

    def __str__(self):
        return f"{self.branch} cash, {self.day}"

    @property
    def difference_paise(self) -> int:
        """Above zero: more cash than expected. Below zero: short."""
        return self.counted_paise - self.expected_paise


class Reconciliation(GymScoped):
    """A bank account checked against the bank's own statement: up to `up_to`, the opening balance plus the entries
    ticked as on the bank's statement came to `bank_balance_paise`, what the bank said. Those ticks are then locked."""

    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="reconciliations")
    up_to = models.DateField()
    bank_balance_paise = models.BigIntegerField(help_text="The bank's balance at the end of `up_to`")
    by = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="+")

    class Meta:
        ordering = ["-up_to", "-id"]

    def __str__(self):
        return f"{self.account} up to {self.up_to}"


class StatementTick(GymScoped):
    """One entry on a bank account's statement ticked as on the bank's statement too: a payment, an expense, a refund
    or a money move (a transfer between two bank accounts is ticked on each side apart). Keeps the entry's day and signed amount
    as they were when ticked; changing or voiding the entry drops the tick, and a reconciled one can't change at all
    until an admin un-reconciles it."""

    PAYMENT, EXPENSE, MOVE, REFUND = "payment", "expense", "move", "refund"
    KINDS = [(PAYMENT, "Payment"), (EXPENSE, "Expense"), (MOVE, "Money move"), (REFUND, "Refund")]

    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="ticks")
    kind = models.CharField(max_length=8, choices=KINDS)
    entry_id = models.PositiveBigIntegerField()
    on = models.DateField(help_text="The entry's day on this account's statement")
    amount_paise = models.BigIntegerField(help_text="Signed: above zero came in, below zero went out")
    reconciliation = models.ForeignKey(Reconciliation, null=True, blank=True, on_delete=models.PROTECT, related_name="ticks",
                                       help_text="Set once reconciled: the entry is locked until an admin un-reconciles it")
    ticked_by = models.ForeignKey("gyms.GymRole", on_delete=models.PROTECT, related_name="+")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["account", "kind", "entry_id"], name="one_tick_per_entry_per_account")]
        indexes = [models.Index(fields=["account", "on"], name="tick_account_on"), models.Index(fields=["kind", "entry_id"], name="tick_entry")]
