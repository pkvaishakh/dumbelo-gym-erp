# Deploy on one server

Dumbelo on a single Linux server: the API, its database, Redis, the background jobs and the web app, all in Docker
on one machine. This page uses a **DigitalOcean droplet in Bangalore**; [On Oracle Cloud instead](#on-oracle-cloud-instead)
has the few steps that differ there. It's simpler and cheaper than the AWS setup in `docs/deploy.md`, but
everything is on one machine, so the backups (step 11) are not optional.

Written for someone deploying for the first time. Do the steps in order. Each one ends with a check; don't go on
until it passes.

```
phone / laptop ──HTTPS──► server (Ubuntu 24.04, Docker)
                            caddy :80 :443   gets the HTTPS certificates
                              ├── app.<domain> ──► web      (Next.js)
                              └── api.<domain> ──► api      (gunicorn) ──► db (Postgres 16), redis
                                                   worker, beat (the jobs) ──┘
```

Everything lives in [`deploy/server/`](../deploy/server/): `docker-compose.yml` (the containers), `Caddyfile`
(the HTTPS front door), `.env.example` (the settings), `update.sh` (deploy) and `backup.sh` (the nightly backup).
The short, command-only version of this page, with running and maintaining it, is `PRODUCTION.md`.

Commands in `PS>` blocks run in PowerShell on your Windows machine. All the others run on the server, over SSH.

## 0. Before you start

- A **DigitalOcean** account with a card added. Turn on two-factor sign-in (Settings → Security) on day one: anyone
  who gets into this account gets the gym's data.
- Two-factor sign-in on **GitHub** too, for the same reason.
- A **domain** (`dumbelo.com` → `api.dumbelo.com` and `app.dumbelo.com`). A real gym needs a real one.
- The code on GitHub, on `main`, including the `deploy/server/` folder. The server downloads it from there.

What it costs: the droplet at $24 a month, plus $4.80 for its weekly backups, so about $29 a month (roughly ₹2,500),
and the domain, about ₹1,000 a year. Check the current prices on DigitalOcean's pricing page.

## 1. Make an SSH key (on Windows)

The key is how you sign in to the server: there is no password to guess.

```powershell
PS> ssh-keygen -t ed25519 -f $HOME\.ssh\dumbelo -C "dumbelo server"
PS> Get-Content $HOME\.ssh\dumbelo.pub
```

When it asks, give the key a **passphrase**. Then a stolen laptop isn't a way into the gym's server. The second
command prints one line starting `ssh-ed25519`: that's the public half, which is safe to paste anywhere. The other
file, `dumbelo` without `.pub`, is the private half. Never send it to anyone.

## 2. Create the droplet

DigitalOcean → **Create → Droplets**.

| Field | Choose | Why |
|---|---|---|
| Region | **Bangalore** (BLR1) | Close to the gym, so the front desk is fast, and the data stays in India |
| Image | **Ubuntu 24.04 (LTS) x64** | The commands below are written for it |
| Size | **Basic → Regular → $24/mo: 4 GB, 2 CPUs, 80 GB** | Postgres, Redis, the API, the jobs and the web build need about 2–3 GB together |
| Authentication | **SSH Key → New SSH Key**: paste the line from step 1, name it `laptop` | Not *Password* |
| Backups | **Enable, weekly** | A copy of the whole disk, kept by DigitalOcean, off this server |
| Monitoring | Tick **improved metrics monitoring and alerting** (free) | So step 13's alerts work |
| Hostname | `dumbelo` | |

Press **Create Droplet**. After a minute it shows an **ipv4** address (it looks like `139.59.10.20`): copy it.
The address stays the same for as long as the droplet exists.

## 3. The firewall

**Networking → Firewalls → Create Firewall**. Name it `dumbelo`.

| Inbound rule | Protocol | Port | Sources |
|---|---|---|---|
| SSH | TCP | 22 | All IPv4, All IPv6 |
| HTTP | TCP | 80 | All IPv4, All IPv6 |
| HTTPS | TCP | 443 | All IPv4, All IPv6 |

Leave the outbound rules as they are (the server has to reach GitHub, Let's Encrypt and WhatsApp). Under **Apply to
Droplets**, choose `dumbelo`. Then **Create Firewall**.

Use this firewall, not `ufw` on the server: Docker opens the ports it publishes past `ufw`, but it can't touch a
firewall outside the server. Postgres and Redis publish no ports at all, so nothing but these three is reachable.

## 4. Sign in, and a user of your own

The first sign-in is as `root`:

```powershell
PS> ssh -i $HOME\.ssh\dumbelo root@139.59.10.20
```

Answer `yes` the first time. Working as `root` all the time is risky, because one wrong command can break anything.
So make your own user, `dumbelo`, which can do everything with `sudo`:

```bash
adduser --disabled-password --gecos "" dumbelo
echo 'dumbelo ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/dumbelo && chmod 440 /etc/sudoers.d/dumbelo
rsync --archive --chown=dumbelo:dumbelo ~/.ssh /home/dumbelo
```

**Keep this window open.** In a second PowerShell window, check the new user works:

```powershell
PS> ssh -i $HOME\.ssh\dumbelo dumbelo@139.59.10.20
```
```bash
sudo whoami          # root
```

Only if that worked, turn off signing in as `root` and with passwords:

```bash
printf 'PermitRootLogin no\nPasswordAuthentication no\nKbdInteractiveAuthentication no\n' | sudo tee /etc/ssh/sshd_config.d/00-dumbelo.conf
sudo sshd -t && sudo systemctl restart ssh
```

Check from Windows that `ssh -i $HOME\.ssh\dumbelo root@139.59.10.20` now says **Permission denied**. Then close
the `root` window. From here on, always sign in as `dumbelo`.

Optional shortcut: add this to `$HOME\.ssh\config` on Windows, and after that `ssh dumbelo` is enough:

```
Host dumbelo
  HostName 139.59.10.20
  User dumbelo
  IdentityFile ~/.ssh/dumbelo
```

## 5. Prepare the server

Updates, some swap (spare memory on disk, so a big build doesn't run out), and Docker:

```bash
sudo apt update && sudo apt -y upgrade
sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
sudo reboot
```

Sign in again after a minute. That applies the new kernel and the Docker group. Then check:

```bash
docker run --rm hello-world        # "Hello from Docker!"
docker compose version             # v2.something
free -h                            # Swap: 2.0Gi
```

Then **fail2ban**, which bans an address for an hour after 5 failed SSH sign-ins in 10 minutes. The key already
keeps strangers out; this stops them trying thousands of times a day:

```bash
sudo apt install -y fail2ban
printf '[sshd]
enabled = true
maxretry = 5
findtime = 10m
bantime = 1h
' | sudo tee /etc/fail2ban/jail.d/dumbelo.local
sudo systemctl enable fail2ban && sudo systemctl restart fail2ban
sudo fail2ban-client status sshd            # "Status for the jail: sshd"
```

If the last line errors, add `backend = systemd` to `/etc/fail2ban/jail.d/dumbelo.local` and run the `restart` again.

Ubuntu installs security updates by itself (`unattended-upgrades`). Reboot now and then, at a quiet hour:
`sudo reboot`. Everything comes back on its own, because every container is `restart: unless-stopped`.

## 6. Point the names at the server

At the company you bought the domain from (GoDaddy, Namecheap, Hostinger, Cloudflare and so on), add two **A** records:

| Type | Name | Value |
|---|---|---|
| A | `api` | the droplet's IP |
| A | `app` | the droplet's IP |

On Cloudflare, set both to **DNS only** (grey cloud). Caddy makes the certificates itself.

Check, on the server. Both names must answer with the droplet's IP before step 9. A new record can take from a
few minutes to an hour to show up:

```bash
getent hosts api.dumbelo.com app.dumbelo.com
```

## 7. Get the code onto the server

The repository is private, so the server needs its own read-only key for GitHub (a *deploy key*):

```bash
ssh-keygen -t ed25519 -f ~/.ssh/github -N ""
cat ~/.ssh/github.pub
```

Copy the line it prints. On GitHub, open the repository → **Settings → Deploy keys → Add deploy key**, paste it,
and leave *Allow write access* **off**. Then:

```bash
printf 'Host github.com\n  IdentityFile ~/.ssh/github\n' >> ~/.ssh/config
git clone git@github.com:pkvaishakh/dumbelo-gym-erp.git ~/dumbelo
ls ~/dumbelo/deploy/server          # Caddyfile  backup.sh  docker-compose.yml  update.sh
```

The server follows `main`. To try a branch first: `cd ~/dumbelo && git switch <branch>`.

## 8. The settings

```bash
cd ~/dumbelo/deploy/server
cp .env.example .env && chmod 600 .env
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 24)|" .env
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$(openssl rand -hex 50)|" .env
sed -i "s|^FIELD_ENCRYPTION_KEY=.*|FIELD_ENCRYPTION_KEY=$(openssl rand -base64 32 | tr '+/' '-_')|" .env
nano .env
```

The three `sed` lines make the secrets for you. In `nano`, set `API_DOMAIN`, `APP_DOMAIN` (just the name, without
`https://`), `ACME_EMAIL`, and `CONTACT_EMAIL` (sales' address, which the landing page shows gym owners). If sales
has a WhatsApp number, remove the `#` in front of `SALES_WHATSAPP` and put it there: the Chat on WhatsApp buttons
appear once it's set. Save with `Ctrl+O`, `Enter`, and quit with `Ctrl+X`. Check that no value is empty:

```bash
grep -E '^[A-Z_]+=$' .env || echo "all set"
```

Then **copy the whole file to a password manager**: `cat .env`, and copy what it prints. If this server is ever
lost, a backup restores the data, but only this file can read the WhatsApp credentials (`FIELD_ENCRYPTION_KEY`).
Never commit it. Git already ignores `.env`.

## 9. Start it

```bash
cd ~/dumbelo/deploy/server
bash update.sh
```

The first run builds both images, which takes about 5 to 10 minutes; later runs take about a minute. It ends with
`{"status":"ok","database":"ok"}` and `Deployed <commit>.` What it starts, in order: Postgres and Redis, then the
migrations (`migrate`, which exits when done), then the API, the worker, beat, the web app, and Caddy, which fetches
the HTTPS certificates for both names.

```bash
docker compose ps                     # every service "Up" (api "healthy"); migrate "Exited (0)"
docker compose logs caddy | grep -i "certificate obtained"
```

If something isn't up, read its log: `docker compose logs --tail 100 api` (or `web`, `caddy`, `worker`,
`migrate`). The fixes for the usual problems are under [When something's wrong](#when-somethings-wrong).

## 10. The first sign-in and the first gym

Make yourself a Dumbelo admin (it asks for a username, your name and a password; use a long one, from your password
manager). The username is how you sign in: lowercase letters, numbers, `.` and `_`, and not `admin` or `dumbelo`:

```bash
docker compose exec api python manage.py createsuperuser
```

Open `https://app.<your domain>/console` on your phone, sign in, and follow `docs/operations.md` ("Opening a
gym"). (`https://app.<your domain>` itself is the public landing page: gym owners who book a demo there show up in
Console → Leads.) In short: **Prices → Add Price List** first (no gym opens without one), then **New Gym**, which makes the
gym, its first branch and its owner's sign-in.

**Never run `seed_demo` on this server.** It builds the demo gym, with demo logins anyone can read in the README.

Then check the app works, on a phone: sign in as the gym's admin, add a member, sell a plan, collect a payment and
check someone in. From any terminal:

```bash
curl -s https://api.dumbelo.com/api/health/                                   # {"status":"ok","database":"ok"}
curl -s -o /dev/null -w '%{http_code}\n' https://api.dumbelo.com/api/me/      # 401: it wants a sign-in
docker compose logs worker | grep ready                                       # celery@... ready
```

## 11. Backups (do this the same day)

There are two layers. The first, DigitalOcean's weekly copy of the whole disk, has been on since step 2. The
second is a nightly copy of the database, at 3 AM IST, keeping the newest 14:

```bash
crontab -e            # choose nano if it asks, and add this line at the end:
30 21 * * * bash $HOME/dumbelo/deploy/server/backup.sh >> $HOME/backups.log 2>&1
```

(21:30 is in UTC, which is 3 AM IST.) Run it once by hand to see it work: `bash ~/dumbelo/deploy/server/backup.sh`.

The nightly copies live on the server, so also keep them **somewhere else**:

- **To start:** once a week, download them to your machine:
  ```powershell
  PS> scp -i $HOME\.ssh\dumbelo "dumbelo@139.59.10.20:backups/*.dump" D:\dumbelo-backups\
  ```
- **Better, once the gym is live:** DigitalOcean **Spaces** (about $5 a month), with `rclone` copying the folder to it
  from the same cron job, so nobody has to remember.

**Prove a backup restores** before you rely on it, and again every month (`docs/operations.md` has the drill).
This restores into a separate, throwaway database, not the live one:

```bash
cd ~/dumbelo/deploy/server
docker compose exec db createdb -U dumbelo drill
docker compose exec -T db pg_restore -U dumbelo -d drill --no-owner < "$(ls -1t ~/backups/*.dump | head -1)"
docker compose exec db psql -U dumbelo -d drill -c "select count(*) from members_member;"
docker compose exec db dropdb -U dumbelo drill
```

## 12. Deploying again

Merge to `main` on GitHub, then on the server:

```bash
cd ~/dumbelo/deploy/server && bash update.sh
```

It backs up the database, pulls, rebuilds, runs any new migrations, restarts what changed and checks the health
page. There's a few
seconds' gap while the API restarts. Fine for a gym: deploy in the afternoon, not at opening time or at 6 AM, when
the reminders go out.

**Going back** to an earlier commit: `cd ~/dumbelo && git switch --detach <good commit>`, then
`docker compose up -d --build` in `deploy/server`. When you're done: `git switch main`. Migrations are not undone
by this. If the bad commit changed data, restore a backup instead (`docs/operations.md`, "Restoring for real").

## 13. Before the gym relies on it

- [ ] Two-factor sign-in on DigitalOcean and GitHub (step 0).
- [ ] Signing in as `root` and with passwords is off (step 4).
- [ ] The `.env` is in a password manager (step 8).
- [ ] Nightly backups running, a copy off the server, and one restore drill done (step 11).
- [ ] **Alerts:** DigitalOcean → Monitoring → **Create alert policy**. Make three, each emailing you: CPU above 80%
  for 5 minutes, memory above 90%, disk above 80%.
- [ ] **Uptime check:** Monitoring → **Uptime** → check `https://api.<domain>/api/health/`, so you hear about it
  if the site goes down before the gym does.
- [ ] **Billing alert:** Billing → **Billing alerts**, at about $35.
- [ ] **The landing page:** `CONTACT_EMAIL` (and `SALES_WHATSAPP`, if any) set in `.env`; a test demo request from
  `https://app.<domain>` shows in Console → Leads; the sitemap submitted in Google Search Console (`PRODUCTION.md`,
  step 11). New leads are worth a call the same day.
- [ ] WhatsApp, when you're ready: add the account in the Console, set `WHATSAPP_PROVIDER=whatsapp_cloud` in `.env`,
  then run `bash update.sh`. Meta's webhook is `https://api.<domain>/api/whatsapp/webhook/` (`docs/deploy.md`, step 3).

## On Oracle Cloud instead

Everything from step 5 on is the same on an Oracle Cloud VM (Always Free is fine for studying). Steps 1–4 differ:

1. **Compute → Instances → Create instance**. Image **Canonical Ubuntu 24.04**. Shape **Ampere VM.Standard.A1.Flex,
   2 OCPU, 12 GB**, which is within Always Free's 4 OCPU / 24 GB. Don't use `E2.1.Micro`: 1 GB is too small to
   build the web app. Assign a public IPv4. Under SSH keys, paste the public key from step 1.
2. **Oracle's firewall:** Networking → Virtual cloud networks → your network → the public subnet → Default Security
   List → **Add Ingress Rules**: source `0.0.0.0/0`, TCP, port `80`, and again for `443`.
3. **Ubuntu's own firewall** blocks everything but SSH on Oracle's images. Open it **before** installing Docker:
   ```bash
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
   sudo netfilter-persistent save
   ```
4. Sign in as `ubuntu` (`ssh -i $HOME\.ssh\dumbelo ubuntu@<IP>`), which already has `sudo` and no `root` login,
   so skip making the `dumbelo` user.

When the 30-day trial ends, Always Free resources keep running. But Oracle deletes anything paid made with the
trial credits, and more than 4 OCPU / 24 GB of Ampere in total gets disabled. Back up the Oracle way too: Storage →
Boot volumes → assign the *Bronze* policy.

## When something's wrong

| What you see | Usually | Fix |
|---|---|---|
| The browser can't reach the site at all (times out) | The firewall | Step 3: the firewall exists, has 80 and 443, and is applied to the droplet. (On Oracle, check both of its firewalls) |
| Caddy log: `challenge failed` / `no such host` | The name doesn't point at this server yet, or port 80 is closed | Step 6's check, then `docker compose restart caddy`. Don't restart it over and over: Let's Encrypt limits failed tries per hour |
| `set SECRET_KEY in .env` (or another name) when starting | That line in `.env` is empty | Step 8 |
| API log: `PRODUCTION=true needs ...` | A setting is missing | Same as above |
| `Bad Request (400)` from the API | `API_DOMAIN` doesn't match the name in the browser | Fix `.env`, then `bash update.sh` |
| The app loads, but signing in fails with a network or CORS error | `APP_DOMAIN` is wrong, or the web app was built for another API address | Fix `.env`, then `bash update.sh` (the web image is rebuilt with the new address) |
| The build stops with `Killed` or `JavaScript heap out of memory` | Not enough memory | Check the swap from step 5 is on (`free -h`) |
| `permission denied ... docker.sock` | The Docker group hasn't applied yet | Sign out and in again |
| `Permission denied (publickey)` when signing in | Wrong key or wrong user | `-i $HOME\.ssh\dumbelo` and user `dumbelo` (`root` is off after step 4) |
| `migrate` shows `Exited (1)` | A migration failed | `docker compose logs migrate`. Nothing else starts until it's fixed, which is on purpose |
| The landing page shows `hello@dumbelo.com`, or no WhatsApp button | `CONTACT_EMAIL` or `SALES_WHATSAPP` isn't set (or still has its `#`) | Fix `.env`, then `bash update.sh`: they're built into the web app, so a restart isn't enough |

Locked out completely? DigitalOcean → the droplet → **Access → Recovery Console** signs you in from the browser,
without SSH (reset the root password there first if it asks for one).

Handy commands, run in `~/dumbelo/deploy/server`:

```bash
docker compose ps                         # what's running
docker compose logs -f --tail 50 api      # follow a service's log (Ctrl+C to stop following)
docker compose restart worker             # restart one service
docker compose exec api python manage.py shell     # a Django shell on the live database: be careful
docker compose down                       # stop everything (the data stays in the volumes)
df -h /  &&  free -h                      # disk and memory
```

Never run `docker compose down -v`. The `-v` deletes the volumes, and the database is in one of them.
