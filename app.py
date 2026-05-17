import os
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import IntegerField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional

from models import Activity, ActivitySignup, Announcement, User, Zone, db

SOCIAL_MODES = [
    "Open to conversation",
    "Focused but approachable",
    "Looking for activity",
    "New here",
    "Quiet mode",
]


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "presence-house-dev-key")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///presence_house.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["FORMSPREE_ENDPOINT"] = os.environ.get("FORMSPREE_ENDPOINT", "").strip()

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "login"
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()
        seed_data()

    register_routes(app)
    return app


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash("Admin access required.", "warning")
            return redirect(url_for("dashboard"))
        return func(*args, **kwargs)

    return wrapper


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    interests = TextAreaField("Interests", validators=[Optional(), Length(max=500)])
    social_mode = SelectField("Preferred social mode", choices=[(m, m) for m in SOCIAL_MODES])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=120)])
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class ActivityForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=150)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(max=800)])
    zone = StringField("Zone", validators=[DataRequired(), Length(max=100)])
    start_time = StringField("Start (YYYY-MM-DD HH:MM)", validators=[DataRequired()])
    end_time = StringField("End (YYYY-MM-DD HH:MM)", validators=[DataRequired()])
    capacity = IntegerField("Capacity", validators=[DataRequired(), NumberRange(min=1, max=200)])
    status = SelectField("Status", choices=[("Open", "Open"), ("Filling", "Filling"), ("Full", "Full")])
    activity_type = StringField("Activity type", validators=[DataRequired(), Length(max=80)])
    submit = SubmitField("Create activity")


class AnnouncementForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=180)])
    body = TextAreaField("Body", validators=[DataRequired(), Length(max=600)])
    submit = SubmitField("Post announcement")


def parse_dt(value: str):
    return datetime.strptime(value, "%Y-%m-%d %H:%M")


def register_routes(app: Flask):
    @app.route("/")
    def index():
        return render_template("index.html", formspree_endpoint=app.config["FORMSPREE_ENDPOINT"])

    @app.route("/founding-list", methods=["POST"])
    def founding_list():
        if app.config["FORMSPREE_ENDPOINT"]:
            flash("Your form should submit directly to Formspree. Thanks for supporting Presence House.", "success")
        else:
            flash("Thanks! No Formspree endpoint configured, so this local demo captured your interest.", "success")
        return redirect(url_for("index") + "#founding-list")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        form = RegisterForm()
        if form.validate_on_submit():
            if User.query.filter_by(email=form.email.data.lower().strip()).first():
                flash("Email already registered.", "danger")
                return render_template("register.html", form=form)
            user = User(
                name=form.name.data.strip(),
                email=form.email.data.lower().strip(),
                interests=form.interests.data.strip(),
                social_mode=form.social_mode.data,
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash("Account created. Welcome to Presence House.", "success")
            return redirect(url_for("login"))
        return render_template("register.html", form=form)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data.lower().strip()).first()
            if not user or not user.check_password(form.password.data):
                flash("Invalid email or password.", "danger")
                return render_template("login.html", form=form)
            login_user(user)
            flash("Welcome back. The app exists to help you return to the room.", "success")
            return redirect(url_for("dashboard"))
        return render_template("login.html", form=form)

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("Logged out.", "info")
        return redirect(url_for("index"))

    @app.route("/dashboard", methods=["GET", "POST"])
    @login_required
    def dashboard():
        if request.method == "POST":
            mode = request.form.get("social_mode", "")
            if mode in SOCIAL_MODES:
                current_user.social_mode = mode
                db.session.commit()
                flash("Social mode updated.", "success")
        activities = Activity.query.order_by(Activity.start_time.asc()).all()
        zones = Zone.query.order_by(Zone.name.asc()).all()
        announcements = Announcement.query.filter_by(active=True).order_by(Announcement.created_at.desc()).all()
        my_signups = {s.activity_id for s in current_user.signups}
        return render_template("dashboard.html", activities=activities, zones=zones, announcements=announcements, my_signups=my_signups, social_modes=SOCIAL_MODES)

    @app.route("/activity/<int:activity_id>")
    @login_required
    def activity_detail(activity_id):
        activity = Activity.query.get_or_404(activity_id)
        attendee_names = [s.user.first_name for s in activity.signups]
        joined = any(s.user_id == current_user.id for s in activity.signups)
        return render_template("activity_detail.html", activity=activity, attendee_names=attendee_names, joined=joined)

    @app.post("/activity/<int:activity_id>/join")
    @login_required
    def join_activity(activity_id):
        activity = Activity.query.get_or_404(activity_id)
        existing = ActivitySignup.query.filter_by(user_id=current_user.id, activity_id=activity.id).first()
        if existing:
            flash("You are already in this activity.", "info")
        elif activity.seats_open <= 0:
            flash("No seats open right now.", "warning")
        else:
            db.session.add(ActivitySignup(user_id=current_user.id, activity_id=activity.id))
            db.session.commit()
            flash("Joined activity.", "success")
        return redirect(url_for("activity_detail", activity_id=activity.id))

    @app.post("/activity/<int:activity_id>/leave")
    @login_required
    def leave_activity(activity_id):
        signup = ActivitySignup.query.filter_by(user_id=current_user.id, activity_id=activity_id).first_or_404()
        db.session.delete(signup)
        db.session.commit()
        flash("You left the activity.", "info")
        return redirect(url_for("activity_detail", activity_id=activity_id))

    @app.route("/admin", methods=["GET", "POST"])
    @login_required
    @admin_required
    def admin():
        activity_form = ActivityForm(prefix="activity")
        ann_form = AnnouncementForm(prefix="announce")

        if activity_form.validate_on_submit() and activity_form.submit.data:
            try:
                activity = Activity(
                    title=activity_form.title.data,
                    description=activity_form.description.data,
                    zone=activity_form.zone.data,
                    start_time=parse_dt(activity_form.start_time.data.strip()),
                    end_time=parse_dt(activity_form.end_time.data.strip()),
                    capacity=activity_form.capacity.data,
                    status=activity_form.status.data,
                    activity_type=activity_form.activity_type.data,
                )
                db.session.add(activity)
                db.session.commit()
                flash("Activity created.", "success")
                return redirect(url_for("admin"))
            except ValueError:
                flash("Use date format YYYY-MM-DD HH:MM", "danger")

        if ann_form.validate_on_submit() and ann_form.submit.data:
            db.session.add(Announcement(title=ann_form.title.data, body=ann_form.body.data))
            db.session.commit()
            flash("Announcement posted.", "success")
            return redirect(url_for("admin"))

        if request.method == "POST" and request.form.get("action") == "update_activity_status":
            activity = Activity.query.get_or_404(int(request.form.get("activity_id")))
            activity.status = request.form.get("status", activity.status)
            db.session.commit()
            flash("Activity status updated.", "success")

        if request.method == "POST" and request.form.get("action") == "update_zone":
            zone = Zone.query.get_or_404(int(request.form.get("zone_id")))
            zone.vibe = request.form.get("vibe", zone.vibe)
            zone.occupancy = request.form.get("occupancy", zone.occupancy)
            db.session.commit()
            flash("Zone updated.", "success")

        return render_template("admin.html", activity_form=activity_form, ann_form=ann_form, activities=Activity.query.all(), zones=Zone.query.all())

    @app.route("/health")
    def health():
        return "OK", 200

    @app.errorhandler(404)
    def not_found(_):
        return render_template("404.html"), 404


