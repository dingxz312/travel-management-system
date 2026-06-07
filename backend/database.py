"""数据库连接与初始化。

SQLite 数据库就是一个本地文件 travel.db —— 没有额外的数据库服务器，
一个文件就装下了所有数据，最适合用来理解“数据是怎么存的”。
"""
import os

from sqlmodel import SQLModel, create_engine, Session

# 把 travel.db 固定放在本文件所在的 backend 目录，
# 这样不管从哪里启动，数据库文件位置都一致。
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_FILE = os.path.join(BASE_DIR, "travel.db")

# engine（引擎）= 程序连接数据库的“通道”，整个应用共用这一个。
engine = create_engine(f"sqlite:///{SQLITE_FILE}", echo=False)


def init_db() -> None:
    """按 models.py 里定义的表结构，在数据库里建表（已存在则跳过）。"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """每次请求拿一个数据库会话（session），用完自动关闭。

    session = 一次“和数据库打交道”的对话，增删改查都通过它。
    """
    with Session(engine) as session:
        yield session
