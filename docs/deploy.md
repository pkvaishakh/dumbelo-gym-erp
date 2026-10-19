# Deploy

How Dumbelo gets onto the internet: the API and its database on AWS Mumbai (`ap-south-1`), the web app on
Vercel. Follow this page top to bottom once; after that, deploying again is one button
(["Deploying again"](#deploying-again)).

Everything here is done with the gym owner's own AWS and Vercel accounts. Nothing in this repository holds a
real secret, and nothing in it has to.

```
app.dumbelo.com   Vercel ──────────► api.dumbelo.com   App Runner (gunicorn, 2 instances)
                                            │
                                            ├── RDS Postgres 16      the gym's data
                                            └── ElastiCache Redis    rate-limit counts + the job queue
                                                     ▲
                                     ECS Fargate ────┘  worker (runs the jobs) and beat (the clock)
```

Three processes, one image. The API, the Celery worker and beat all run `api/Dockerfile`; only the command
differs. App Runner runs HTTP services only, so the worker and beat run as two small ECS Fargate services.

## What you need first

- An AWS account with admin access, and the AWS CLI signed in to it (`aws sts get-caller-identity`).
- Docker on your machine, to build the image the first time.
- A Vercel account connected to the GitHub repository.
- A domain. This page uses `dumbelo.com`: `api.dumbelo.com` for the API, `app.dumbelo.com` for the app.
- A WhatsApp Cloud API number with its token, phone number id and app secret, if you want reminders from day one.
  It is added in the Console once the API is up (WhatsApp → Add Account), not as a setting.

Set these once in your shell, and the commands below can be copied as they are:

```bash
export AWS_REGION=ap-south-1
export ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export ECR=$ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/dumbelo-api
```

## 1. The database (RDS Postgres)

One `db.t4g.micro`, 20 GB gp3, PostgreSQL 16, **not** publicly accessible, in the VPC the API will run in.
Private subnets if the account has them; in a plain default VPC, `--no-publicly-accessible` and the security
group below keep it off the internet anyway. Backups and the monthly restore drill are in `docs/operations.md`;
the 14-day retention, encryption at rest and deletion protection are set here, at the start.

```bash
aws rds create-db-instance \
  --db-instance-identifier dumbelo-db --db-instance-class db.t4g.micro \
  --engine postgres --engine-version 16 --allocated-storage 20 --storage-type gp3 --storage-encrypted \
  --master-username dumbelo --manage-master-user-password \
  --db-name dumbelo --backup-retention-period 14 --preferred-backup-window 20:30-21:00 --deletion-protection \
  --no-publicly-accessible
```

`--manage-master-user-password` keeps the password in Secrets Manager instead of your shell history. Read it
(and the endpoint) when the instance is `available`:

```bash
aws rds describe-db-instances --db-instance-identifier dumbelo-db \
  --query 'DBInstances[0].[Endpoint.Address,MasterUserSecret.SecretArn]' --output text
```

The connection string the API wants is one value, `DATABASE_URL`:

```
postgres://dumbelo:<password>@dumbelo-db.xxxx.ap-south-1.rds.amazonaws.com:5432/dumbelo
```

## 2. Redis (ElastiCache)

Redis does two jobs: it holds the rate-limit counts that must be shared by every API worker (`CACHE_URL`), and
it is the queue the Celery worker takes jobs from (`CELERY_BROKER_URL`).

Create it in the ElastiCache console: Redis OSS, cluster mode off, one `cache.t4g.micro` node, in the same VPC
and subnets as the database. That is plenty for a pilot. Use two different databases on the one node, so a
`FLUSHDB` of the cache can't take the job queue with it:

```
CACHE_URL=redis://dumbelo-cache.xxxx.cache.amazonaws.com:6379/1
CELERY_BROKER_URL=redis://dumbelo-cache.xxxx.cache.amazonaws.com:6379/0
```

If you turn on encryption in transit, the scheme becomes `rediss://`.

Give the database and the cache a security group that allows port 5432 / 6379 **only** from the security group
the API and the jobs run in. Nothing about Dumbelo is reachable from the internet except the API itself.

## 3. The settings a server must have

The API refuses to start with `PRODUCTION=true` unless it has been told all five of `SECRET_KEY`,
`ALLOWED_HOSTS`, `DATABASE_URL`, `CACHE_URL` and `FIELD_ENCRYPTION_KEY` (`api/config/env.py`), so a
half-configured server fails loudly at boot instead of quietly serving with a default secret.

| Setting | Value on the pilot server | Why |
|---|---|---|
| `PRODUCTION` | `true` | Turns on HTTPS-only cookies, HSTS, the redirect and these checks |
| `SECRET_KEY` | 50+ random characters, this server's own | Signs the sign-in tokens. Changing it signs everyone out |
| `ALLOWED_HOSTS` | `api.dumbelo.com` | The names the API answers on |
| `DATABASE_URL` | from step 1 | Postgres |
| `CACHE_URL` | from step 2, db 1 | Shared rate-limit counts |
| `CELERY_BROKER_URL` | from step 2, db 0 | The job queue. Empty means jobs run inside the request: never on a server |
| `CORS_ALLOWED_ORIGINS` | `https://app.dumbelo.com` | Which site may call the API from a browser. The default is localhost, so this must be set |
| `FIELD_ENCRYPTION_KEY` | a Fernet key, this server's own (below) | Encrypts the WhatsApp credentials in the database. Losing it loses them |
| `WHATSAPP_PROVIDER` | `whatsapp_cloud` | Posts templates to Meta's Cloud API from each gym's number. `fake` (the default) sends nothing |
| `DEBUG` | leave unset | `PRODUCTION=true` with `DEBUG=True` refuses to start |

Set by the image itself, nothing to do: `APP_VERSION` (the commit) and `DEPLOYED_AT` (when the deploy workflow
built it, UTC), which the Console's Server screen shows. The workflow passes both to `docker build`; an image built
by hand says `dev` unless you pass `--build-arg APP_VERSION=… --build-arg DEPLOYED_AT=…` too.

Optional, with sensible defaults in `api/config/settings.py`: `WHATSAPP_API_VERSION` (Meta's Graph API version,
`v23.0`), `JWT_ACCESS_MINUTES` (30), `JWT_REFRESH_DAYS` (30), `THROTTLE_LOGIN`, `THROTTLE_LOGIN_IP`, `THROTTLE_REFRESH`, `THROTTLE_QR`, `THROTTLE_DEVICE`.

Keep the secret ones — `SECRET_KEY`, `DATABASE_URL`, `FIELD_ENCRYPTION_KEY`, and the Redis URLs if they carry
a password — in Secrets Manager, one secret per value, and point the services at them. The rest are plain
environment variables, readable by anyone who can open the service.

```bash
aws secretsmanager create-secret --name dumbelo/secret-key \
  --secret-string "$(python -c 'import secrets; print(secrets.token_urlsafe(64))')"
aws secretsmanager create-secret --name dumbelo/database-url --secret-string 'postgres://...'
aws secretsmanager create-secret --name dumbelo/field-encryption-key   --secret-string "$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
```

The WhatsApp numbers' own credentials (access token, app secret) are not settings: a Dumbelo admin pastes them
into the Console (WhatsApp → Add Account, or Replace Credentials), and they are kept encrypted with
`FIELD_ENCRYPTION_KEY`. Nothing shows them again, only their last 4 characters. The API, the worker and beat
all need the same key.

Each number also needs Meta's webhook, so delivery, read receipts and STOP replies come back (and shared-number
usage can be billed). In the Meta app's WhatsApp → Configuration, set the Callback URL and Verify token that the
Console shows on the account (Dumbelo's shared number: `https://<api host>/api/whatsapp/webhook/`; a gym's own:
`.../api/whatsapp/webhook/<slug>/`), then subscribe to the `messages` field. Meta signs every call with the app
secret, so the account's app secret in the Console must be that app's. Every signed call is kept in the database
(`WebhookEvent`), with an error if handling it failed. To run calls again (a status that came before the send
saved Meta's id, or a call that broke on a bug since fixed): `python manage.py replay_webhook_events --since
2026-10-18T09:00+05:30` (add `--failed` for only the broken ones, or `--id N`). Running one again is always safe.

### Rotating the encryption key

`FIELD_ENCRYPTION_KEY` takes several keys, newest first: values are written with the first and read with any.

1. Make a new key and set `FIELD_ENCRYPTION_KEY=<new>,<old>` on the API, the worker and beat. Deploy.
2. Run `python manage.py rotate_credentials` once (a one-off task, like the migration in step 5). It writes every
   credential again with the new key, or changes nothing if one can't be read.
3. Set `FIELD_ENCRYPTION_KEY=<new>` and deploy again. Keep the old key in its own secret for 14 more days: the
   backups from before the rotation are encrypted with it (`docs/operations.md`, Backups).

## 4. The image (ECR)

```bash
aws ecr create-repository --repository-name dumbelo-api --image-scanning-configuration scanOnPush=true
aws ecr get-login-password | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

cd api
docker build -t $ECR:$(git rev-parse --short HEAD) -t $ECR:latest .
docker push --all-tags $ECR
```

The image collects the static files at build time and runs gunicorn as a non-root user. It does **not** run
migrations when it starts: a deploy runs them once, in step 5, so ten containers starting at once can't fight
over the same database.

## 5. Migrate, and make the first gym

Migrations run as a one-off Fargate task on the same image, in the same VPC, with the same settings. Create an
ECS cluster (the worker and beat will use it too) and a task definition whose command is the migration:

```bash
aws ecs create-cluster --cluster-name dumbelo
```

Register `dumbelo-migrate` with one container **named `migrate`** (the deploy workflow overrides that
container's image by name), `"command": ["python", "manage.py", "migrate", "--noinput"]`, the image from step
4, the environment from step 3, 0.25 vCPU / 0.5 GB, awsvpc networking in the private subnets, and the log
group `/ecs/dumbelo`. Then run it:

```bash
aws ecs run-task --cluster dumbelo --task-definition dumbelo-migrate --launch-type FARGATE \
  --network-configuration 'awsvpcConfiguration={subnets=[subnet-aaa,subnet-bbb],securityGroups=[sg-app]}'
```

Watch it in CloudWatch under `/ecs/dumbelo`; it should end with `OK` for every migration and exit 0.

A gym of your own comes next. Make a Dumbelo superuser with the same one-off task (command
`["python", "manage.py", "createsuperuser", "--noinput"]` with `DJANGO_SUPERUSER_*` set), sign in to the Console
(`/console`) and add Dumbelo's prices first (Prices → Add Price List): no gym opens without them. Then New Gym in
the Console, or `python manage.py create_gym` from the command line, makes the gym, its first branch, its owner
admin and its Dumbelo plan. Don't create gyms in the Django admin: they get no Dumbelo plan, so they can't add
branches.

Never run `seed_demo` against the pilot database. It builds the demo gym, not a real one.

## 6. The API (App Runner)

Create a service from the ECR image:

- **Port** 8000, and let App Runner deploy the `latest` tag manually (not automatically — the deploy workflow
  decides when).
- **Instance role**: may read the secrets from step 3 (`secretsmanager:GetSecretValue` on `dumbelo/*`).
- **Access role**: may pull from ECR (App Runner offers to make it).
- **VPC connector** into the private subnets with the app security group, so the service can reach Postgres
  and Redis. Those subnets need a **NAT gateway**: with a VPC connector every outbound call goes through the
  VPC, and the reminders have to reach WhatsApp.
- **Health check**: HTTP, path `/api/health/`, every 10 s, 1 healthy / 5 unhealthy. The check arrives with the
  container's own address in the `Host` header, which `ALLOWED_HOSTS` can't know; `/api/health/` answers it
  anyway (`apps/core/middleware.py`), and the HTTPS redirect leaves that one path alone.
- **Size**: 1 vCPU / 2 GB, 1–2 instances is enough for a pilot gym.
- **Environment**: everything in step 3.

### The worker and beat (ECS Fargate)

Two services on the `dumbelo` cluster, same image, same environment, 0.25 vCPU / 0.5 GB, desired count **1**,
private subnets, no load balancer:

| Service | Command | Note |
|---|---|---|
| `dumbelo-worker` | `celery -A config worker --loglevel=info` | Runs the jobs |
| `dumbelo-beat` | `celery -A config beat --loglevel=info --schedule /tmp/celerybeat-schedule` | The clock. Exactly one |

Beat ticks every quarter hour and wakes each gym when its own clock reaches its reminder hours (6 AM unless a
Dumbelo admin set others in Console → Automation, read from the database on every tick, so a change needs no
restart), so keep **one** beat instance: two would hand out the same morning twice. (Nothing breaks if they do — a
second sweep writes no new reminder rows and sends no second message — but there is no reason to pay for it.) The
same tick reminds gyms' owners about Dumbelo invoices coming due or late. Beat also runs
`apps.billing.tasks.write_invoices` at five past every hour: each active gym's Dumbelo invoice on its billing day,
from Dumbelo's invoice hour (midnight by default) on the gym's clock, skipped once written. If the worker was down on a billing day, write it by hand:
`python manage.py write_invoices --day 2026-11-01`. And every minute, `apps.messages.tasks.retry_messages` tries
again the WhatsApp messages Meta turned away for now (rate limits, Meta busy), up to 3 times with growing waits.
A message Meta may already have taken (it didn't answer, or the worker died mid-send) is never sent again on its
own: the gym's message log says so.

### If you'd rather run the API on ECS too

Same image, a third service on the `dumbelo` cluster behind an Application Load Balancer: target group on
port 8000 with health check path `/api/health/` (HTTP 200), the ALB in the public subnets with an ACM
certificate for `api.dumbelo.com`, HTTP redirected to HTTPS. You lose App Runner's one-click deploys and gain
control over scaling. Everything else on this page is unchanged.

## 7. Domains and HTTPS

- `api.dumbelo.com`: add it as a custom domain on the App Runner service and create the CNAME records it asks
  for. App Runner manages the certificate. (On ECS: point the record at the ALB and use ACM.)
- `app.dumbelo.com`: add it in Vercel (step 8) and create the record Vercel asks for.
- Then `ALLOWED_HOSTS=api.dumbelo.com` and `CORS_ALLOWED_ORIGINS=https://app.dumbelo.com`. HSTS is on with a
  one-year max-age and `includeSubDomains`, so serve every `dumbelo.com` name over HTTPS from the start.

## 8. The web app (Vercel)

Vercel builds from GitHub, so it needs no workflow of ours.

1. Import the repository and set **Root Directory** to `web`. The framework (Next.js) is detected; `npm ci`
   and `npm run build` are the defaults.
2. Environment variable, for Production and Preview: `NEXT_PUBLIC_API_URL=https://api.dumbelo.com`.
   It is baked into the build, so changing it needs a redeploy.
3. Production branch `main`. Every pull request gets its own preview URL; the API's CORS list doesn't include
   those, so a preview can't call the production API — point a preview at a staging API or test on `main`.
4. Add the `app.dumbelo.com` domain.

## 9. Check it, in this order

```bash
curl -s https://api.dumbelo.com/api/health/            # {"status":"ok","database":"ok"}
curl -s -D- -o /dev/null https://api.dumbelo.com/api/docs/ | grep -i strict-transport-security
curl -s -o /dev/null -w '%{http_code}\n' https://api.dumbelo.com/api/me/     # 401: it wants a sign-in
```

The service's own health check should read **Healthy** in the App Runner console. That is the proof that
`/api/health/` answers a check made to the container's address; if it reads unhealthy while the `curl` above
works, the health check is pointed at the wrong path or port.

Then in a browser, on a phone: open `https://app.dumbelo.com`, sign in as the gym's admin, add a member, sell a
plan, collect a payment, check someone in. Finally confirm the jobs are alive — the worker's log shows
`celery@... ready` and beat's shows it sending `apps.messages.tasks.send_reminders` every quarter hour.

## Deploying again

`.github/workflows/deploy.yml` does it, and only when you press the button: **Actions → Deploy API → Run
workflow**. It refuses to run unless CI has already passed on that exact commit, then it builds and pushes the
image, runs the migrations as the one-off task, tells App Runner to deploy, restarts the worker and beat, and
asks `/api/health/` whether it worked.

Give GitHub these first. The repository holds no secret of its own; the role is assumed with OIDC, so there is
no AWS key to leak.

| GitHub setting | What it is |
|---|---|
| Secret `AWS_ROLE_ARN` | A role GitHub may assume (trusts `token.actions.githubusercontent.com` for this repository) with: push to the ECR repository, `apprunner:StartDeployment` and `apprunner:ListOperations`, `ecs:RunTask`, `ecs:UpdateService`, `ecs:DescribeTasks`, and `iam:PassRole` for the task's roles |
| Variable `AWS_REGION` | `ap-south-1` (the default if unset) |
| Variable `ECR_REPOSITORY` | `dumbelo-api` |
| Variable `APPRUNNER_SERVICE_ARN` | The service from step 6 |
| Variable `ECS_CLUSTER` | `dumbelo` |
| Variable `MIGRATE_TASK_DEFINITION` | `dumbelo-migrate` |
| Variable `MIGRATE_SUBNETS` | `subnet-aaa,subnet-bbb` |
| Variable `MIGRATE_SECURITY_GROUPS` | `sg-app` |
| Variable `WORKER_SERVICE`, `BEAT_SERVICE` | `dumbelo-worker`, `dumbelo-beat` (leave unset to not restart them) |
| Variable `API_HEALTH_URL` | `https://api.dumbelo.com/api/health/` |

Make a GitHub **environment** called `production` and add yourself as a required reviewer if you want a deploy
to need a second pair of eyes. Vercel deploys the web app from `main` by itself.

### A migration that needs care

A migration that drops or renames a column breaks the containers still running the old code. Ship it in two
deploys: one that adds and keeps writing both, one that removes the old. Nothing in the MVP needs this yet.

### Going back

The image is tagged with the commit it was built from, so a bad deploy is undone by pointing the service at
the last good tag — which deploys it as well:

```bash
aws apprunner update-service --service-arn <arn> --source-configuration \
  "ImageRepository={ImageIdentifier=$ECR:<good-short-sha>,ImageRepositoryType=ECR}"
```

Then put it back on `latest` (the same command with `:latest`) before the next deploy, or re-run the deploy
workflow from the good commit instead of all this. A migration is **not** undone by either: check what the bad
commit migrated before you roll back, and if data moved, restore instead (`docs/operations.md`, Restoring for real).

## What this costs, roughly

App Runner 1 vCPU/2 GB (~$25–45), RDS `db.t4g.micro` (~$15), ElastiCache `cache.t4g.micro` (~$12), two Fargate
tasks at 0.25 vCPU (~$10), NAT gateway (~$35), ECR and CloudWatch (a few dollars). Around $100–120 a month for
the pilot, in `ap-south-1`. Vercel's Hobby plan is free; a client-facing app belongs on Pro ($20).
