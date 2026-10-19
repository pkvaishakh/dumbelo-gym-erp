# Production

API, worker and beat on AWS Mumbai (`ap-south-1`); web on Vercel. Commands are bash (AWS CloudShell, Git Bash or WSL).
Details behind each step: `docs/deploy.md` (setup) and `docs/operations.md` (backups, restore, opening a gym).

```
app.dumbelo.com (Vercel) ──► api.dumbelo.com (App Runner) ──► RDS Postgres 16
                                                          └─► ElastiCache Redis ◄── ECS Fargate: worker, beat
```

## 0. Shell

```bash
aws sts get-caller-identity
export AWS_REGION=ap-south-1
export ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export ECR=$ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/dumbelo-api
export NET='awsvpcConfiguration={subnets=[subnet-aaa,subnet-bbb],securityGroups=[sg-app]}'   # your private subnets + app SG
```

# Setup (once)

## 1. Database (RDS)

```bash
aws rds create-db-instance \
  --db-instance-identifier dumbelo-db --db-instance-class db.t4g.micro \
  --engine postgres --engine-version 16 --allocated-storage 20 --storage-type gp3 --storage-encrypted \
  --master-username dumbelo --manage-master-user-password \
  --db-name dumbelo --backup-retention-period 14 --preferred-backup-window 20:30-21:00 --deletion-protection \
  --no-publicly-accessible

aws rds describe-db-instances --db-instance-identifier dumbelo-db \
  --query 'DBInstances[0].[Endpoint.Address,MasterUserSecret.SecretArn]' --output text
aws secretsmanager get-secret-value --secret-id <secret arn> --query SecretString --output text
```

`DATABASE_URL=postgres://dumbelo:<password>@<endpoint>:5432/dumbelo`

## 2. Redis (ElastiCache console)

Redis OSS, cluster mode off, one `cache.t4g.micro`, same VPC/subnets.

```
CACHE_URL=redis://<host>:6379/1
CELERY_BROKER_URL=redis://<host>:6379/0        # rediss:// with encryption in transit
```

Security group: 5432 and 6379 open **only** to the app security group.

## 3. Secrets and settings

```bash
aws secretsmanager create-secret --name dumbelo/secret-key \
  --secret-string "$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
aws secretsmanager create-secret --name dumbelo/database-url --secret-string 'postgres://...'
aws secretsmanager create-secret --name dumbelo/field-encryption-key \
  --secret-string "$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
```

| Setting | Value |
|---|---|
| `PRODUCTION` | `true` |
| `SECRET_KEY` | secret `dumbelo/secret-key` |
| `ALLOWED_HOSTS` | `api.dumbelo.com` |
| `DATABASE_URL` | secret `dumbelo/database-url` |
| `CACHE_URL` | `redis://<host>:6379/1` |
| `CELERY_BROKER_URL` | `redis://<host>:6379/0` |
| `CORS_ALLOWED_ORIGINS` | `https://app.dumbelo.com` |
| `FIELD_ENCRYPTION_KEY` | secret `dumbelo/field-encryption-key` (back it up: losing it loses WhatsApp credentials) |
| `WHATSAPP_PROVIDER` | `whatsapp_cloud` |
| `DEBUG` | unset |

Same settings on the API, the worker, beat and the one-off task.

## 4. Image (ECR)

```bash
aws ecr create-repository --repository-name dumbelo-api --image-scanning-configuration scanOnPush=true
aws ecr get-login-password | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com
cd api
docker build -t $ECR:$(git rev-parse --short HEAD) -t $ECR:latest \
  --build-arg APP_VERSION=$(git rev-parse --short HEAD) --build-arg DEPLOYED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ) .
docker push --all-tags $ECR
```

## 5. Cluster, migrate task, first migration

```bash
aws ecs create-cluster --cluster-name dumbelo
```

Register task definition `dumbelo-migrate`: one container named **`migrate`**, image `$ECR:latest`,
command `["python","manage.py","migrate","--noinput"]`, settings from step 3, 0.25 vCPU / 0.5 GB, awsvpc,
log group `/ecs/dumbelo`.

```bash
aws ecs run-task --cluster dumbelo --task-definition dumbelo-migrate --launch-type FARGATE --network-configuration "$NET"
aws logs tail /ecs/dumbelo --since 10m --follow
```

## 6. API (App Runner console)

From ECR `dumbelo-api:latest`, manual deploys · port 8000 · 1 vCPU / 2 GB, 1–2 instances ·
health check HTTP `/api/health/` · VPC connector into the private subnets (with a NAT gateway) ·
instance role may read `dumbelo/*` secrets · settings from step 3.

