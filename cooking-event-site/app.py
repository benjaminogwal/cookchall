import csv
import io
import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    flash,
    g,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import DateTime, Integer, String, create_engine, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from werkzeug.middleware.proxy_fix import ProxyFix


COUNTRY_DISHES = {
    "Kenya": [
        "Nyama Choma",
        "Githeri",
        "Sukuma Wiki",
        "Mukimo",
        "Kenyan Pilau",
    ],
    "Germany": [
        "Sauerbraten",
        "Schnitzel",
        "Kaesespaetzle",
        "Bratwurst and Sauerkraut",
        "Kartoffelpuffer",
    ],
    "Uganda": [
        "Luwombo",
        "Rolex",
        "Matoke",
        "Groundnut Stew",
        "Posho and Beans",
    ],
    "Nigeria": [
        "Jollof Rice",
        "Egusi Soup",
        "Suya",
        "Pounded Yam and Ogbono Soup",
        "Moi Moi",
    ],
    "Cameroon": [
        "Ndole",
        "Eru",
        "Koki Beans",
        "Poulet DG",
        "Achu Soup",
    ],
    "Zimbabwe": [
        "Sadza with Beef Stew",
        "Dovi",
        "Muriwo Unedovi",
        "Mapopo Candy",
        "Mazondo",
    ],
}

COUNTRY_DETAILS = {
    "Kenya": {
        "flag": "🇰🇪",
        "spotlight": "Nyama Choma",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Nyama%20Choma.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Nyama_Choma.jpg",
        "image_credit": "Samuel Kiongo / Wikimedia Commons",
        "image_alt": "Nyama choma grilling over charcoal",
    },
    "Germany": {
        "flag": "🇩🇪",
        "spotlight": "Schnitzel",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Iranian%20schnitzel.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Iranian_schnitzel.jpg",
        "image_credit": "Guywithacoolname / Wikimedia Commons",
        "image_alt": "Schnitzel served with fries and lemon",
    },
    "Uganda": {
        "flag": "🇺🇬",
        "spotlight": "Luwombo",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Traditional%20Ugandan%20Luwombo.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Traditional_Ugandan_Luwombo.jpg",
        "image_credit": "Nabunje Leticia / Wikimedia Commons",
        "image_alt": "Traditional Ugandan luwombo wrapped in banana leaves",
    },
    "Nigeria": {
        "flag": "🇳🇬",
        "spotlight": "Jollof Rice",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Jollof%20Rice.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Jollof_Rice.jpg",
        "image_credit": "ChukaMadu / Wikimedia Commons",
        "image_alt": "A plate of Nigerian jollof rice",
    },
    "Cameroon": {
        "flag": "🇨🇲",
        "spotlight": "Poulet DG",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Poulet%20DG.JPG",
        "image_source": "https://commons.wikimedia.org/wiki/File:Poulet_DG.JPG",
        "image_credit": "Affirebecca / Wikimedia Commons",
        "image_alt": "Cameroonian poulet DG with plantain",
    },
    "Zimbabwe": {
        "flag": "🇿🇼",
        "spotlight": "Sadza with Beef Stew",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/A%20plate%20of%20sadza.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:A_plate_of_sadza.jpg",
        "image_credit": "Tafadzwa Albert Mappurisa / Wikimedia Commons",
        "image_alt": "A plate of Zimbabwean sadza with meat and vegetables",
    },
}

ORGANIZER = {
    "name": "Campus Connect Vibes Team",
    "strapline": "Campus Connect cultural cook-off organizer",
    "message": "Bringing students together through food, teamwork, and cultural pride.",
}


class Base(DeclarativeBase):
    pass


class Registration(Base):
    __tablename__ = "registrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    country: Mapped[str] = mapped_column(String(40), nullable=False)
    dish: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        server_default=func.now(),
        nullable=False,
    )


def normalize_database_url(database_url):
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


def create_db_engine(database_url):
    engine_options = {"pool_pre_ping": True}
    if database_url.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **engine_options)


def format_timestamp(value):
    if value is None:
        return ""
    if hasattr(value, "isoformat"):
        return value.isoformat(sep=" ", timespec="seconds")
    return str(value)


