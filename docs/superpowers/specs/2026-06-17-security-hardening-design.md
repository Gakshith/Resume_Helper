# Security Hardening — Design Spec

Date: 2026-06-17
Status: Shipped (commit a6a597b). Backfilled spec (written after a parallel
security-architect + code-analyzer swarm review surfaced the findings).

## Goal

Close the high-severity findings from the swarm security audit without breaking the
existing flow or requiring a user-data migration step.

## Decisions

1. **Password hashing** — bcrypt via passlib. Register stores a hash; login verifies.
   Legacy plaintext records are transparently re-hashed on first successful login
   (no separate migration). Pin `bcrypt==4.0.1` (passlib 1.7.4 is incompatible with
   bcrypt ≥4.1: `module 'bcrypt' has no attribute '__about__'`).
2. **Upload safety** — reject >5 MB (content-length + post-read), validate the `%PDF`
   magic bytes (not just the extension), and store on disk under a random
   `token_hex.pdf` name so the client filename can't drive path traversal.
3. **Per-user PDF authorization** — remove the public `/uploads` static mount; serve
   PDFs via an authenticated `GET /uploads/{name}` route that checks the requesting
   user owns the file (`upload_owners` map) and blocks `..`/slashes.
4. **Hardening extras** — cookie `max_age`; generic error messages (no exception
   string leakage) on register/upload.

## Verification (live)

USER plaintext → `$2b$` hash on login; wrong password 401; owner reads PDF (200) but
another user blocked (403); path traversal 404; non-PDF rejected. Analysis tests: 20 pass.

## Explicitly deferred (still open)

CSRF tokens, login rate-limiting, the process-wide `ssl` verify-disable (`app.py`),
and `pickle.load` integrity verification on the model artifact. Tracked in
`Plans/ROADMAP.md`.
