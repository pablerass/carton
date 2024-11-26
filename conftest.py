import pytest

from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from carton.models import *

@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        # "sqlite:///test.db",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=True
    )
    SQLModel.metadata.create_all(engine, )

    with Session(engine) as session:
        yield session