def build_country_data():
    return {
        country: {
            **COUNTRY_DETAILS[country],
            "dishes": dishes,
        }
        for country, dishes in COUNTRY_DISHES.items()
    }


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    default_database_url = normalize_database_url(
        os.environ.get(
            "DATABASE_URL",
            f"sqlite:///{os.path.join(app.instance_path, 'registrations.db')}",
        )
    )

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me"),
        DATABASE_URL=default_database_url,
        ADMIN_PASSWORD=os.environ.get("EVENT_ADMIN_PASSWORD", "change-me"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.environ.get("SESSION_COOKIE_SECURE", "0") == "1",
    )

    if test_config:
        app.config.update(test_config)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
    app.config["DATABASE_URL"] = normalize_database_url(app.config["DATABASE_URL"])
    app.extensions["db_engine"] = create_db_engine(app.config["DATABASE_URL"])
    app.extensions["db_sessionmaker"] = sessionmaker(
        bind=app.extensions["db_engine"],
        expire_on_commit=False,
    )
    country_data = build_country_data()

    def get_db():
        if "db_session" not in g:
            g.db_session = app.extensions["db_sessionmaker"]()
        return g.db_session

    def init_db():
        Base.metadata.create_all(bind=app.extensions["db_engine"])

    def close_db(_error=None):
        db = g.pop("db_session", None)
        if db is not None:
            db.close()

    def get_country_counts():
        counts = {country: 0 for country in COUNTRY_DISHES}
        rows = get_db().execute(
            select(Registration.country, func.count(Registration.id).label("total")).group_by(
                Registration.country
            )
        ).all()
        for row in rows:
            counts[row.country] = row.total
        return counts

    def get_team_members(country):
        return (
            get_db()
            .execute(
                select(Registration)
                .where(Registration.country == country)
                .order_by(Registration.created_at.asc(), Registration.name.asc())
            )
            .scalars()
            .all()
        )

    def admin_required(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if not session.get("is_admin"):
                return redirect(url_for("admin_login"))
            return view(**kwargs)

        return wrapped_view

    @app.teardown_appcontext
    def teardown_db(error=None):
        close_db(error)

    with app.app_context():
        init_db()

    @app.context_processor
    def inject_site_data():
        photo_credits = [
            {
                "country": country,
                "spotlight": details["spotlight"],
                "source": details["image_source"],
                "credit": details["image_credit"],
            }
            for country, details in country_data.items()
        ]
        return {
            "organizer": ORGANIZER,
            "photo_credits": photo_credits,
        }

    @app.route("/")
    def index():
        return render_template(
            "index.html",
            country_data=country_data,
            country_counts=get_country_counts(),
        )

    @app.route("/health")
    def health():
        get_db().execute(select(1))
        return jsonify({"status": "ok"})

    @app.route("/register", methods=["POST"])
    def register():
        name = request.form.get("name", "").strip()
        country = request.form.get("country", "").strip()
        dish = request.form.get("dish", "").strip()

        if not name:
            flash("Please enter your name.", "error")
            return redirect(url_for("index"))
        if len(name) > 80:
            flash("Names should be 80 characters or less.", "error")
            return redirect(url_for("index"))
        if country not in COUNTRY_DISHES:
            flash("Please choose one of the listed countries.", "error")
            return redirect(url_for("index"))
        if dish not in COUNTRY_DISHES[country]:
            flash("Please choose a valid dish for your country.", "error")
            return redirect(url_for("index"))

        db = get_db()
        db.add(
            Registration(
                name=name,
                country=country,
                dish=dish,
            )
        )
        db.commit()

        session["team_country"] = country
        session["participant_name"] = name
        flash(f"You joined Team {country}. Coordinate with your teammates below.", "success")
        return redirect(url_for("team"))

    @app.route("/team")
    def team():
        country = session.get("team_country")
        if not country or country not in COUNTRY_DISHES:
            flash("Choose a country and register first.", "error")
            return redirect(url_for("index"))

        return render_template(
            "team.html",
            country=country,
            members=get_team_members(country),
            participant_name=session.get("participant_name"),
            dishes=COUNTRY_DISHES[country],
            country_meta=country_data[country],
        )

    @app.route("/api/countries/<country>/members")
    def country_members(country):
        if country not in COUNTRY_DISHES:
            return jsonify({"error": "Unknown country."}), 404

        members = get_team_members(country)
        return jsonify(
            {
                "country": country,
                "count": len(members),
                "dishes": COUNTRY_DISHES[country],
                "flag": country_data[country]["flag"],
                "image_url": country_data[country]["image_url"],
                "image_alt": country_data[country]["image_alt"],
                "spotlight": country_data[country]["spotlight"],
                "members": [
                    {"name": member.name, "dish": member.dish}
                    for member in members
                ],
            }
        )

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            password = request.form.get("password", "")
            if password == app.config["ADMIN_PASSWORD"]:
                session["is_admin"] = True
                return redirect(url_for("admin_dashboard"))
            flash("Incorrect organizer password.", "error")

        return render_template(
            "admin_login.html",
            using_default_password=app.config["ADMIN_PASSWORD"] == "change-me",
        )

    @app.route("/admin/logout")
    def admin_logout():
        session.pop("is_admin", None)
        flash("Organizer session closed.", "success")
        return redirect(url_for("index"))

    @app.route("/admin")
    @admin_required
    def admin_dashboard():
        registrations = (
            get_db()
            .execute(
                select(Registration).order_by(
                    Registration.country.asc(),
                    Registration.created_at.asc(),
                    Registration.name.asc(),
                )
            )
            .scalars()
            .all()
        )
        return render_template(
            "admin.html",
            registrations=registrations,
            country_counts=get_country_counts(),
        )

    @app.route("/admin/export.csv")
    @admin_required
    def admin_export():
        registrations = (
            get_db()
            .execute(
                select(Registration).order_by(
                    Registration.country.asc(),
                    Registration.created_at.asc(),
                    Registration.name.asc(),
                )
            )
            .scalars()
            .all()
        )

        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(["Name", "Country", "Dish", "Created At"])
        for row in registrations:
            writer.writerow(
                [
                    row.name,
                    row.country,
                    row.dish,
                    format_timestamp(row.created_at),
                ]
            )

        response = make_response(buffer.getvalue())
        response.headers["Content-Type"] = "text/csv; charset=utf-8"
        response.headers["Content-Disposition"] = "attachment; filename=registrations.csv"
        return response

    return app


app = create_app()


if __name__ == "__main__":
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", os.environ.get("FLASK_PORT", "5000")))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)
