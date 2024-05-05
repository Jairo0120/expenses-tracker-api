from api import config
from api.models import Cycle, User
from sqlmodel import Session, create_engine, select, update
from datetime import date, datetime
from api import utils


db_session = None


def get_session():
    global db_session
    if db_session:
        return db_session
    sqlite_url = f"sqlite:///{config.Settings().sqlite_database_url}"
    connect_args = {"check_same_thread": False}
    engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)
    with Session(engine) as session:
        db_session = session
        return db_session


def create_cycles():
    """
    Function that iterates over all  the active users and start creating new
    cycles (if necessary) and disable old cycles
    """
    session = get_session()
    statement = select(User).where(User.is_active == 1)
    for user in session.exec(statement).all():
        current_cycle = session.exec(
            select(Cycle)
            .where(Cycle.user_id == user.id)
            .where(Cycle.end_date >= datetime.now())
        ).first()
        if current_cycle:
            continue
        cycle = Cycle(
            description=datetime.now().strftime('%B, %Y'),
            start_date=utils.get_first_day_month(date.today()),
            end_date=utils.get_last_day_month(date.today()),
            user_id=user.id or 0
        )
        session.exec(
            update(Cycle)
            .where(Cycle.user_id == user.id)
            .where(Cycle.is_active == 1)
            .values(is_active=0)
        )
        session.add(cycle)
        session.commit()


if __name__ == '__main__':
    create_cycles()
