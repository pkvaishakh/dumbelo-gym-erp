# Deploy on one Oracle Cloud server

Dumbelo on a single Oracle Cloud VM: the API, its database, Redis, the background jobs and the web app, all in
Docker on one machine. It fits in Oracle's Always Free allowance. It's simpler and cheaper than the AWS setup in
`docs/deploy.md`, but everything is on one server, so the backups (step 10) are not optional.

Written for someone deploying for the first time. Do the steps in order. Each one ends with a check; don't go
on until it passes.

```
phone / laptop ──HTTPS──► Oracle VM (Ubuntu 24.04, Docker)
                            caddy :80 :443   gets the HTTPS certificates
                              ├── app.<domain> ──► web      (Next.js)
                              └── api.<domain> ──► api      (gunicorn) ──► db (Postgres 16), redis
                                                   worker, beat (the jobs) ──┘
```

Everything lives in [`deploy/oracle/`](../deploy/oracle/): `docker-compose.yml` (the containers),
`Caddyfile` (the HTTPS front door), `.env.example` (the settings), `backup.sh` and `update.sh`.

Commands in `PS>` blocks run in PowerShell on your Windows machine. All the others run on the server, over SSH.

## 0. Before you start

- An Oracle Cloud account (cloud.oracle.com). Pick **India South (Hyderabad)** or **India West (Mumbai)** as the
  home region, so the gym's data and the app's speed stay in India. The home region can't be changed later.
- The code on GitHub, including the `deploy/oracle/` folder. The server downloads it from there.
- A domain, if you have one (`dumbelo.com` → `api.dumbelo.com` and `app.dumbelo.com`). No domain yet is fine for
  a trial: step 5 uses a free `sslip.io` name instead.

## 1. Create the server

Oracle console → **Compute → Instances → Create instance**.

| Field | Choose | Why |
|---|---|---|
| Name | `dumbelo` | |
| Image | **Canonical Ubuntu 24.04** | The commands below are written for Ubuntu |
| Shape | **Ampere → VM.Standard.A1.Flex**, **2 OCPU, 12 GB** memory | Always Free covers up to 4 OCPU / 24 GB in total. Don't use `VM.Standard.E2.1.Micro`: its 1 GB is too small to build the web app |
| Networking | Create a new virtual cloud network and a **public** subnet; **assign a public IPv4 address** | So the internet can reach it |
| SSH keys | **Generate a key pair for me**, then **Save private key** | Your only way in. Keep this file safe |
| Boot volume | Default (about 47 GB) is enough; up to 200 GB is free | |

Press **Create**. After a minute it reads **Running**; copy its **Public IP address** (it looks like `140.238.10.20`).

**"Out of capacity"?** Free Ampere machines often run out. Try another *Availability domain* on the same page, or try
again later. Upgrading the account to **Pay As You Go** (Billing → Upgrade) almost always fixes it. Always Free
resources stay free after you upgrade, and it also stops Oracle from reclaiming the server (step 12).

**Keep the IP from changing (recommended):** Networking → IP management → **Reserved public IPs** → Reserve. Then, on
the instance, open **Attached VNICs** → the VNIC → **IPv4 addresses**. Edit the address to *No public IP*, then
edit it again to the reserved IP. Do this before step 5, because your DNS will point at this address.

## 2. Open ports 80 and 443 in Oracle's firewall

There are two firewalls: Oracle's, in front of the server (this step), and Ubuntu's, on it (step 3). Both block
web traffic until you open them.

Networking → **Virtual cloud networks** → your network → **Subnets** → the public subnet → **Security lists** →
*Default Security List* → **Add Ingress Rules**. Add two rules:

| Source CIDR | IP protocol | Destination port range |
|---|---|---|
| `0.0.0.0/0` | TCP | `80` |
| `0.0.0.0/0` | TCP | `443` |

Port 22 (SSH) is open already. Don't open anything else: Postgres and Redis must never be reachable from outside.

## 3. Get onto the server

Move the key you saved to your SSH folder and make it private. SSH refuses keys that other Windows users can read.

```powershell
PS> mkdir $HOME\.ssh -Force
PS> move $HOME\Downloads\ssh-key-*.key $HOME\.ssh\dumbelo.key
PS> icacls $HOME\.ssh\dumbelo.key /inheritance:r /grant:r "$($env:USERNAME):R"
PS> ssh -i $HOME\.ssh\dumbelo.key ubuntu@140.238.10.20
```

Answer `yes` the first time. You should see `ubuntu@dumbelo:~$`. That is the server; everything from here on
runs there. (`exit` takes you back to Windows.)

Optional shortcut: add this to `$HOME\.ssh\config` on Windows, and after that `ssh dumbelo` is enough:

```
Host dumbelo
  HostName 140.238.10.20
  User ubuntu
  IdentityFile ~/.ssh/dumbelo.key
```

