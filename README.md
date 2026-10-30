# The House of Hem

An online clothing store for women, men and kids, built with **FastAPI**, **MongoDB** and a dependency-free vanilla-JS frontend.

- Browse by category and product type (mega menu), search, filter by price and sort 100 demo products
- Wishlist, and quick-add sizes straight from the product grid
- Pick size, colour and quantity; a bag that follows your account across devices
- One-step checkout with server-side pricing and full order history
- Email/password accounts (optional Google Sign-In), profile photo, account deletion
- Admin dashboard: add, edit and delete products, or bulk-import from Excel + an images zip

## Run locally

Requires Python 3.10+ and a MongoDB database (a free [MongoDB Atlas](https://www.mongodb.com/atlas) cluster works).

```bash
python -m venv fashionagent
fashionagent\Scripts\activate            # macOS/Linux: source fashionagent/bin/activate
pip install -r requirements.txt
copy .env.example .env                   # macOS/Linux: cp .env.example .env
# edit .env and set MONGO_URI
python main.py
```

The browser opens at http://localhost:8000 (the next free port if 8000 is busy).

On startup the app:

- checks MongoDB is reachable and explains common problems (Atlas IP access list, wrong password, bad URI) in plain words
- creates its indexes
- upgrades data written by older versions of the app
- fills an **empty** catalogue with the 100 demo products in `demo_data/` (disable with `SEED_DEMO_DATA=false`)

## Admin access

Register on the site, then grant yourself admin rights from the project folder:

```bash
python -m backend.make_admin                     # list users and who is admin
python -m backend.make_admin you@example.com     # grant admin
python -m backend.make_admin you@example.com --revoke
```

Reload the site and a **Manage store** button appears. Admin rights live only in the database (`is_admin` on the user); nothing in the website can grant them.

## How login works

Logging in returns a token signed with `SECRET_KEY` (HMAC-SHA256). The browser sends it as `Authorization: Bearer <token>`, and the server identifies the user from the token alone, so a client can't claim to be someone else. Changing your password or email invalidates every older token. Carts and orders are keyed by user id, and prices are always read from the catalogue on the server.

## Configuration

All settings are environment variables (or `.env`); see `.env.example`.

| Variable | Default | Purpose |
|---|---|---|
| `MONGO_URI` | — | MongoDB connection string (required) |
| `SECRET_KEY` | generated into `.secret_key` | Signs login tokens. **Set it in production.** |
| `HOST` / `PORT` | `127.0.0.1` / `8000` | Use `HOST=0.0.0.0` when deploying |
| `SEED_DEMO_DATA` | `true` | Import demo products into an empty catalogue |
| `MAX_IMAGE_MB` | `5` | Largest product image accepted |
| `GOOGLE_CLIENT_ID` | empty | Enables the Google Sign-In button |

## Deploying (e.g. Render)

- Build command: `pip install -r requirements.txt`
- Start command: `python main.py`
- Environment: `MONGO_URI`, `SECRET_KEY`, `HOST=0.0.0.0` (Render provides `PORT`)
- In MongoDB Atlas → Network Access, allow the host's outbound IPs (or `0.0.0.0/0`)

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```

The suite runs against an in-memory MongoDB (mongomock), so it needs no database or network.

## Project layout

```
main.py                 app entry point, startup tasks, static frontend
backend/
  auth.py, tokens.py    login tokens and the current-user / admin checks
  routes/               products, bulk import, cart, orders, auth, profile, Google sign-in
  utils/                catalogue helpers, image validation, Excel importer, users
  seed.py               demo-data import
  make_admin.py         grant/revoke admin from the command line
frontend/
  index.html
  src/                  router, pages, components, API client (services/api/*)
demo_data/              100 demo products: spreadsheet + images
tests/                  pytest suite
```

## License

MIT — see [LICENSE](LICENSE).
