import csv
import io
import os
from datetime import datetime
from functools import wraps
from urllib.parse import quote

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
from sqlalchemy import DateTime, Integer, String, create_engine, delete, func, select
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
        "flag_url": "https://flagcdn.com/ke.svg",
        "flag_alt": "Flag of Kenya",
        "spotlight": "Nyama Choma",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Nyama%20Choma.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Nyama_Choma.jpg",
        "image_credit": "Samuel Kiongo / Wikimedia Commons",
        "image_alt": "Nyama choma grilling over charcoal",
    },
    "Germany": {
        "flag_url": "https://flagcdn.com/de.svg",
        "flag_alt": "Flag of Germany",
        "spotlight": "Schnitzel",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Iranian%20schnitzel.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Iranian_schnitzel.jpg",
        "image_credit": "Guywithacoolname / Wikimedia Commons",
        "image_alt": "Schnitzel served with fries and lemon",
    },
    "Uganda": {
        "flag_url": "https://flagcdn.com/ug.svg",
        "flag_alt": "Flag of Uganda",
        "spotlight": "Luwombo",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Traditional%20Ugandan%20Luwombo.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Traditional_Ugandan_Luwombo.jpg",
        "image_credit": "Nabunje Leticia / Wikimedia Commons",
        "image_alt": "Traditional Ugandan luwombo wrapped in banana leaves",
    },
    "Nigeria": {
        "flag_url": "https://flagcdn.com/ng.svg",
        "flag_alt": "Flag of Nigeria",
        "spotlight": "Jollof Rice",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Jollof%20Rice.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Jollof_Rice.jpg",
        "image_credit": "ChukaMadu / Wikimedia Commons",
        "image_alt": "A plate of Nigerian jollof rice",
    },
    "Cameroon": {
        "flag_url": "https://flagcdn.com/cm.svg",
        "flag_alt": "Flag of Cameroon",
        "spotlight": "Poulet DG",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Poulet%20DG.JPG",
        "image_source": "https://commons.wikimedia.org/wiki/File:Poulet_DG.JPG",
        "image_credit": "Affirebecca / Wikimedia Commons",
        "image_alt": "Cameroonian poulet DG with plantain",
    },
    "Zimbabwe": {
        "flag_url": "https://flagcdn.com/zw.svg",
        "flag_alt": "Flag of Zimbabwe",
        "spotlight": "Sadza with Beef Stew",
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/A%20plate%20of%20sadza.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:A_plate_of_sadza.jpg",
        "image_credit": "Tafadzwa Albert Mappurisa / Wikimedia Commons",
        "image_alt": "A plate of Zimbabwean sadza with meat and vegetables",
    },
}

