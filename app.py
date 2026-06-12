from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

from database import db
from models import User, Category, Event, Registration

app = Flask(__name__)
app.secret_key = "greenmeet_secret_key_2026"


@app.before_request
def before_request():
    if db.is_closed():
        db.connect()


@app.teardown_request
def teardown_request(exception):
    if not db.is_closed():
        db.close()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Tens de iniciar sessão para aceder a esta página.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session or not session.get("is_admin"):
            flash("Acesso restrito ao administrador.")
            return redirect(url_for("home"))
        return f(*args, **kwargs)
    return decorated_function


def parse_event_datetime(value):
    return datetime.strptime(value, "%Y-%m-%dT%H:%M")


@app.route("/")
def home():
    featured_events = Event.select().order_by(Event.date_time).limit(3)
    return render_template("home.html", featured_events=featured_events)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not name or not email or not password:
            flash("Preenche todos os campos.")
            return redirect(url_for("register"))

        if User.select().where(User.email == email).exists():
            flash("Este email já está registado.")
            return redirect(url_for("register"))

        User.create(
            name=name,
            email=email,
            password=generate_password_hash(password),
            is_admin=False
        )

        flash("Registo concluído com sucesso. Podes iniciar sessão.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Preenche todos os campos.")
            return redirect(url_for("login"))

        user = User.get_or_none(User.email == email)

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["user_name"] = user.name
            session["is_admin"] = user.is_admin
            flash("Login efetuado com sucesso.")
            return redirect(url_for("home"))

        flash("Email ou password incorretos.")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sessão terminada.")
    return redirect(url_for("home"))


@app.route("/events")
def list_events():
    search = request.args.get("search", "").strip().lower()
    category = request.args.get("category", "").strip().lower()
    location = request.args.get("location", "").strip().lower()
    date = request.args.get("date", "").strip().lower()

    events = list(Event.select().join(Category).order_by(Event.date_time))

    filtered_events = []
    for event in events:
        matches_search = (
            search in event.title.lower() or
            search in event.short_description.lower()
        ) if search else True

        matches_category = category in event.category.name.lower() if category else True
        matches_location = location in event.location.lower() if location else True
        matches_date = date in event.date_time.strftime("%Y-%m-%d %H:%M").lower() if date else True

        if matches_search and matches_category and matches_location and matches_date:
            filtered_events.append(event)

    return render_template("events.html", events=filtered_events)


@app.route("/event/<int:event_id>")
def event_detail(event_id):
    event = Event.get_or_none(Event.id == event_id)

    if not event:
        return "Evento não encontrado", 404

    participants = Registration.select().where(Registration.event == event).count()

    registered = False
    if "user_id" in session:
        registered = Registration.select().where(
            (Registration.user == session["user_id"]) &
            (Registration.event == event)
        ).exists()

    return render_template(
        "event_detail.html",
        event=event,
        category_name=event.category.name,
        organizer_name=event.organizer.name,
        participants=participants,
        registered=registered
    )


@app.route("/join/<int:event_id>")
@login_required
def join_event(event_id):
    event = Event.get_or_none(Event.id == event_id)
    user = User.get_by_id(session["user_id"])

    if not event:
        flash("Evento não existe.")
        return redirect(url_for("list_events"))

    already_registered = Registration.get_or_none(
        (Registration.user == user) & (Registration.event == event)
    )

    if already_registered:
        flash("Já estás inscrito neste evento.")
    else:
        Registration.create(user=user, event=event)
        flash("Inscrição confirmada.")

    return redirect(url_for("event_detail", event_id=event.id))


@app.route("/cancel-registration/<int:event_id>")
@login_required
def cancel_registration(event_id):
    user = User.get_by_id(session["user_id"])
    event = Event.get_or_none(Event.id == event_id)

    if not event:
        flash("Evento não existe.")
        return redirect(url_for("my_events"))

    registration = Registration.get_or_none(
        (Registration.user == user) & (Registration.event == event)
    )

    if registration:
        registration.delete_instance()
        flash("Inscrição cancelada.")
    else:
        flash("Não estás inscrito neste evento.")

    return redirect(url_for("my_events"))


@app.route("/my-events")
@login_required
def my_events():
    user = User.get_by_id(session["user_id"])
    registrations = Registration.select().where(Registration.user == user)
    events = [registration.event for registration in registrations]
    return render_template("my_events.html", events=events)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = User.get_by_id(session["user_id"])

    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not name:
            flash("O nome não pode estar vazio.")
            return redirect(url_for("profile"))

        user.name = name
        user.save()
        session["user_name"] = user.name
        flash("Perfil atualizado com sucesso.")
        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)


