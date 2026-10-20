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
The requested jobs.africandroid.world is occupied by Africa Jobs. Deployment refuses to replace it. Choose an unused domain and point its DNS at the hosting server first.
```
ansible-playbook -i 'YOUR_SERVER,' -u YOUR_SSH_USER deploy/hosting.yml -e credit_domain=YOUR_UNUSED_DOMAIN -e letsencrypt_email=YOUR_EMAIL
```
First-install setup token lives in /etc/africa-credit.env, readable only by root. Visit /?setup once. Service database is private in /var/lib/africa-credit. No default admin password. This project uses a dedicated systemd/nginx deployment and does not modify Olamidepanel’s undocumented inventory database.

## Android
Android WebView client, HTTPS-only, external links in browser, no JS native bridge, no TLS-error bypass. GitHub Actions builds a development APK and publishes a prerelease download. Production signing is not configured. Set the appUrl Gradle property only after verifying an unoccupied Africa Credit deployment. The default domain is blocked in workflow verification until it serves Africa Credit.

## Actual scope and remaining work
Working: registration/sign-in/logout, guarded first-admin setup, member case submission/history, role-protected case updates, user suspension, organization creation, tenant-scoped queries, offer publishing, education, repayment calculator, legal notices, download page, mobile source and deployment automation.

Not implemented as live services: official bureau reports/scores/history, score simulation, identity verification, freezes/locks, dispute delivery to bureaus, banking/transfers/cards, aggregation, bill reporting, cash advances, insurance quoting, tax preparation/e-file, business-report purchasing, subscriptions/payments, automatic recovery emails, document evidence uploads, push/SMS/email, partner callbacks, approval models, privacy export/deletion execution, tenant self-service onboarding/branding/domains, custom staff roles and tenant membership provisioning GUI. Their request screens save cases only. No fake financial data or completed provider actions are displayed. Provider credentials/contracts and additional engineering are required. This is an initial foundation, not feature parity with Credit Karma/Experian.

Legal pages require operator identity/contact/territory and professional review before commercial launch. Production operations also require managed TLS, backups, monitoring, proxy-level rate limits, concurrency/load assessment and security review. The built-in HTTP server is an initial implementation behind nginx, not a high-scale application runtime.

## Verify
```
python3 -m unittest discover -s tests -v
node --check static/app.js
```
