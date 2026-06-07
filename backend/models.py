"""数据模型 = 数据库里的“表”长什么样 + 接口收发数据的“格式”。

SQLModel 的好处：一个 Python 类同时定义了「数据库表结构」和「接口数据格式」，
不用写两遍。带 table=True 的类会真正变成数据库里的一张表。
"""
from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field


class Role(str, Enum):
    """角色：员工 或 主管。"""
    employee = "employee"   # 员工：提交出差申请
    manager = "manager"     # 主管：审批申请


class Status(str, Enum):
    """出差申请的状态 —— 这就是“审批状态机”的几个状态。"""
    pending = "pending"     # 待审批
    approved = "approved"   # 已通过
    rejected = "rejected"   # 已驳回


class User(SQLModel, table=True):
    """用户表：员工和主管都存这张表，用 role 区分身份。"""
    id: Optional[int] = Field(default=None, primary_key=True)   # 主键：每条记录的唯一编号
    username: str = Field(index=True, unique=True)              # 登录用的账号，不能重复
    password: str                                              # 教学项目先存明文，后面会讲为什么真实项目要加密
    name: str                                                  # 姓名
    role: Role = Role.employee                                 # 默认是员工


class TravelRequest(SQLModel, table=True):
    """出差申请表：一条记录 = 一次出差申请。"""
    id: Optional[int] = Field(default=None, primary_key=True)
    applicant_id: int = Field(foreign_key="user.id")           # 申请人，指向 user 表的某个 id（外键）
    destination: str                                          # 目的地
    start_date: date                                          # 出差开始日期
    end_date: date                                            # 出差结束日期
    reason: str                                               # 出差事由
    estimated_cost: float                                     # 预估费用
    status: Status = Status.pending                           # 新建时默认“待审批”
    approver_id: Optional[int] = Field(default=None, foreign_key="user.id")  # 审批人（W2 用）
    approval_comment: Optional[str] = None                    # 审批意见（W2 用）
    created_at: datetime = Field(default_factory=datetime.now)  # 提交时间，自动记录


# ---- 下面这两个不是数据库表，只是“接口的输入格式” ----

class TravelRequestCreate(SQLModel):
    """提交出差申请时，前端需要传的字段（不含 id、状态、时间，这些由后端生成）。"""
    applicant_id: int
    destination: str
    start_date: date
    end_date: date
    reason: str
    estimated_cost: float


class LoginInput(SQLModel):
    """登录接口的输入。"""
    username: str
    password: str


class ApprovalInput(SQLModel):
    """审批接口的输入：谁来审 + 审批意见。"""
    approver_id: int
    comment: Optional[str] = None