@app.route("/admin")
@admin_required
def admin_dashboard():
    users_count = User.select().count()
    events_count = Event.select().count()
    categories_count = Category.select().count()
    registrations_count = Registration.select().count()
    events = Event.select().order_by(Event.date_time)

    return render_template(
        "admin_dashboard.html",
        users_count=users_count,
        events_count=events_count,
        categories_count=categories_count,
        registrations_count=registrations_count,
        events=events
    )


@app.route("/admin/events/create", methods=["GET", "POST"])
@admin_required
def admin_create_event():
    categories = Category.select().order_by(Category.name)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        short_description = request.form.get("short_description", "").strip()
        description = request.form.get("description", "").strip()
        date_time = request.form.get("date_time", "").strip()
        location = request.form.get("location", "").strip()
        category_id = request.form.get("category_id", "").strip()

        if not all([title, short_description, description, date_time, location, category_id]):
            flash("Preenche todos os campos.")
            return redirect(url_for("admin_create_event"))

        category = Category.get_or_none(Category.id == int(category_id))
        organizer = User.get_by_id(session["user_id"])

        Event.create(
            title=title,
            short_description=short_description,
            description=description,
            date_time=parse_event_datetime(date_time),
            location=location,
            category=category,
            organizer=organizer
        )

        flash("Evento criado com sucesso.")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_event_form.html", event=None, categories=categories)


@app.route("/admin/events/edit/<int:event_id>", methods=["GET", "POST"])
@admin_required
def admin_edit_event(event_id):
    event = Event.get_or_none(Event.id == event_id)
    categories = Category.select().order_by(Category.name)

    if not event:
        flash("Evento não encontrado.")
        return redirect(url_for("admin_dashboard"))

    if request.method == "POST":
        event.title = request.form.get("title", "").strip()
        event.short_description = request.form.get("short_description", "").strip()
        event.description = request.form.get("description", "").strip()
        event.date_time = parse_event_datetime(request.form.get("date_time", "").strip())
        event.location = request.form.get("location", "").strip()
        event.category = Category.get_by_id(int(request.form.get("category_id")))
        event.save()

        flash("Evento atualizado com sucesso.")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin_event_form.html", event=event, categories=categories)


@app.route("/admin/events/delete/<int:event_id>", methods=["POST"])
@admin_required
def admin_delete_event(event_id):
    event = Event.get_or_none(Event.id == event_id)

    if event:
        event.delete_instance(recursive=True)
        flash("Evento eliminado com sucesso.")
    else:
        flash("Evento não encontrado.")

    return redirect(url_for("admin_dashboard"))


@app.route("/admin/categories", methods=["GET", "POST"])
@admin_required
def admin_categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()

        if not name:
            flash("O nome da categoria não pode estar vazio.")
            return redirect(url_for("admin_categories"))

        if Category.select().where(Category.name == name).exists():
            flash("Essa categoria já existe.")
            return redirect(url_for("admin_categories"))

        Category.create(name=name)
        flash("Categoria criada com sucesso.")
        return redirect(url_for("admin_categories"))

    categories = Category.select().order_by(Category.name)
    return render_template("admin_categories.html", categories=categories)


@app.route("/admin/categories/delete/<int:category_id>", methods=["POST"])
@admin_required
def admin_delete_category(category_id):
    category = Category.get_or_none(Category.id == category_id)

    if not category:
        flash("Categoria não encontrada.")
        return redirect(url_for("admin_categories"))

    if Event.select().where(Event.category == category).exists():
        flash("Não podes apagar uma categoria que tem eventos associados.")
        return redirect(url_for("admin_categories"))

    category.delete_instance()
    flash("Categoria apagada com sucesso.")
    return redirect(url_for("admin_categories"))


@app.route("/admin/event/<int:event_id>/registrations")
@admin_required
def admin_event_registrations(event_id):
    event = Event.get_or_none(Event.id == event_id)

    if not event:
        flash("Evento não encontrado.")
        return redirect(url_for("admin_dashboard"))

    registrations = (
        Registration
        .select()
        .where(Registration.event == event)
        .order_by(Registration.registration_date)
    )

    return render_template("admin_registrations.html", event=event, registrations=registrations)


if __name__ == "__main__":
    app.run(debug=True)