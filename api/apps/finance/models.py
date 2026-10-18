"""Where the gym's money sits: each branch's cash in hand, and the bank accounts its branches pay into."""
from datetime import date

from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q

from apps.core.models import GymScoped

#: How a payment or an expense moved money that isn't cash: these land in, or come out of, the branch's bank account.
CASH = "cash"


class AccountQuerySet(models.QuerySet):
    def for_money(self, branch_id: int, method: str, *, on: date):
        """The account money taken or paid at a branch on day `on` moves: its cash in hand for cash, its bank account
        for UPI, card and bank transfer. None when the gym hasn't set that one up, so the money is in no balance, and
        None when the account was added after `on`: its opening balance already counts that money."""
        if method == CASH:
            return self.filter(kind=Account.CASH, branch_id=branch_id, is_active=True, opened_on__lte=on).first()
        return self.filter(kind=Account.BANK, links__branch_id=branch_id, is_active=True, opened_on__lte=on).first()


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
