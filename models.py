from peewee import (
    Model,
    AutoField,
    CharField,
    BooleanField,
    ForeignKeyField,
    DateTimeField,
    TextField
)
from datetime import datetime
from database import db


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    id = AutoField()
    name = CharField(max_length=100)
    email = CharField(unique=True, max_length=150)
    password = CharField(max_length=255)
    is_admin = BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.email})"


class Category(BaseModel):
    id = AutoField()
    name = CharField(unique=True, max_length=100)

    def __str__(self):
        return self.name


class Event(BaseModel):
    id = AutoField()
    title = CharField(max_length=150)
    description = TextField()
    short_description = CharField(max_length=255)
    date_time = DateTimeField()
    location = CharField(max_length=150)
    category = ForeignKeyField(Category, backref="events", on_delete="CASCADE")
    organizer = ForeignKeyField(User, backref="organized_events", on_delete="CASCADE")

    def __str__(self):
        return self.title


class Registration(BaseModel):
    id = AutoField()
    user = ForeignKeyField(User, backref="registrations", on_delete="CASCADE")
    event = ForeignKeyField(Event, backref="registrations", on_delete="CASCADE")
    registration_date = DateTimeField(default=datetime.now)

    class Meta:
        indexes = (
            (("user", "event"), True),
        )

    def __str__(self):
        return f"{self.user.name} -> {self.event.title}"