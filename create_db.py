from datetime import datetime
from werkzeug.security import generate_password_hash

from database import db
from models import User, Category, Event, Registration


def create_tables():
    db.connect(reuse_if_open=True)
    db.create_tables([User, Category, Event, Registration])


def seed_database():
    admin_user, _ = User.get_or_create(
        email="admin@app.com",
        defaults={
            "name": "Admin Supremo",
            "password": generate_password_hash("admin123"),
            "is_admin": True
        }
    )

    normal_user, _ = User.get_or_create(
        email="teste@email.com",
        defaults={
            "name": "João Utilizador",
            "password": generate_password_hash("teste123"),
            "is_admin": False
        }
    )

    prof_user, _ = User.get_or_create(
        email="prof@app.com",
        defaults={
            "name": "Professor Xavier",
            "password": generate_password_hash("prof123"),
            "is_admin": False
        }
    )

    cat_educacao, _ = Category.get_or_create(name="Educação")
    cat_desporto, _ = Category.get_or_create(name="Desporto")
    cat_musica, _ = Category.get_or_create(name="Música")
    cat_networking, _ = Category.get_or_create(name="Networking")
    cat_bemestar, _ = Category.get_or_create(name="Bem-Estar")

    event_python, _ = Event.get_or_create(
        title="Workshop de Python",
        defaults={
            "description": "Aprende Flask do zero neste workshop intensivo para iniciantes.",
            "short_description": "Workshop prático de web development.",
            "date_time": datetime(2026, 5, 20, 14, 0),
            "location": "Sala 1.1",
            "category": cat_educacao,
            "organizer": prof_user
        }
    )

    event_tennis, _ = Event.get_or_create(
        title="Torneio de Ténis",
        defaults={
            "description": "Torneio amigável para vários níveis, com jogos em formato eliminatório.",
            "short_description": "Vem jogar ténis connosco.",
            "date_time": datetime(2026, 6, 15, 9, 0),
            "location": "University Tennis Club",
            "category": cat_desporto,
            "organizer": admin_user
        }
    )

    event_boat, _ = Event.get_or_create(
        title="Boat Trip Experience",
        defaults={
            "description": "Passeio de barco em grupo com música e outdoor activities.",
            "short_description": "Boat trip com sunset vibes.",
            "date_time": datetime(2026, 6, 8, 10, 0),
            "location": "Tagus Marina",
            "category": cat_bemestar,
            "organizer": admin_user
        }
    )

    Event.get_or_create(
        title="Summer Concert",
        defaults={
            "description": "Concerto ao ar livre com bandas locais para celebrar o fim do semestre.",
            "short_description": "Música ao vivo ao ar livre.",
            "date_time": datetime(2026, 7, 1, 21, 0),
            "location": "Main Garden",
            "category": cat_musica,
            "organizer": admin_user
        }
    )

    Event.get_or_create(
        title="Startup Meetup",
        defaults={
            "description": "Networking event para estudantes interessados em empreendedorismo.",
            "short_description": "Networking com founders e estudantes.",
            "date_time": datetime(2026, 6, 3, 18, 30),
            "location": "Innovation Room",
            "category": cat_networking,
            "organizer": admin_user
        }
    )

    Event.get_or_create(
        title="Yoga in the Park",
        defaults={
            "description": "Sessão de yoga de manhã ao ar livre aberta a todos.",
            "short_description": "Outdoor yoga para relaxar.",
            "date_time": datetime(2026, 6, 8, 8, 0),
            "location": "Riverside Park",
            "category": cat_bemestar,
            "organizer": admin_user
        }
    )

    Registration.get_or_create(user=normal_user, event=event_python)
    Registration.get_or_create(user=normal_user, event=event_tennis)
    Registration.get_or_create(user=normal_user, event=event_boat)


if __name__ == "__main__":
    create_tables()
    seed_database()
    print("Base de dados criada e populada com sucesso.")