def seed_data():
    if not User.query.filter_by(email="admin@presencehouse.club").first():
        admin = User(name="Presence Admin", email="admin@presencehouse.club", interests="Community", social_mode="Open to conversation", is_admin=True)
        admin.set_password("presence123")
        db.session.add(admin)

    if Zone.query.count() == 0:
        zones = [
            Zone(name="Quiet Lounge", description="Calm reading and reflection", vibe="Soft-spoken, reflective", occupancy="Light", phone_expectation="Silent and tucked away"),
            Zone(name="Social Commons", description="Conversation-friendly central room", vibe="Warm and social", occupancy="Moderate", phone_expectation="Quick checks only"),
            Zone(name="Focus Rooms", description="Heads-down work corners", vibe="Quiet concentration", occupancy="Steady", phone_expectation="No calls"),
            Zone(name="Activity Hall", description="Group activity and workshop space", vibe="Lively with structure", occupancy="Busy", phone_expectation="Away during sessions"),
            Zone(name="Café & Bar", description="Tea, coffee, and intentional chats", vibe="Gentle hum", occupancy="Moderate", phone_expectation="Use briefly between conversations"),
            Zone(name="Outdoor Space", description="Fresh air and walking loops", vibe="Restorative", occupancy="Open", phone_expectation="Minimal"),
        ]
        db.session.add_all(zones)

    if Activity.query.count() == 0:
        now = datetime.now().replace(second=0, microsecond=0)
        samples = [
            ("Silent Reading Lounge", "Bring a book and share quiet company.", "Quiet Lounge", 0, 90, 18, "Open", "Reflection"),
            ("Open Conversation Table", "Meet someone new over guided prompts.", "Social Commons", 30, 90, 10, "Open", "Social"),
            ("Chess & Strategy Night", "Analog strategy and friendly matches.", "Activity Hall", 120, 180, 16, "Filling", "Games"),
            ("Community Dinner", "Long table dinner with intentional conversation.", "Café & Bar", 240, 120, 22, "Filling", "Dining"),
            ("Deep Work Session", "Focused sprint with light accountability.", "Focus Rooms", 60, 120, 12, "Open", "Work"),
            ("Analog Creative Hour", "Sketching, journaling, and collage.", "Outdoor Space", 150, 90, 14, "Open", "Creative"),
            ("Philosophy Circle", "Slow dialogue around one timeless question.", "Quiet Lounge", 300, 90, 10, "Open", "Discussion"),
            ("Phone-Light Social Hour", "Easy social time with phones tucked away.", "Social Commons", 360, 90, 20, "Open", "Social"),
        ]
        for title, desc, zone, offset, dur, cap, status, a_type in samples:
            start = now + timedelta(minutes=offset)
            db.session.add(Activity(title=title, description=desc, zone=zone, start_time=start, end_time=start + timedelta(minutes=dur), capacity=cap, status=status, activity_type=a_type))

    if Announcement.query.count() == 0:
        db.session.add_all([
            Announcement(title="Welcome to Presence House", body="Welcome to Presence House—this app exists to help you return to the room."),
            Announcement(title="Phone guidance", body="Phones stay tucked away during activities unless otherwise noted."),
            Announcement(title="Tonight's dinner", body="Community dinner starts at 7:30 PM in Café & Bar."),
            Announcement(title="New member tip", body="New members can begin at the Open Conversation Table."),
        ])

    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