Now open Ubuntu's own firewall. Oracle's Ubuntu images block everything except SSH. Do this **before** installing
Docker, because the last line saves the rules as they are right then:

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

## 4. Prepare the server

Updates, some swap (spare memory on disk, so a big build doesn't run out), and Docker:

```bash
sudo apt update && sudo apt -y upgrade
sudo fallocate -l 4G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
exit
```

SSH in again (the Docker group only applies to a new sign-in), then check:

```bash
docker run --rm hello-world        # "Hello from Docker!"
docker compose version             # v2.something
```

Ubuntu installs security updates by itself (`unattended-upgrades`). Reboot now and then: `sudo reboot`.
Everything comes back on its own, because every container is `restart: unless-stopped`.

## 5. Point the names at the server

**With a domain:** at the company you bought it from (GoDaddy, Namecheap, Cloudflare and so on), add two **A** records:

| Type | Name | Value |
|---|---|---|
| A | `api` | the server's public IP |
| A | `app` | the server's public IP |

On Cloudflare, set both to **DNS only** (grey cloud), at least until the certificates are issued.

**Without a domain (a trial only):** use `sslip.io`, which turns a name into an IP for free and needs no setup.
With IP `140.238.10.20` the names are `api.140-238-10-20.sslip.io` and `app.140-238-10-20.sslip.io`. Move to a real
domain before a gym uses it.

Check, from the server or from Windows. Both names must answer with your IP before step 8:

```bash
getent hosts api.dumbelo.com app.dumbelo.com      # on Windows: nslookup api.dumbelo.com
```

## 6. Get the code onto the server

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
ls ~/dumbelo/deploy/oracle          # Caddyfile  backup.sh  docker-compose.yml  update.sh
```

The server follows `main`. To try a branch first: `cd ~/dumbelo && git switch <branch>`.

## 7. The settings

```bash
cd ~/dumbelo/deploy/oracle
cp .env.example .env && chmod 600 .env
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 24)|" .env
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$(openssl rand -hex 50)|" .env
sed -i "s|^FIELD_ENCRYPTION_KEY=.*|FIELD_ENCRYPTION_KEY=$(openssl rand -base64 32 | tr '+/' '-_')|" .env
nano .env
```

The three `sed` lines make the secrets for you. In `nano`, set `API_DOMAIN`, `APP_DOMAIN` (no `https://`, just the
name) and `ACME_EMAIL`. Save with `Ctrl+O`, `Enter`, and quit with `Ctrl+X`. Check that no value is empty:

```bash
grep -E '^[A-Z_]+=$' .env || echo "all set"
```

Then **copy the whole file to a password manager**: `cat .env`, and copy what it prints. If this server is ever
lost, a backup restores the data, but only this file can read the WhatsApp credentials (`FIELD_ENCRYPTION_KEY`).
Never commit it. Git already ignores `.env`.

## 8. Start it

```bash
cd ~/dumbelo/deploy/oracle
bash update.sh
```

The first run builds both images. On 2 OCPUs that takes about 5 to 15 minutes; later runs take about a minute.
It ends with `{"status":"ok","database":"ok"}` and `Deployed <commit>.` What it starts, in order: Postgres and Redis,
then the migrations (`migrate`, which exits when done), then the API, the worker, beat, the web app, and Caddy,
which fetches the HTTPS certificates for both names.

```bash
docker compose ps                     # every service "Up" (api "healthy"); migrate "Exited (0)"
docker compose logs caddy | grep -i "certificate obtained"
```

