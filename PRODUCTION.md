# Production

Dumbelo on **any cloud server**: one Linux machine running everything in Docker (DigitalOcean, Hetzner, AWS
Lightsail, Oracle, any VPS). Every step is a command to copy. The longer explanation of each step is in
`docs/deploy-server.md`. The AWS setup with managed services (RDS, App Runner, Vercel) is in `docs/deploy.md`.

```
phone ──HTTPS──► server: caddy :443 ─┬─ app.<domain> ─► web (Next.js)
                                      └─ api.<domain> ─► api (Django) ─► db (Postgres 16), redis ◄─ worker, beat
```

The server files are in `deploy/server/`: `docker-compose.yml`, `Caddyfile`, `.env.example`, `update.sh` and
`backup.sh`. `# laptop` blocks run in PowerShell on your machine; every other block runs on the server.

# Part 1: Set up (once, about an hour)

## 1. Pick a server

Any provider works if it gives you all of these:

| Need | Minimum |
|---|---|
| OS | **Ubuntu 24.04 LTS** (x64 or ARM) |
| Size | **2 vCPU, 4 GB RAM, 40 GB disk** (1–2 GB of RAM is too small to build the web app) |
| Region | India (Mumbai, Bangalore, Hyderabad, Delhi) or the nearest one |
| Sign-in | SSH key, not a password |
| Network | A fixed public IPv4, and a firewall in the provider's console |
| Backups | Weekly disk snapshots, if offered (turn them on) |

Also have: a domain, two-factor sign-in on the provider and on GitHub, and a password manager.

## 2. SSH key, and create the server

```powershell
# laptop
ssh-keygen -t ed25519 -f $HOME\.ssh\dumbelo -C "dumbelo server"     # give it a passphrase
Get-Content $HOME\.ssh\dumbelo.pub                                  # paste this into the provider
```

In the provider's console, create the server from step 1's table and paste the public key as its SSH key. Copy
its **public IP**.

