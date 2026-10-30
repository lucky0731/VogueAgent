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

## Shopping assistant (chatbot)

`chatbot/` is an AI shopping assistant that reads the same MongoDB catalogue. Shoppers can:

- **type** a request ("men's shirts under 2000") — a pydantic-ai agent on Groq searches the catalogue
- **speak** it — the recording is transcribed with Whisper and answered the same way
- **share a photo** — a vision model tags the garment and colours, and the closest lookalikes are ranked by tags plus colour similarity

Every result links to its product page in the store. Inputs and replies pass through guardrail models (prompt-injection and content-policy checks). Calls go through the Portkey gateway when configured, falling back to Groq directly.

```bash
cd chatbot
python -m venv webchatbot                # or: uv venv webchatbot
webchatbot\Scripts\activate
pip install -r requirements.txt          # or: uv pip install -r requirements.txt
copy .env.example .env                   # set MONGO_URI and GROQ_API_KEY
python main.py                           # http://localhost:8001
```

### Run the store and the assistant together

From the project root, with both environments set up:

```bash
python run_all.py
```

It starts the store (port 8000) and the assistant (port 8001) in their own environments, points the assistant's product links at the store's actual port, shows both logs in one window and opens both in the browser. Ctrl+C stops both.

To run the assistant on its own, the store must also be running for product links to open; if it isn't on port 8000, set `STORE_URL` in `chatbot/.env`.

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
run_all.py              start the store and the shopping assistant together
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
chatbot/                AI shopping assistant: text, voice and photo search (separate app)
```

## License

MIT — see [LICENSE](LICENSE).
