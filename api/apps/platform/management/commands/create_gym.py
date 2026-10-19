"""Open a gym from the command line, the same way the Console's New Gym does (`services.create_gym`).

    python manage.py create_gym --name "Iron House" --slug iron-house --branch Indiranagar \
        --owner-email meera@ironhouse.in --owner-name "Meera Iyer"

A new owner login gets the password given with --owner-password, or one made up here and printed once to pass
on. An owner who already signs in to Dumbelo (at another gym) keeps their password.
"""
import secrets

from django.core.management.base import BaseCommand, CommandError

from apps.audit.models import record
from apps.core.errors import RuleBroken
from apps.platform import services


class Command(BaseCommand):
    help = "Create a gym with its first branch and its owner admin (the Console's New Gym)."

    def add_arguments(self, parser):
        parser.add_argument("--name", required=True, help="The gym's name")
        parser.add_argument("--slug", required=True, help="Short name the app sends as X-Gym: lowercase letters, numbers, dashes")
        parser.add_argument("--branch", required=True, help="The first branch's name")
        parser.add_argument("--owner-email", required=True)
        parser.add_argument("--owner-name", default="", help="Needed when the owner is new to Dumbelo")
        parser.add_argument("--owner-password", default="", help="A first password for a new login; made up if left out")
        parser.add_argument("--timezone", default="Asia/Kolkata")
        parser.add_argument("--billing-email", default="", help="Where Dumbelo sends invoices; the owner's email if left out")

    def handle(self, *args, **o):
        password = o["owner_password"]
        made_up = not password and services.find_login(o["owner_email"]) is None
        if made_up:
            password = secrets.token_urlsafe(9)
        try:
            made = services.create_gym(
                name=o["name"], slug=o["slug"].strip().lower(), timezone_name=o["timezone"], branch=o["branch"],
                owner_email=o["owner_email"], owner_name=o["owner_name"], owner_password=password or None, billing_email=o["billing_email"],
            )
        except RuleBroken as e:
            raise CommandError(str(e.detail))
        record(None, "gym.created", made.gym, None, {"slug": made.gym.slug, "owner": made.owner.user.email, "new_login": made.new_login}, gym=made.gym)
        self.stdout.write(self.style.SUCCESS(f"{made.gym.name} is ready (X-Gym: {made.gym.slug}), on trial."))
        if not made.new_login:
            self.stdout.write(f"{made.owner.user.email} already signs in to Dumbelo and keeps their password.")
        elif made_up:
            self.stdout.write(f"{made.owner.user.email} signs in with this first password: {password}  (shown once: pass it on)")
        else:
            self.stdout.write(f"{made.owner.user.email} signs in with the password you gave.")
