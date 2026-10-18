# Operations

Running Rackline once it is deployed (`docs/deploy.md`): the database's backups, the monthly restore drill, putting
a backup back for real, and opening a real gym. The commands assume the shell from deploy.md
(`AWS_REGION=ap-south-1`, the `rackline` ECS cluster, the `rackline-migrate` one-off task).

## Backups

The database is the only thing that needs one. Everything else can be rebuilt or isn't worth keeping:

| What | Where it lives | If it's lost |
|---|---|---|
| Gyms, members, money, check-ins, messages | RDS Postgres `rackline-db` | **Restore it** (below) |
| Rate-limit counts and the job queue | ElastiCache Redis | Nothing to restore. Beat queues every job again on its next tick; a Run Now that was waiting is pressed again |
| The API image | ECR, tagged by commit | Rebuild from git (`docs/deploy.md` step 4) |
| The web app | Vercel, built from `main` | Redeploy from Vercel |
| `SECRET_KEY`, `DATABASE_URL`, `FIELD_ENCRYPTION_KEY` | Secrets Manager | A deleted secret can be brought back within its recovery window (7–30 days). **Losing `FIELD_ENCRYPTION_KEY` loses every WhatsApp number's credentials**: they would have to be pasted into the Console again |

RDS keeps automated backups for **14 days**: a nightly snapshot plus the database's log, so it can go back to any
second in those 14 days (point-in-time restore), usually up to about five minutes ago. They are encrypted, like
the database. Check that it is still set up so:

```bash
aws rds describe-db-instances --db-instance-identifier rackline-db --query \
  'DBInstances[0].{retention:BackupRetentionPeriod,window:PreferredBackupWindow,encrypted:StorageEncrypted,deletionProtection:DeletionProtection,latestRestorable:LatestRestorableTime}'
```

It should say `retention: 14`, `encrypted: true` and `deletionProtection: true`. If it doesn't, set them. The
backup window is in UTC; 20:30–21:00 UTC is 2:00–2:30 AM in India, when no gym is open:

```bash
aws rds modify-db-instance --db-instance-identifier rackline-db --apply-immediately \
  --backup-retention-period 14 --preferred-backup-window 20:30-21:00 --deletion-protection
```

Before a deploy whose migration changes data (deploy.md, "A migration that needs care"), also take a snapshot by
hand. Unlike the automated ones, it stays until you delete it:

```bash
aws rds create-db-snapshot --db-instance-identifier rackline-db --db-snapshot-identifier rackline-before-$(git rev-parse --short HEAD)
```

**The encryption key and old backups.** A backup holds the WhatsApp credentials encrypted with the key that was
current when it was taken. After rotating `FIELD_ENCRYPTION_KEY` (deploy.md), keep the old key for 14 more days in
its own secret (`rackline/field-encryption-key-retired`), and delete it only then. A restore from before the
rotation needs it put back after the new key: `FIELD_ENCRYPTION_KEY=<new>,<old>`.

## The restore drill (monthly)

Once a month, on a weekday morning, prove that a backup can be put back and that it holds what the live database
held. It takes about 45 minutes, most of it waiting for AWS, and changes nothing live: the copy is a new instance
that the app never uses, and it is deleted at the end.

**1. Pick the moment to go back to, and what the copy needs.** Fifteen minutes ago is safely inside what RDS can
restore (`latestRestorable` above).

```bash
DRILL=rackline-drill-$(date -u +%Y%m)
T=$(date -u -d '15 minutes ago' +%Y-%m-%dT%H:%M:%SZ)    # macOS: date -u -v-15M +%Y-%m-%dT%H:%M:%SZ
GYM=<a gym's short name, e.g. the pilot gym's>
read SUBNETS SG <<<"$(aws rds describe-db-instances --db-instance-identifier rackline-db \
  --query 'DBInstances[0].[DBSubnetGroup.DBSubnetGroupName,VpcSecurityGroups[0].VpcSecurityGroupId]' --output text)"
echo "$DRILL $T $SUBNETS $SG"
```

**2. Restore a copy to that moment.** Note the time you start: how long this takes is how long a real restore
takes.

```bash
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier rackline-db --target-db-instance-identifier $DRILL \
  --restore-time $T --db-instance-class db.t4g.micro --no-publicly-accessible \
  --db-subnet-group-name $SUBNETS --vpc-security-group-ids $SG --manage-master-user-password
aws rds wait db-instance-available --db-instance-identifier $DRILL    # 10–30 minutes
```

`--manage-master-user-password` gives the copy its own password in Secrets Manager. If your AWS CLI says it doesn't
know that option, update the CLI, or leave the option out: the copy then keeps the live database's password as it
was at `$T`.

**3. Count the live database's rows as they were at `$T`.** `verify_counts` counts the gym's members, payments
and check-ins written by then. Rows are never deleted (members are archived, payments voided), so these numbers
can't change after `$T`, however busy the gym is now.

```bash
cat > live.json <<EOF
{"containerOverrides": [{"name": "migrate",
  "command": ["python", "manage.py", "verify_counts", "--gym", "$GYM", "--until", "$T"]}]}
EOF
aws ecs run-task --cluster rackline --task-definition rackline-migrate --launch-type FARGATE \
  --network-configuration 'awsvpcConfiguration={subnets=[subnet-aaa,subnet-bbb],securityGroups=[sg-app]}' \
  --overrides file://live.json
```

