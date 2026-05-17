from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    interests = db.Column(db.Text, default="")
    social_mode = db.Column(db.String(60), default="Open to conversation")
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    signups = db.relationship("ActivitySignup", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def first_name(self) -> str:
        return self.name.split()[0] if self.name else "Member"


class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    zone = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    capacity = db.Column(db.Integer, nullable=False, default=12)
    status = db.Column(db.String(50), nullable=False, default="Open")
    activity_type = db.Column(db.String(80), nullable=False, default="Community")

    signups = db.relationship("ActivitySignup", back_populates="activity", cascade="all, delete-orphan")

    @property
    def attendee_count(self) -> int:
        return len(self.signups)

    @property
    def seats_open(self) -> int:
        return max(self.capacity - self.attendee_count, 0)


class ActivitySignup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="signups")
    activity = db.relationship("Activity", back_populates="signups")

    __table_args__ = (db.UniqueConstraint("user_id", "activity_id", name="uq_user_activity"),)


class Zone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    vibe = db.Column(db.String(120), nullable=False)
    occupancy = db.Column(db.String(50), nullable=False)
    phone_expectation = db.Column(db.String(150), nullable=False)


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