## 7. Worker and beat (ECS services)

Same image and settings, 0.25 vCPU / 0.5 GB, private subnets, no load balancer, desired count **1** each.

| Service | Command |
|---|---|
| `dumbelo-worker` | `celery -A config worker --loglevel=info` |
| `dumbelo-beat` | `celery -A config beat --loglevel=info --schedule /tmp/celerybeat-schedule` (exactly one) |

## 8. Web (Vercel)

Import the repo · Root Directory `web` · env `NEXT_PUBLIC_API_URL=https://api.dumbelo.com` (Production and Preview) ·
production branch `main` · domain `app.dumbelo.com`.

## 9. Domains

App Runner → custom domain `api.dumbelo.com` (add its CNAMEs). Vercel → `app.dumbelo.com`.

## 10. Check

```bash
curl -s https://api.dumbelo.com/api/health/                                        # {"status":"ok","database":"ok"}
curl -s -D- -o /dev/null https://api.dumbelo.com/api/docs/ | grep -i strict-transport-security
curl -s -o /dev/null -w '%{http_code}\n' https://api.dumbelo.com/api/me/           # 401
```

Then Console → Server: everything Up.

## 11. Dumbelo admin (super admin)

```bash
cat > su.json <<'EOF'
{"containerOverrides": [{"name": "migrate",
  "command": ["python", "manage.py", "createsuperuser", "--noinput"],
  "environment": [
    {"name": "DJANGO_SUPERUSER_EMAIL", "value": "you@dumbelo.com"},
    {"name": "DJANGO_SUPERUSER_NAME", "value": "Your Name"},
    {"name": "DJANGO_SUPERUSER_PASSWORD", "value": "<a long password>"}]}]}
EOF
aws ecs run-task --cluster dumbelo --task-definition dumbelo-migrate --launch-type FARGATE \
  --network-configuration "$NET" --overrides file://su.json
rm su.json
```

Sign in at `https://app.dumbelo.com` → lands on the Console.

## 12. First gym

1. Console → More → Prices → **Add Price List** (no gym opens without one).
2. Console → Gyms → **New Gym** (name, short name, time zone, first branch, owner email).
3. The gym → Dumbelo plan: branch quota, billing day, WhatsApp mode; add setup charges.
4. WhatsApp: Console → More → WhatsApp → **Add Account** → Test Connection → templates →
   set Meta's webhook to the Callback URL and Verify token the Console shows, subscribe to `messages`.
5. Owner signs in, adds branches, plans, staff, members.

Never `seed_demo` or create gyms in the Django admin on production.

## 13. GitHub deploy button

Secret `AWS_ROLE_ARN` (OIDC role). Variables: `AWS_REGION`, `ECR_REPOSITORY=dumbelo-api`, `APPRUNNER_SERVICE_ARN`,
`ECS_CLUSTER=dumbelo`, `MIGRATE_TASK_DEFINITION=dumbelo-migrate`, `MIGRATE_SUBNETS`, `MIGRATE_SECURITY_GROUPS`,
`WORKER_SERVICE=dumbelo-worker`, `BEAT_SERVICE=dumbelo-beat`, `API_HEALTH_URL=https://api.dumbelo.com/api/health/`.
Environment `production` (add yourself as reviewer).

# Run and manage

## Deploy

GitHub → **Actions → Deploy API → Run workflow** (needs green CI on that commit). It builds, migrates, deploys
App Runner, restarts worker and beat, checks health. Web deploys itself from `main`.

Before a deploy whose migration changes data:

```bash
aws rds create-db-snapshot --db-instance-identifier dumbelo-db --db-snapshot-identifier dumbelo-before-$(git rev-parse --short HEAD)
```

## Roll back

```bash
aws apprunner update-service --service-arn <arn> --source-configuration \
  "ImageRepository={ImageIdentifier=$ECR:<good-short-sha>,ImageRepositoryType=ECR}"
```

Then set it back to `:latest` (same command), or rerun Deploy from the good commit. Migrations aren't undone.

## Any manage.py command