**Firewall** (in the provider's console): allow inbound **TCP 22, 80, 443** from anywhere, and nothing else.
Outbound: allow everything.
- No console firewall? Use the server's own, after step 3: `sudo ufw allow OpenSSH && sudo ufw allow 80,443/tcp && sudo ufw --force enable`.
- On Oracle Cloud there are two firewalls to open: `docs/deploy-server.md`, "On Oracle Cloud instead".

## 3. Sign in, and a safe user

```powershell
# laptop: root on DigitalOcean, Hetzner and Vultr; ubuntu on AWS and Oracle
ssh -i $HOME\.ssh\dumbelo root@<IP>
```

**Signed in as `ubuntu`?** It already is a safe user. Skip to step 4.

**Signed in as `root`?** Make a user of your own:

```bash
adduser --disabled-password --gecos "" dumbelo
echo 'dumbelo ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/dumbelo && chmod 440 /etc/sudoers.d/dumbelo
rsync --archive --chown=dumbelo:dumbelo ~/.ssh /home/dumbelo
```

Keep that window open. In a new one, check the user works, then turn off root and password sign-in:

```powershell
# laptop
ssh -i $HOME\.ssh\dumbelo dumbelo@<IP>
```
```bash
printf 'PermitRootLogin no\nPasswordAuthentication no\nKbdInteractiveAuthentication no\n' | sudo tee /etc/ssh/sshd_config.d/00-dumbelo.conf
sudo sshd -t && sudo systemctl restart ssh
```

Check that `ssh -i $HOME\.ssh\dumbelo root@<IP>` now says **Permission denied**.

Optional: put this in `$HOME\.ssh\config` on your laptop, and then `ssh dumbelo` is enough:
```
Host dumbelo
  HostName <IP>
  User dumbelo
  IdentityFile ~/.ssh/dumbelo
```

## 4. Prepare the server

```bash
sudo apt update && sudo apt -y upgrade
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
sudo reboot
```

Sign in again after a minute, then:

```bash
docker run --rm hello-world && docker compose version && free -h      # "Hello from Docker!", v2.x, Swap 2.0Gi
```

Save your names for later commands, and add a `manage` shortcut for Django's commands. Change the first two lines:

```bash
DOMAIN=dumbelo.com              # your domain
EMAIL=you@example.com           # Let's Encrypt writes here about certificates
cat >> ~/.bashrc <<EOF
export DOMAIN=$DOMAIN EMAIL=$EMAIL
manage() { (cd ~/dumbelo/deploy/server && docker compose exec api python manage.py "\$@"); }
EOF
source ~/.bashrc
```

## 5. DNS

At your domain's registrar, add two **A** records: `api` → the server IP, and `app` → the server IP. On Cloudflare,
set them to *DNS only* (grey cloud). Wait until both names answer with the IP:

```bash
getent hosts api.$DOMAIN app.$DOMAIN
```

## 6. Code and settings

```bash
ssh-keygen -t ed25519 -f ~/.ssh/github -N "" && cat ~/.ssh/github.pub
```

GitHub → the repository → **Settings → Deploy keys → Add deploy key**: paste the key, and leave write access off. Then:

```bash
printf 'Host github.com\n  IdentityFile ~/.ssh/github\n' >> ~/.ssh/config
git clone git@github.com:pkvaishakh/dumbelo-gym-erp.git ~/dumbelo
cd ~/dumbelo/deploy/server
cp .env.example .env && chmod 600 .env
sed -i "s|^API_DOMAIN=.*|API_DOMAIN=api.$DOMAIN|; s|^APP_DOMAIN=.*|APP_DOMAIN=app.$DOMAIN|; s|^ACME_EMAIL=.*|ACME_EMAIL=$EMAIL|" .env
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 24)|" .env
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$(openssl rand -hex 50)|" .env
sed -i "s|^FIELD_ENCRYPTION_KEY=.*|FIELD_ENCRYPTION_KEY=$(openssl rand -base64 32 | tr '+/' '-_')|" .env
grep -E '^[A-Z_]+=$' .env || echo "all set"
cat .env
```

**Copy what `cat .env` prints into your password manager now.** Without it, a backup can't be read back with its
WhatsApp credentials (`FIELD_ENCRYPTION_KEY`), and changing `SECRET_KEY` signs everyone out. Never commit `.env`.

## 7. Start it

```bash
cd ~/dumbelo/deploy/server && bash update.sh      # first time 5–15 minutes; ends with "Deployed <commit>."
docker compose ps                                 # all Up, api (healthy), migrate Exited (0)
```

## 8. Check it

```bash
curl -s https://api.$DOMAIN/api/health/                                    # {"status":"ok","database":"ok"}
curl -s -o /dev/null -w '%{http_code}\n' https://api.$DOMAIN/api/me/       # 401
curl -sI https://api.$DOMAIN/api/docs/ | grep -i strict-transport          # the HSTS header
manage check --deploy                                                       # no errors
```

## 9. Dumbelo admin and the first gym

```bash
manage createsuperuser            # your email, name and a long password from the password manager
```

1. Open `https://app.<domain>`, sign in, and you land on the Console.
2. Console → More → Prices → **Add Price List**. No gym opens without one.
3. Console → Gyms → **New Gym** (name, short name, time zone, first branch, owner's email).
   From the command line instead:
   `manage create_gym --name "Pulse Fitness" --slug pulse --branch Kochi --owner-email anil@pulse.in --owner-name "Anil Menon"`
4. The gym → **Dumbelo plan**: the branch quota, the billing day and the WhatsApp mode.
5. The owner signs in and adds branches, plans, staff and members. On a phone, check: add a member, sell a plan,
   collect a payment, check someone in.

**Never run `seed_demo` on production.** It makes demo logins anyone can read in the README.

## 10. Backups and monitoring (same day)

Nightly database copy at 3 AM IST, keeping the newest 14:

```bash
(crontab -l 2>/dev/null; echo '30 21 * * * bash $HOME/dumbelo/deploy/server/backup.sh >> $HOME/backups.log 2>&1') | crontab -
bash ~/dumbelo/deploy/server/backup.sh            # once now, to see it work
```

**Off the server, every night.** Any S3-style bucket works: DigitalOcean Spaces, Cloudflare R2, Backblaze B2 or
AWS S3. Make the bucket **private**, give it a rule that deletes files after 90 days, and create an access key for it. Then:

```bash
sudo apt install -y rclone
rclone config            # n (new) → name: offsite → type: s3 → your provider → access key, secret, endpoint → defaults
rclone lsd offsite:      # lists your bucket
(crontab -l; echo '0 22 * * * rclone copy $HOME/backups offsite:<bucket>/dumbelo --max-age 48h >> $HOME/backups.log 2>&1') | crontab -
```

`copy` never deletes anything in the bucket. The dumps hold members' names and phone numbers, so keep the bucket
private and its keys only on this server.

**Alerts:**
- An uptime monitor on `https://api.<domain>/api/health/`: the provider's own, or UptimeRobot (free).
- The provider's alerts for CPU above 80%, memory above 90% and disk above 80%.
- A billing alert on the provider account.

# Part 2: Run it

Every `docker compose` command runs in `~/dumbelo/deploy/server`, so `cd` there first.

## Start, stop, restart

```bash
docker compose up -d                  # start everything (also after a change to .env)
docker compose ps                     # what's running
docker compose restart api            # restart one: api, web, worker, beat, caddy, db, redis
docker compose stop                   # stop everything; the data stays
docker compose stop worker beat       # pause the jobs (reminders, invoices) only
docker compose start worker beat      # and resume them
```

After a reboot everything starts by itself. Never run `docker compose down -v`: `-v` deletes the database.

## Deploy a new version

Merge to `main` on GitHub (CI green), then:

```bash
cd ~/dumbelo/deploy/server && bash update.sh
```

It backs up the database, pulls, rebuilds, migrates, restarts and checks health. There's a few seconds' gap
while the API restarts, so deploy in a quiet hour: not at opening time, and not at 6 AM, when the reminders go out.

## Roll back

```bash
cd ~/dumbelo && git log --oneline -10                  # find the last good commit
git switch --detach <good commit>
cd deploy/server && docker compose up -d --build
git switch main                                        # when the fix is on main; then bash update.sh
```

This doesn't undo migrations. If the bad version changed data, restore the backup `update.sh` took just before it
([Restore for real](#restore-for-real)).

## Logs

```bash
docker compose logs -f --tail 100 api          # follow one (Ctrl+C stops following)
docker compose logs --since 1h worker beat     # the jobs, last hour
docker compose logs caddy | grep -i error      # HTTPS and certificate problems
```

The logs rotate by themselves: each service keeps 5 files of 10 MB.

## Django commands

```bash
manage write_invoices --day 2026-11-01                     # a billing day the worker missed
manage replay_webhook_events --failed                      # WhatsApp webhook calls that broke
manage replay_webhook_events --since 2026-10-18T09:00+05:30
manage verify_counts --gym pulse                           # members, payments, check-ins for one gym
manage check --deploy                                      # the security settings
manage shell                                               # Python on the live database: be careful
docker compose exec db psql -U dumbelo                     # SQL on the live database: be more careful
```

Console → Server → **Run Now** starts the jobs from the browser.

## Change a setting

```bash
nano .env && docker compose up -d                  # an API setting (e.g. WHATSAPP_PROVIDER=whatsapp_cloud)
nano .env && bash update.sh                        # API_DOMAIN or APP_DOMAIN: the web app is built again
```

# Part 3: Maintain it

## The schedule

| When | What | Time |
|---|---|---|
| Every night, by itself | Database backup + off-site copy, security updates, HTTPS renewal, log rotation | 0 |
| Weekly | [Weekly check](#weekly-check) | 5 min |
| Monthly | [Updates](#monthly-updates), then the [restore drill](#restore-drill) | 45 min |
| Before each release | On your laptop: `cd api; pip-audit` and `cd web; npm audit` | 5 min |
| Yearly | Domain on auto-renew; review who has access (Console admins, deploy keys, provider team); rotate keys if anyone left | 15 min |

## Weekly check

```bash
cd ~/dumbelo/deploy/server
docker compose ps                                   # all Up
tail -5 ~/backups.log                               # last night's "wrote ..." and the rclone copy
rclone ls offsite:<bucket>/dumbelo | tail -3        # yesterday's dump is there
df -h / && free -h                                  # disk under 80%
curl -s https://api.$DOMAIN/api/health/
```

Then Console → **Server** (database, Redis, worker, beat: all up) and Console → **Home** (what needs you).

## Monthly updates

```bash
sudo apt update && sudo apt -y upgrade
cd ~/dumbelo/deploy/server
docker compose pull db redis caddy                  # same major versions: postgres 16, redis 7, caddy 2
docker compose build --pull                         # newer Python and Node security fixes under the app
docker compose up -d
docker image prune -f && docker builder prune -f    # free the disk
[ -f /var/run/reboot-required ] && sudo reboot      # only if the updates need it
```

Never change `postgres:16` to another major version in `docker-compose.yml`. A major upgrade means a dump and a
restore into the new version, planned on its own.

## Restore drill

Once a month, prove last night's backup restores and holds what the live database held. It changes nothing live:
the copy goes into a separate database, `drill`, which is deleted at the end.

```bash
cd ~/dumbelo/deploy/server
F=$(ls -1t ~/backups/dumbelo-*.dump | head -1); echo $F
T=$(basename $F .dump | sed -E 's/dumbelo-(....)(..)(..)T(..)(..)Z/\1-\2-\3T\4:\5Z/'); echo $T
GYM=<a gym's short name>
docker compose exec db createdb -U dumbelo drill
docker compose exec -T db pg_restore -U dumbelo -d drill --no-owner < "$F"
manage verify_counts --gym $GYM --until $T                                                      # live
docker compose exec api sh -c "DATABASE_URL=\${DATABASE_URL%/dumbelo}/drill python manage.py verify_counts --gym $GYM --until $T"   # copy
docker compose exec db dropdb -U dumbelo drill
```

The members, payments and check-ins lines must be **the same** on both. If they differ, keep the `drill` database
and find out why before the next deploy. Write the date and the result in `docs/operations.md` → Drill log.

## Restore for real

When data is lost or broken, go back to the last backup from before it happened. Everything written after that
backup is lost, so tell the gyms what time their data runs to.

```bash
cd ~/dumbelo/deploy/server
ls -lt ~/backups/                                       # pick the one from before the problem
cp ~/backups/dumbelo-<chosen>.dump ~/restore.dump       # set aside, so the backup below can't rotate it away
docker compose stop caddy web api worker beat           # nothing reads or writes; the site is down from here
bash backup.sh                                          # keep the broken state too, just in case
docker compose exec db dropdb -U dumbelo dumbelo
docker compose exec db createdb -U dumbelo dumbelo
docker compose exec -T db pg_restore -U dumbelo -d dumbelo --no-owner < ~/restore.dump
docker compose up -d                                    # migrations run first, then everything starts
curl -s https://api.$DOMAIN/api/health/
```

The backup doesn't have to come from this server: copy one down from the bucket with
`rclone copy offsite:<bucket>/dumbelo/<file> ~/backups/`. The jobs run the day's reminders and invoices again
when they start; both are safe to repeat.

## Move to another server or provider

1. Set up the new server: Part 1, steps 1–4 and 6. For `.env`, paste your saved file instead of making new
   secrets: the **same** `FIELD_ENCRYPTION_KEY` and `SECRET_KEY`.
2. On the old server, stop and take a last backup:
   `docker compose stop caddy web api worker beat && bash backup.sh`.
3. Copy that dump to the new server's `~/backups/`, via the bucket or with `scp` through your laptop.
4. On the new server, start only the database, restore, then start the rest:
   `docker compose up -d db`, then the `dropdb`, `createdb` and `pg_restore` lines from
   [Restore for real](#restore-for-real), then `bash update.sh`.
5. Point the `api` and `app` DNS records at the new IP. Caddy gets new certificates within minutes.
6. Keep the old server, stopped, for a week. Then delete it.

## Rotate keys

**`FIELD_ENCRYPTION_KEY`** (which encrypts the WhatsApp credentials). Do it if it may have leaked, or when someone
who had it leaves:

```bash
cd ~/dumbelo/deploy/server
NEW=$(openssl rand -base64 32 | tr '+/' '-_'); OLD=$(grep ^FIELD_ENCRYPTION_KEY= .env | cut -d= -f2-)
sed -i "s|^FIELD_ENCRYPTION_KEY=.*|FIELD_ENCRYPTION_KEY=$NEW,$OLD|" .env && docker compose up -d
manage rotate_credentials
sed -i "s|^FIELD_ENCRYPTION_KEY=.*|FIELD_ENCRYPTION_KEY=$NEW|" .env && docker compose up -d
echo "old key: $OLD"
```

Update the password manager, and keep the old key there for 14 more days, marked as old. The backups from before
the rotation need it: to restore one, use `FIELD_ENCRYPTION_KEY=<new>,<old>`.

**`SECRET_KEY`** (this signs everyone out):

```bash
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$(openssl rand -hex 50)|" .env && docker compose up -d
```

**Someone loses access:** remove their deploy key on GitHub (or SSH key from `~/.ssh/authorized_keys`), their
provider account, and their Console admin. Rotate whatever they could read.

## Security checklist

- [ ] Only ports 22, 80 and 443 are open (provider firewall). Postgres and Redis publish no ports.
- [ ] SSH by key only, root sign-in off (step 3): `sudo sshd -T | grep -E 'permitrootlogin|passwordauthentication'` says `no` twice.
- [ ] Two-factor sign-in on the provider, GitHub, the domain registrar and the bucket provider.
- [ ] `.env` is `chmod 600` and in the password manager, and in no chat, email or commit.
- [ ] Security updates install themselves: `systemctl is-active unattended-upgrades` says `active`.
- [ ] `manage check --deploy` is clean, and HTTPS answers with HSTS (step 8).
- [ ] Backups are nightly, off the server, private, and the last drill matched.
- [ ] `pip-audit` and `npm audit` before each release.

## When something's wrong

| You see | Look | Usually |
|---|---|---|
| The site times out | Provider firewall | 80/443 not open, or the firewall isn't on this server |
| Certificate error, or Caddy `challenge failed` | `docker compose logs caddy` | DNS doesn't point here yet. Fix it, then `docker compose restart caddy` once |
| `Bad Request (400)` | `.env` `API_DOMAIN` | It doesn't match the address in the browser |
| Sign-in fails with a network or CORS error | `.env` `APP_DOMAIN` | Wrong name. Fix it and `bash update.sh` |
| `502` from Caddy | `docker compose ps`, `logs api` | The API is down or restarting |
| Reminders didn't go | `logs worker beat`, Console → Server | Jobs stopped, or `WHATSAPP_PROVIDER` is still `fake` |
| Build `Killed` | `free -h` | Not enough memory: check the swap, or a bigger server |
| Disk full | `df -h /`, `docker system df` | `docker image prune -f && docker builder prune -f`, and check `~/backups` |
| `migrate` `Exited (1)` | `docker compose logs migrate` | A migration failed. Nothing else starts until it's fixed |

Locked out of SSH? Use the provider's web console (DigitalOcean: Access → Recovery Console; most providers have
one), and add your key to `~/.ssh/authorized_keys` again.

## Cost

A 4 GB server is about $6–30 a month, depending on the provider (Hetzner is the cheapest; DigitalOcean and
Lightsail cost about $24). Add disk snapshots (about 20% of the server's price), a bucket ($0–5) and the domain
(about ₹1,000 a year).
