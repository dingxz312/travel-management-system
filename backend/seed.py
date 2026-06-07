"""灌入几个测试用户，方便登录和提交申请时直接用。

真实项目里用户是注册或后台导入的；这里为了能马上演示，预置 3 个账号。
"""
from sqlmodel import Session, select

from database import engine
from models import User, Role


def seed_users() -> None:
    with Session(engine) as session:
        # 已经有用户了就不重复灌
        if session.exec(select(User)).first():
            return
        users = [
            User(username="zhangsan", password="123456", name="张三", role=Role.employee),
            User(username="lisi", password="123456", name="李四", role=Role.employee),
            User(username="manager", password="123456", name="王经理", role=Role.manager),
        ]
        for u in users:
            session.add(u)
        session.commit()