DISH_DETAILS = {
    "Nyama Choma": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Nyama%20Choma.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Nyama_Choma.jpg",
        "image_credit": "Samuel Kiongo / Wikimedia Commons",
        "image_alt": "Nyama choma grilling over charcoal",
    },
    "Githeri": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Githeri.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Githeri.jpg",
        "image_credit": "Mukuba / Wikimedia Commons",
        "image_alt": "A bowl of Kenyan githeri made from maize and beans",
    },
    "Sukuma Wiki": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Sukuma%20wiki.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Sukuma_wiki.jpg",
        "image_credit": "Valerie Aloo / Wikimedia Commons",
        "image_alt": "Sukuma wiki leafy greens prepared for cooking",
    },
    "Mukimo": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Mukimo%20mix.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Mukimo_mix.jpg",
        "image_credit": "Jaymuiaphotography / Wikimedia Commons",
        "image_alt": "Mukimo, a mashed Kenyan potato and greens dish",
    },
    "Kenyan Pilau": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Food%20Kenya%20Pilau.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Food_Kenya_Pilau.jpg",
        "image_credit": "Cmwaura / Wikimedia Commons",
        "image_alt": "Kenyan pilau rice with meat",
    },
    "Sauerbraten": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Sauerbraten.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Sauerbraten.jpg",
        "image_credit": "Johann H. Addicks / Wikimedia Commons",
        "image_alt": "A plated serving of German sauerbraten",
    },
    "Schnitzel": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Schnitzel.JPG",
        "image_source": "https://commons.wikimedia.org/wiki/File:Schnitzel.JPG",
        "image_credit": "Eikus89 / Wikimedia Commons",
        "image_alt": "Schnitzel served with fries and lemon",
    },
    "Kaesespaetzle": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/K%C3%A4sesp%C3%A4tzle.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:K%C3%A4sesp%C3%A4tzle.jpg",
        "image_credit": "Wiki der Wikinger / Wikimedia Commons",
        "image_alt": "Kasespaetzle with onions and salad",
    },
    "Bratwurst and Sauerkraut": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Bratwurst.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Bratwurst.jpg",
        "image_credit": "Wikimedia Commons",
        "image_alt": "Bratwurst served with cabbage and potatoes",
    },
    "Kartoffelpuffer": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Kartoffelpuffer.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Kartoffelpuffer.jpg",
        "image_credit": "Clemens Pfeiffer / Wikimedia Commons",
        "image_alt": "Kartoffelpuffer potato pancakes",
    },
    "Luwombo": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Traditional%20Ugandan%20Luwombo.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Traditional_Ugandan_Luwombo.jpg",
        "image_credit": "Nabunje Leticia / Wikimedia Commons",
        "image_alt": "Traditional Ugandan luwombo wrapped in banana leaves",
    },
    "Rolex": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/ROLEX2.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:ROLEX2.jpg",
        "image_credit": "Wikimedia Commons",
        "image_alt": "Ugandan rolex street food wrapped in chapati",
    },
    "Matoke": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Matoke.JPG",
        "image_source": "https://commons.wikimedia.org/wiki/File:Matoke.JPG",
        "image_credit": "Wikistallion / Wikimedia Commons",
        "image_alt": "Matoke cooking bananas ready to be served",
    },
    "Groundnut Stew": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Groundnut%20Soup.JPG",
        "image_source": "https://commons.wikimedia.org/wiki/File:Groundnut_Soup.JPG",
        "image_credit": "Blackmapapa / Wikimedia Commons",
        "image_alt": "Groundnut stew in a bowl",
    },
    "Posho and Beans": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Africa%20ugali%20and%20beans.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Africa_ugali_and_beans.jpg",
        "image_credit": "Moseslukyamuzi / Wikimedia Commons",
        "image_alt": "Posho and beans served on a plate",
    },
    "Jollof Rice": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/JOLLOF%20RICE.JPG",
        "image_source": "https://commons.wikimedia.org/wiki/File:JOLLOF_RICE.JPG",
        "image_credit": "Ask4ugo / Wikimedia Commons",
        "image_alt": "A plate of Nigerian jollof rice",
    },
    "Egusi Soup": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Egusi%20Soup.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Egusi_Soup.jpg",
        "image_credit": "AkinkuotuFunmi / Wikimedia Commons",
        "image_alt": "Egusi soup in a serving bowl",
    },
    "Suya": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Suya.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Suya.jpg",
        "image_credit": "olaoluwapemi ogunmola / Wikimedia Commons",
        "image_alt": "Nigerian suya grilled meat",
    },
    "Pounded Yam and Ogbono Soup": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Ogbono%20Soup.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Ogbono_Soup.jpg",
        "image_credit": "Aderiqueza / Wikimedia Commons",
        "image_alt": "Ogbono soup served as a Nigerian swallow dish accompaniment",
    },
    "Moi Moi": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Moi%20moi.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Moi_moi.jpg",
        "image_credit": "Daniel Paullll / Wikimedia Commons",
        "image_alt": "Moi moi steamed bean pudding",
    },
    "Ndole": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/PLAT%20DE%20NDOLE.png",
        "image_source": "https://commons.wikimedia.org/wiki/File:PLAT_DE_NDOLE.png",
        "image_credit": "Destiny DEFFO / Wikimedia Commons",
        "image_alt": "A Cameroonian plate of ndole",
    },
    "Eru": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Eru%20Soup.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Eru_Soup.jpg",
        "image_credit": "Aderiqueza / Wikimedia Commons",
        "image_alt": "Eru soup from Cameroon",
    },
    "Koki Beans": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Koki%20Beans.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Koki_Beans.jpg",
        "image_credit": "Adesolive / Wikimedia Commons",
        "image_alt": "Cameroonian koki beans with plantain",
    },
    "Poulet DG": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Poulet%20DG.JPG",
        "image_source": "https://commons.wikimedia.org/wiki/File:Poulet_DG.JPG",
        "image_credit": "Affirebecca / Wikimedia Commons",
        "image_alt": "Cameroonian poulet DG with plantain",
    },
    "Achu Soup": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Achu%20meal.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Achu_meal.jpg",
        "image_credit": "Adesolive / Wikimedia Commons",
        "image_alt": "Achu with yellow soup from Cameroon",
    },
    "Sadza with Beef Stew": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/White%20sadza%20and%20beef%20stew.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:White_sadza_and_beef_stew.jpg",
        "image_credit": "Shark2025 / Wikimedia Commons",
        "image_alt": "White sadza served with beef stew",
    },
    "Dovi": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Peanut%20butter%20%28dovi%29.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Peanut_butter_(dovi).jpg",
        "image_credit": "Shark2025 / Wikimedia Commons",
        "image_alt": "Peanut butter prepared for dovi in Zimbabwe",
    },
    "Mazondo": {
        "image_url": "https://commons.wikimedia.org/wiki/Special:FilePath/Cow%27s%20trotters%20%28mazondo%29.jpg",
        "image_source": "https://commons.wikimedia.org/wiki/File:Cow%27s_trotters_(mazondo).jpg",
        "image_credit": "Solly Wolf / Wikimedia Commons",
        "image_alt": "Cow's trotters prepared for mazondo",
    },
}

