# World Cooking Challenge Site

A small Flask app for your cultural cooking competition. Participants can:

- register with their name
- choose one of the event countries
- pick a country-specific dish
- see who else has joined the same country team

The organizer gets a private dashboard with the full registration database and CSV export.

## Countries included

- Kenya
- Germany
- Uganda
- Nigeria
- Cameroon
- Zimbabwe

## Project structure

- `app.py` - Flask app and SQLite logic
- `templates/` - page templates
- `static/` - styling and client-side interactivity
- `instance/registrations.db` - SQLite database created automatically when the app starts

## Run locally

1. Create and activate a virtual environment if you want one.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Set an organizer password before you share the site:

```powershell
$env:EVENT_ADMIN_PASSWORD="your-secure-password"
```

4. Optional: set a stronger Flask session secret:

```powershell
$env:FLASK_SECRET_KEY="replace-this-with-a-long-random-value"
```

5. Start the app:

```powershell
python app.py
```

6. Open `http://127.0.0.1:5000`

If you prefer, you can also double-click `start-site.bat` to launch the site.

## Use on other devices on the same Wi-Fi

1. Start the LAN version:

```powershell
.\start-site-lan.bat
```

2. Find this computer's local IP address.
3. On phones, tablets, or other computers on the same network, open:

```text
http://YOUR-PC-IP:5000
```

Example:

```text
http://192.168.1.20:5000
```

If Windows Firewall blocks the connection, allow port `5000` for your private network.
You can right-click `allow-firewall-port-5000.bat` and choose `Run as administrator`.

## Organizer access

- Organizer login page: `/admin/login`
- Default password if you do not set one: `change-me`

Change that password before deploying or sharing the site publicly.

## Free internet hosting recommendation

This project is prepared for a no-pay setup that is good enough for a small event site:

- Render Free web service for the Flask app
- Neon Free Postgres for the database
- Gunicorn for production serving

### Why this combination

SQLite is fine on one local computer, but it is not a good choice for a public hosted service because hosted filesystems can restart or be replaced. For internet hosting, this app now uses:

- local SQLite when `DATABASE_URL` is not set
- PostgreSQL when `DATABASE_URL` is provided by Render

This free combination is the practical option because:

- Render Free web services are available, but Render Free Postgres expires 30 days after creation.
- Neon Free Postgres has no monthly price and is better for keeping the registration data long enough for an event.

### Free-tier caveats

Expect these limits:

- Render Free spins down after 15 minutes with no traffic, and waking back up can take about 1 minute.
- Neon Free scales to zero after 5 minutes of inactivity.
- This is fine for testing, sharing, and a modest event site, but not ideal for a high-traffic or always-on production service.

### Free deploy steps

1. Put this project in a GitHub repository.
2. Create a free Neon account at `https://console.neon.tech`.
3. Create a new Neon project and copy its Postgres connection string.
4. Create a free Render account.
5. In Render, create a new Blueprint from your GitHub repository.
6. Render will read `render.yaml` and create the free web service.
7. During setup, Render will ask for:
   - `DATABASE_URL` -> paste the Neon connection string
   - `EVENT_ADMIN_PASSWORD` -> your organizer password
8. Wait for the deploy to finish.
9. Open the generated `https://...onrender.com` URL and test registration.

### Important environment values

- `EVENT_ADMIN_PASSWORD` - organizer login password
- `FLASK_SECRET_KEY` - generated automatically by Render
- `DATABASE_URL` - paste the Neon Postgres connection string here
- `SESSION_COOKIE_SECURE=1` - already set in `render.yaml` for HTTPS

### If you want paid hosting later

You can later upgrade to:

- a paid Render web service for no spin-downs
- a paid database if you outgrow Neon Free

### Sources

- Render free hosting docs: https://render.com/docs/free
- Render web service docs: https://render.com/docs/web-services
- Render Blueprint docs: https://render.com/docs/blueprint-spec
- Render pricing: https://render.com/pricing
- Neon pricing: https://neon.com/pricing
