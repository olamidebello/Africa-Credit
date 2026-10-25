# Africa Credit
Know your credit. Grow your future.

Initial runnable platform with original branding, responsive member and admin portals, SQLite storage, scrypt passwords, CSRF, session expiry, account status controls, tenant-scoped authorization, cases, partner catalog, calculations, consents and audit records. Python standard library only.

## Run
```
export SETUP_TOKEN="$(python3 -c 'import secrets; print(secrets.token_urlsafe(40))')"
COOKIE_SECURE=0 python3 app.py
```
Open http://127.0.0.1:18840/?setup and enter the token from your local environment to create the first super admin. Never commit or share this token. Use HTTPS and COOKIE_SECURE=1 outside localhost.

## Deploy on Olamidepanel
The production domain is credit.africandroid.world. Point its DNS A record at your Olamidepanel server before deployment. The playbook refuses to replace an unrelated application.
```
ansible-playbook -i 'YOUR_SERVER,' -u YOUR_SSH_USER deploy/hosting.yml -e credit_domain=credit.africandroid.world -e letsencrypt_email=YOUR_EMAIL
```
First-install setup token lives in /etc/africa-credit.env, readable only by root. Visit /?setup once. Service database is private in /var/lib/africa-credit. No default admin password. This project uses a dedicated systemd/nginx deployment and does not modify Olamidepanel’s undocumented inventory database.

## Android
Android WebView client, HTTPS-only, external links in browser, no JS native bridge, no TLS-error bypass. GitHub Actions builds a development APK and publishes a prerelease download. Production signing is not configured. Set the appUrl Gradle property only after verifying an unoccupied Africa Credit deployment. Publication is blocked until credit.africandroid.world verifies as Africa Credit.

## Actual scope and remaining work
Working: registration/sign-in/logout, guarded first-admin setup, member case submission/history, role-protected case updates, user suspension, organization creation, tenant-scoped queries, offer publishing, education, repayment calculator, legal notices, download page, mobile source and deployment automation.

Not implemented as live services: official bureau reports/scores/history, score simulation, identity verification, freezes/locks, dispute delivery to bureaus, banking/transfers/cards, aggregation, bill reporting, cash advances, insurance quoting, tax preparation/e-file, business-report purchasing, subscriptions/payments, automatic recovery emails, document evidence uploads, push/SMS/email, partner callbacks, approval models, privacy export/deletion execution, tenant self-service onboarding/branding/domains, custom staff roles and tenant membership provisioning GUI. Their request screens save cases only. No fake financial data or completed provider actions are displayed. Provider credentials/contracts and additional engineering are required. This is an initial foundation, not feature parity with Credit Karma/Experian.

Legal pages require operator identity/contact/territory and professional review before commercial launch. Production operations also require managed TLS, backups, monitoring, proxy-level rate limits, concurrency/load assessment and security review. The built-in HTTP server is an initial implementation behind nginx, not a high-scale application runtime.

## Verify
```
python3 -m unittest discover -s tests -v
node --check static/app.js
```

## Pull and deploy directly on the hosting server

Ensure DNS A record credit.africandroid.world points to 181.214.149.146 and remove any conflicting AAAA record if that server does not serve IPv6. Run these commands over your existing server SSH session:

```bash
sudo apt-get update
sudo apt-get install -y git ansible
sudo git clone https://github.com/olamidebello/Africa-Credit.git /opt/africa-credit-deployer
sudo bash /opt/africa-credit-deployer/deploy/pull-and-deploy.sh
```

If the deployer already exists, omit the clone and run the last command. It fetches and fast-forwards main before running the local Ansible playbook. Local changes cause a stop rather than being discarded.

The certificate contact defaults to dobcalldemo@gmail.com. Override if needed:

```bash
sudo bash /opt/africa-credit-deployer/deploy/pull-and-deploy.sh -e letsencrypt_email=YOUR_EMAIL
```

This installs dependencies, backs up an existing SQLite database under /var/backups/africa-credit, pulls the application into /opt/africa-credit, starts its isolated systemd service, preserves an existing Africa Credit nginx/TLS configuration, obtains HTTPS and checks health. Open https://credit.africandroid.world/?setup for first-admin setup using the private server setup token. No SSH password or production secrets are committed. This script does not provision registrar DNS or publish an APK, and successful GitHub publication does not establish that it has run on your server.

## Signed Android download and store publication (1.0.1)
The checked-in APK is signed with the dedicated privately backed-up Africa Credit key, package world.africandroid.credit, minSdk 26, targetSdk 35, version code 2. APK v2/v3 signatures and the published checksum have been verified. No emulator or physical-device test was available. This is an Android HTTPS website client, not a native implementation of every finance service. File downloads and unsupported flows may require the browser.

Direct repository download: https://raw.githubusercontent.com/olamidebello/Africa-Credit/main/static/downloads/africa-credit.apk

On the existing Olamidepanel server:
```bash
git -C /opt/africa-credit-deployer pull --ff-only origin main
ansible-playbook -i localhost, -c local /opt/africa-credit-deployer/deploy/mobile-and-store.yml
```
The playbook verifies the bundled checksum, updates the existing African Apps Store, publishes its download and hosted listing, then updates Africa Credit's install page and APK. It requires both existing services and the existing store database. If its database is elsewhere, pass -e credit_store_database=/absolute/path/store.sqlite3. Existing code/databases are backed up by the store updater. This playbook is not a fresh install of either service.

After successful deployment:
- https://credit.africandroid.world/download.html
- https://credit.africandroid.world/downloads/africa-credit.apk
- https://africanappsstore.space/downloads/africa-credit.apk
- https://africanappsstore.space/#Hosted%20apps

The SDK workflow no longer requests the obsolete tools package. It produces debug artifacts separately; do not replace the distributed APK with a differently signed debug build. Keep the private signing backup out of GitHub.