ORGANIZER = {
    "name": "Campus Connect Vibes Team",
    "strapline": "Campus Connect cultural cookout host",
    "message": "Bringing students together to share food, stories, and culture in a friendly cookout.",
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


def build_qr_code_url(share_url):
    return (
        "https://api.qrserver.com/v1/create-qr-code/"
        f"?size=280x280&format=svg&data={quote(share_url, safe='')}"
    )


def build_dish_card(country, dish):
    country_details = COUNTRY_DETAILS[country]
    dish_details = DISH_DETAILS.get(dish, {})
    return {
        "name": dish,
        "image_url": dish_details.get("image_url", country_details["image_url"]),
        "image_alt": dish_details.get("image_alt", f"{dish} from {country}"),
        "fallback_image_url": country_details["image_url"],
        "fallback_image_alt": country_details["image_alt"],
    }


def build_country_data():
    return {
        country: {
            **COUNTRY_DETAILS[country],
            "dishes": [build_dish_card(country, dish) for dish in dishes],
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
        share_url = url_for("index", _external=True)
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
            "site_title": "Taste the World Cookout",
            "share_url": share_url,
            "qr_code_url": build_qr_code_url(share_url),
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
        flash(f"You joined Team {country}. Coordinate with your teammates for the cookout below.", "success")
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
                "flag_url": country_data[country]["flag_url"],
                "flag_alt": country_data[country]["flag_alt"],
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

    @app.route("/admin/delete/<int:registration_id>", methods=["POST"])
    @admin_required
    def admin_delete_registration(registration_id):
        db = get_db()
        registration = db.get(Registration, registration_id)

        if registration is None:
            flash("That registration entry no longer exists.", "error")
            return redirect(url_for("admin_dashboard"))

        deleted_name = registration.name
        deleted_country = registration.country
        db.delete(registration)
        db.commit()
        flash(f"Deleted {deleted_name} from Team {deleted_country}.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/clear", methods=["POST"])
    @admin_required
    def admin_clear_registrations():
        db = get_db()
        result = db.execute(delete(Registration))
        db.commit()
        deleted_total = result.rowcount or 0

        if deleted_total == 0:
            flash("There were no registrations to delete.", "error")
        else:
            flash(f"Deleted all {deleted_total} registration entries.", "success")
        return redirect(url_for("admin_dashboard"))

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