If something isn't up, read its log: `docker compose logs --tail 100 api` (or `web`, `caddy`, `worker`,
`migrate`). The fixes for the usual problems are under [When something's wrong](#when-somethings-wrong).

## 9. The first sign-in and the first gym

Make yourself a Dumbelo admin (it asks for an email and a password):

```bash
docker compose exec api python manage.py createsuperuser
```

Open `https://app.<your domain>/console` on your phone, sign in, and follow `docs/operations.md` ("Opening a
gym"). In short: **Prices → Add Price List** first (no gym opens without one), then **New Gym**, which makes the
gym, its first branch and its owner's sign-in.

Don't run `seed_demo` here. It builds the demo gym, not a real one. (On a server that is only for showing the demo,
`docker compose exec api python manage.py seed_demo` is fine.)

Then check the app works, on a phone: sign in as the gym's admin, add a member, sell a plan, collect a payment and
check someone in. From any terminal:

```bash
curl -s https://api.dumbelo.com/api/health/                                   # {"status":"ok","database":"ok"}
curl -s -o /dev/null -w '%{http_code}\n' https://api.dumbelo.com/api/me/      # 401: it wants a sign-in
docker compose logs worker | grep ready                                       # celery@... ready
```

## 10. Backups (do this the same day)

Every night at 3 AM IST, keep the newest 14 copies:

```bash
crontab -e            # choose nano if it asks, and add this line at the end:
30 21 * * * /usr/bin/bash /home/ubuntu/dumbelo/deploy/oracle/backup.sh >> /home/ubuntu/backups.log 2>&1
```

(21:30 is in UTC, which is 3 AM IST.) Run it once by hand to see it work: `bash ~/dumbelo/deploy/oracle/backup.sh`.

A copy on the same server is lost along with the server, so also keep copies **somewhere else**:

- **Simplest:** once a week, download them to your machine:
  ```powershell
  PS> scp -i $HOME\.ssh\dumbelo.key "ubuntu@140.238.10.20:backups/*.dump" D:\dumbelo-backups\
  ```
- **Automatic:** Oracle Object Storage (20 GB free). Make a bucket and copy the folder to it nightly with `rclone`,
  run from the same cron job.
- **And:** Oracle console → Storage → **Boot volumes** → your volume → assign the *Bronze* backup policy. That's a
  copy of the whole disk, kept by Oracle.

**Prove a backup restores** before you rely on it, and again every month (`docs/operations.md` has the drill).
This restores into a separate, throwaway database, not the live one:

```bash
cd ~/dumbelo/deploy/oracle
docker compose exec db createdb -U dumbelo drill
docker compose exec -T db pg_restore -U dumbelo -d drill --no-owner < "$(ls -1t ~/backups/*.dump | head -1)"
docker compose exec db psql -U dumbelo -d drill -c "select count(*) from members_member;"
docker compose exec db dropdb -U dumbelo drill
```

## 11. Deploying again

Merge to `main` on GitHub, then on the server:

```bash
cd ~/dumbelo/deploy/oracle && bash update.sh
```

It pulls, rebuilds, runs any new migrations, restarts what changed and checks the health page. There's a few
seconds' gap while the API restarts. Fine for a gym; just don't deploy at 6 AM, when the reminders go out.

**Going back** to an earlier commit: `cd ~/dumbelo && git switch --detach <good commit>`, then
`docker compose up -d --build` in `deploy/oracle`. When you're done: `git switch main`. Migrations are not undone
by this. If the bad commit changed data, restore a backup instead (`docs/operations.md`, "Restoring for real").

## 12. Before a real gym relies on it

- **Upgrade to Pay As You Go.** On a free-only account, Oracle may *reclaim* (stop) an Always Free server that looks
  idle for a week, and a small gym's server can look idle. After upgrading, the Always Free resources still cost
  nothing. To make sure, set a budget alert: Billing → Budgets → ₹100.
- A real domain, not `sslip.io`.
- Backups running, a copy off the server, and one restore drill done (step 10).
- The `.env` in a password manager (step 7).
- WhatsApp, when you're ready: add the account in the Console, set `WHATSAPP_PROVIDER=whatsapp_cloud` in `.env`,
  then run `bash update.sh`. Meta's webhook is `https://api.<domain>/api/whatsapp/webhook/` (`docs/deploy.md`, step 3).

## When something's wrong

| What you see | Usually | Fix |
|---|---|---|
| The browser can't reach the site at all (times out) | A firewall | Step 2 (Oracle's security list) **and** step 3 (`iptables`). Check: `sudo iptables -L INPUT -n --line-numbers` shows ACCEPT for 80 and 443 above the REJECT line |
| Caddy log: `challenge failed` / `no such host` | The name doesn't point at this server yet, or port 80 is closed | Step 5's check, then `docker compose restart caddy`. Don't restart it over and over: Let's Encrypt limits failed tries per hour |
| `set SECRET_KEY in .env` (or another name) when starting | That line in `.env` is empty | Step 7 |
| API log: `PRODUCTION=true needs ...` | A setting is missing | Same as above |
| `Bad Request (400)` from the API | `API_DOMAIN` doesn't match the name in the browser | Fix `.env`, then `bash update.sh` |
| The app loads, but signing in fails with a network or CORS error | `APP_DOMAIN` is wrong, or the web app was built for another API address | Fix `.env`, then `bash update.sh` (the web image is rebuilt with the new address) |
| The build stops with `Killed` or `JavaScript heap out of memory` | Not enough memory | Check the swap from step 4 is on (`free -h`), or give the instance more memory |
| `permission denied ... docker.sock` | The Docker group hasn't applied yet | `exit` and SSH in again |
| `migrate` shows `Exited (1)` | A migration failed | `docker compose logs migrate`. Nothing else starts until it's fixed, which is on purpose |

Handy commands, run in `~/dumbelo/deploy/oracle`:

```bash
docker compose ps                         # what's running
docker compose logs -f --tail 50 api      # follow a service's log (Ctrl+C to stop following)
docker compose restart worker             # restart one service
docker compose exec api python manage.py shell     # a Django shell on the live database: be careful
docker compose down                       # stop everything (data stays in the volumes)
df -h /  &&  free -h                      # disk and memory
```

Never run `docker compose down -v`. The `-v` deletes the volumes, and the database is in one of them.
