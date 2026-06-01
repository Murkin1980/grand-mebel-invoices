# Render deploy guide

## 1. Create Blueprint

1. Open Render Dashboard.
2. New -> Blueprint.
3. Connect repository:

```text
https://github.com/Murkin1980/grand-mebel-invoices
```

4. Select branch:

```text
master
```

5. Render will read `render.yaml` and create:

- web service `grand-mebel-invoices`;
- PostgreSQL database `grand-mebel-invoices-db`;
- `DATABASE_URL` env var linked to the database.

## 2. Check environment variables

Render should set:

```text
PYTHON_VERSION=3.11.0
SECRET_KEY=<generated>
DATABASE_URL=<from Render Postgres>
```

Optional later:

```text
ESF_SENDER_BIN=910226302322
```

Do not store EDS `.p12` or EDS password in Render env vars for production use. XML signing is intended to happen through NCALayer on the user's computer.

## 3. First deploy

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT
```

The app will create DB tables on startup because `app.py` runs `init_db()`.

## 4. Important: existing local invoices

The local SQLite database with imported Grand Mebel invoices is not automatically uploaded to Render PostgreSQL.

After the Render app is live, migrate or re-import:

- contractors;
- products;
- invoices;
- invoice items.

Current local import state:

- invoices are imported up to number `36`;
- next invoice should be `37`;
- local SQLite backup files are in `instance/`.

## 5. Smoke test

After deploy:

1. Open the Render URL.
2. Confirm app loads.
3. Create or import a test invoice.
4. Download:
   - invoice XLSX;
   - AVR XLSX;
   - tax invoice XLSX;
   - waybill XLSX;
   - ESF XML.
5. On a Windows machine with NCALayer running, open the invoice and click:

```text
Подписать XML через NCALayer
```

## 6. Next production hardening

Before using with real accounting documents on a public URL:

- add login/password;
- disable public access without auth;
- add backups;
- add R2/Supabase Storage for generated files;
- add migration from local SQLite to Render PostgreSQL;
- verify ESF XML and sending flow in the official test contour.
