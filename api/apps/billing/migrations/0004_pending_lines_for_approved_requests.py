"""Branch requests approved before invoices existed get the pending line that bills them on the next invoice,
worded the way `services.pro_rata_line` words new ones."""
from django.db import migrations


def _label(day):
    return f"{day.day} {day:%b}"


def lines_for_approved(apps, schema_editor):
    BranchRequest = apps.get_model("billing", "BranchRequest")
    InvoiceLine = apps.get_model("billing", "InvoiceLine")
    rows = []
    for req in BranchRequest.objects.filter(status="approved", invoice_line__isnull=True, pro_rata_paise__isnull=False).iterator():
        days = (req.charged_to - req.charged_from).days + 1
        what = f"{req.count} branch" if req.count == 1 else f"{req.count} branches"
        rows.append(InvoiceLine(
            gym_id=req.gym_id, kind="branches_pro_rata", branch_request=req, starts=req.charged_from, ends=req.charged_to,
            description=f"{what} added, {_label(req.charged_from)} to {_label(req.charged_to)} ({days} of {req.period_days} days)",
            quantity=req.count, rate_paise=req.rate_paise, amount_paise=req.pro_rata_paise, added_by_id=req.decided_by_id,
        ))
    InvoiceLine.objects.bulk_create(rows, batch_size=500)


class Migration(migrations.Migration):
    dependencies = [("billing", "0003_invoices")]

    operations = [migrations.RunPython(lines_for_approved, migrations.RunPython.noop)]