```bash
run() {  # run "write_invoices --day 2026-11-01"
  printf '{"containerOverrides":[{"name":"migrate","command":["sh","-c","exec python manage.py %s"]}]}' "$1" > cmd.json
  aws ecs run-task --cluster dumbelo --task-definition dumbelo-migrate --launch-type FARGATE \
    --network-configuration "$NET" --overrides file://cmd.json && rm cmd.json
}
run "migrate --noinput"
run "write_invoices --day 2026-11-01"              # a missed billing day
run "replay_webhook_events --failed"
run "replay_webhook_events --since 2026-10-18T09:00+05:30"
run "create_gym --name 'Pulse Fitness' --slug pulse --branch Kochi --owner-email anil@pulse.in --owner-name 'Anil Menon'"
run "verify_counts --gym pulse"
run "check --deploy"
aws logs tail /ecs/dumbelo --since 10m --follow    # its output
```

Jobs can also be started from Console → Server → **Run Now** (reminders, invoices, webhook replay).

## Logs

```bash
aws logs tail /ecs/dumbelo --since 1h --follow     # worker, beat, one-off tasks
```

API: App Runner console → the service → Logs.

## Stop / start jobs

```bash
aws ecs update-service --cluster dumbelo --service dumbelo-beat   --desired-count 0
aws ecs update-service --cluster dumbelo --service dumbelo-worker --desired-count 0
aws ecs update-service --cluster dumbelo --service dumbelo-worker --desired-count 1
aws ecs update-service --cluster dumbelo --service dumbelo-beat   --desired-count 1   # never more than 1
aws ecs update-service --cluster dumbelo --service dumbelo-worker --force-new-deployment   # restart
```

## Pause / resume the API

```bash
aws apprunner pause-service  --service-arn <arn>
aws apprunner resume-service --service-arn <arn>
```

## Rotate the encryption key

```bash
python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
```

1. `FIELD_ENCRYPTION_KEY=<new>,<old>` on API, worker, beat, task → Deploy.
2. `run "rotate_credentials"`
3. `FIELD_ENCRYPTION_KEY=<new>` → Deploy. Keep `<old>` 14 days in `dumbelo/field-encryption-key-retired`.

## Rotate SECRET_KEY

```bash
aws secretsmanager put-secret-value --secret-id dumbelo/secret-key \
  --secret-string "$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
```

Then Deploy. Signs everyone out.

## Backups

```bash
aws rds describe-db-instances --db-instance-identifier dumbelo-db --query \
  'DBInstances[0].{retention:BackupRetentionPeriod,encrypted:StorageEncrypted,deletionProtection:DeletionProtection,latestRestorable:LatestRestorableTime}'
aws rds modify-db-instance --db-instance-identifier dumbelo-db --apply-immediately \
  --backup-retention-period 14 --preferred-backup-window 20:30-21:00 --deletion-protection
```

## Restore drill (monthly)

```bash
DRILL=dumbelo-drill-$(date -u +%Y%m); T=$(date -u -d '15 minutes ago' +%Y-%m-%dT%H:%M:%SZ); GYM=<slug>
read SUBNETS SG <<<"$(aws rds describe-db-instances --db-instance-identifier dumbelo-db \
  --query 'DBInstances[0].[DBSubnetGroup.DBSubnetGroupName,VpcSecurityGroups[0].VpcSecurityGroupId]' --output text)"
aws rds restore-db-instance-to-point-in-time --source-db-instance-identifier dumbelo-db \
  --target-db-instance-identifier $DRILL --restore-time $T --db-instance-class db.t4g.micro --no-publicly-accessible \
  --db-subnet-group-name $SUBNETS --vpc-security-group-ids $SG --manage-master-user-password
aws rds wait db-instance-available --db-instance-identifier $DRILL
run "verify_counts --gym $GYM --until $T"           # live; then the copy: docs/operations.md step 4
aws rds delete-db-instance --db-instance-identifier $DRILL --skip-final-snapshot --delete-automated-backups
```

Counts must match. Log it in `docs/operations.md` → Drill log.

## Restore for real

1. Stop beat and worker (above).
2. Restore to just before the problem (drill commands, name `dumbelo-db-restored`), check counts.
3. Put the copy's URL in `dumbelo/database-url` → Deploy.
4. Start worker and beat.
5. Tell gyms what time their data runs to.
6. Turn on the copy's backups and deletion protection; keep the old instance 14 days.

## Health at a glance

Console → **Home** (gyms, money, what needs you) and Console → **Server** (database, Redis, worker, beat, jobs).

```bash
curl -s https://api.dumbelo.com/api/health/
```

## Before a release

```bash
cd api && pip install pip-audit && pip-audit
cd web && npm audit
run "check --deploy"
```

## Cost

Around $100–120/month: App Runner, RDS micro, ElastiCache micro, 2 Fargate tasks, NAT gateway. Vercel Pro $20.