**4. Count the copy the same way.** Its address and password:

```bash
aws rds describe-db-instances --db-instance-identifier $DRILL \
  --query 'DBInstances[0].[Endpoint.Address,MasterUserSecret.SecretArn]' --output text
aws secretsmanager get-secret-value --secret-id <that arn> --query SecretString --output text   # {"username", "password"}
```

The same one-off task, pointed at the copy. `DATABASE_URL` stays the live one's: the command swaps it for the
copy's only inside this one task.

```bash
cat > copy.json <<EOF
{"containerOverrides": [{"name": "migrate",
  "environment": [{"name": "DRILL_DATABASE_URL", "value": "postgres://rackline:<password>@<copy address>:5432/rackline"}],
  "command": ["sh", "-c", "DATABASE_URL=\"\$DRILL_DATABASE_URL\" exec python manage.py verify_counts --gym $GYM --until $T"]}]}
EOF
aws ecs run-task --cluster rackline --task-definition rackline-migrate --launch-type FARGATE \
  --network-configuration 'awsvpcConfiguration={subnets=[subnet-aaa,subnet-bbb],securityGroups=[sg-app]}' \
  --overrides file://copy.json
rm live.json copy.json   # copy.json holds the copy's password
```

**5. Compare.** Both tasks print to CloudWatch:

```bash
aws logs tail /ecs/rackline --since 15m
```

Each printed this, for the same moment:

```
Rows written by 2026-11-02T03:45:00+00:00
pilot-gym  Pilot Gym
  members         412   9 archived
  payments        980   4 voided, 21,46,500 rupees recorded
  check-ins     18304
```

Members, payments and check-ins must be **the same on both**. That is the check: the copy holds every row the live
database held at `$T`. The archived, voided and rupees figures are what those rows say now, so they can differ only
if someone archived a member or corrected or voided a payment after `$T`. If one does differ, the audit log on
the live side says who, and when.

If a count differs, keep the copy, don't delete it, and find out why before the next deploy. A restore you can't
trust is the thing this drill exists to catch.

**6. Delete the copy** (it costs about as much as the live database while it runs):

```bash
aws rds delete-db-instance --db-instance-identifier $DRILL --skip-final-snapshot --delete-automated-backups
```

**7. Write it down** in the log at the end of this page: the date, `$T`, how many minutes step 2 took, and
whether the counts matched.

## Restoring for real

When data is lost or broken (a bad migration, rows changed by mistake), go back to just before it happened.
Everything written after that moment is lost, so pick it with care: the audit log and the API's log say when things
went wrong.

1. **Stop the jobs**, so nothing is sent from a database about to be replaced:
   ```bash
   aws ecs update-service --cluster rackline --service rackline-beat --desired-count 0
   aws ecs update-service --cluster rackline --service rackline-worker --desired-count 0
   ```
2. **Restore a copy** to that moment, exactly as drill steps 1–2 (call it `rackline-db-restored`), and **check it**
   with drill steps 3–5, giving `--until` the moment you restored to.
3. **Point the API at it.** Put the copy's address and password into the `rackline/database-url` secret, then deploy
   again (Actions → Deploy API → Run workflow) so App Runner and the jobs pick it up. The deploy runs the migrations,
   which brings a copy from before a deploy up to date. If the bad change *was* a migration, deploy the last good
   commit instead (deploy.md, "Going back").
4. **Start the jobs again**: the same commands with `--desired-count 1`. Beat runs the day's reminders and invoices
   again; both are safe to repeat, so nothing that already went out goes twice.
5. **Tell the gyms** what time their data now runs to. Payments and check-ins after it must be entered again.
6. **Make the copy the live database for good**: turn on its 14-day backups and deletion protection (the command
   under Backups, with its name), and use its name in place of `rackline-db` everywhere on this page.
7. **Keep the old instance** for 14 days in case something is needed from it, then turn off its deletion protection
   and delete it.

## Opening a real gym

The Console does it (session 9). For each new gym:

1. **Prices exist** (Console → Prices). No gym opens without a price list.
2. **Console → New Gym**: its name, short name, time zone, first branch, and the owner's email. A new owner gets a
   first password to pass on; one who already signs in to Rackline keeps theirs. (`python manage.py create_gym` does
   the same from the command line.)
3. **Its Rackline plan** (the gym's screen → Rackline plan): the branch quota, the billing day, and the WhatsApp mode.
   Add one-time setup charges (WhatsApp, machines) as charges for the first invoice.
4. **WhatsApp**: on Rackline's shared number, nothing more to do. On its own number, add the account from the gym's
   screen, run Test Connection, add its approved templates, and set the webhook in Meta's app (deploy.md, step 3).
5. **The owner signs in** on their phone and adds: the other branches, plans and offers, staff, and members (each one
   with their current plan and what they still owe).
6. **Check it with them**: add a member, sell a plan, collect a payment, check someone in at the desk and by the wall
   QR. Confirm the first morning's reminders went (Console → WhatsApp log) and that Console → Server is all up.

Never run `seed_demo` against the live database: it builds the demo gym, not a real one.

## Drill log

| Date | Restored to (UTC) | Minutes to restore | Counts matched | By |
|---|---|---|---|---|
| | | | | |
