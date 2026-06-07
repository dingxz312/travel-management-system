"""出差管理系统 · 后端入口。

启动方式（在 backend 目录下）：
    uvicorn main:app --reload
然后浏览器打开 http://127.0.0.1:8000/docs 就能看到所有接口并直接点着试。
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from database import init_db, get_session
from models import (
    User, TravelRequest, TravelRequestCreate, LoginInput, ApprovalInput,
    Role, Status,
)
from seed import seed_users


@asynccontextmanager
async def lifespan(app: FastAPI):
    """服务启动时做的准备：建表 + 灌入测试用户。"""
    init_db()
    seed_users()
    yield


app = FastAPI(title="出差管理系统 API", lifespan=lifespan)

# 状态的中文显示，用在提示信息里
STATUS_LABEL = {
    Status.pending: "待审批",
    Status.approved: "已通过",
    Status.rejected: "已驳回",
}


@app.get("/")
def health():
    """健康检查：能看到这句话，就说明后端活着。"""
    return {"message": "出差管理系统后端运行中"}


@app.post("/login")
def login(data: LoginInput, session: Session = Depends(get_session)):
    """登录：用户名 + 密码对得上，就返回这个人的信息。"""
    user = session.exec(select(User).where(User.username == data.username)).first()
    if not user or user.password != data.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    return {"id": user.id, "name": user.name, "role": user.role}


@app.post("/travel-requests", response_model=TravelRequest)
def create_travel_request(
    data: TravelRequestCreate, session: Session = Depends(get_session)
):
    """提交一条出差申请，存进数据库，状态默认“待审批”。"""
    request = TravelRequest(**data.model_dump())
    session.add(request)        # 放进“待提交”区
    session.commit()            # 真正写入数据库
    session.refresh(request)    # 取回数据库自动生成的 id、时间等
    return request


@app.get("/travel-requests", response_model=list[TravelRequest])
def list_travel_requests(
    status: Status | None = None,
    applicant_id: int | None = None,
    session: Session = Depends(get_session),
):
    """查看出差申请，可按状态或申请人过滤。

    - 不带参数：看全部
    - ?status=pending：主管看“待审批”待办
    - ?applicant_id=1：员工看自己提交的
    """
    query = select(TravelRequest)
    if status is not None:
        query = query.where(TravelRequest.status == status)
    if applicant_id is not None:
        query = query.where(TravelRequest.applicant_id == applicant_id)
    return session.exec(query).all()


@app.get("/travel-requests/{request_id}", response_model=TravelRequest)
def get_travel_request(request_id: int, session: Session = Depends(get_session)):
    """按 id 查看某一条出差申请。"""
    request = session.get(TravelRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="申请不存在")
    return request


def _decide(
    request_id: int, decision: Status, data: ApprovalInput, session: Session
) -> TravelRequest:
    """审批的共用逻辑：通过和驳回只差“最终落到哪个状态”。"""
    request = session.get(TravelRequest, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="申请不存在")

    # 权限校验：只有主管能审批
    approver = session.get(User, data.approver_id)
    if not approver or approver.role != Role.manager:
        raise HTTPException(status_code=403, detail="只有主管可以审批")

    # 状态机保护：只有“待审批”的申请能被审批，避免重复处理
    if request.status != Status.pending:
        raise HTTPException(
            status_code=400,
            detail=f"该申请当前是「{STATUS_LABEL[request.status]}」，不能重复审批",
        )

    request.status = decision
    request.approver_id = data.approver_id
    request.approval_comment = data.comment
    session.add(request)
    session.commit()
    session.refresh(request)
    return request


@app.post("/travel-requests/{request_id}/approve", response_model=TravelRequest)
def approve_travel_request(
    request_id: int, data: ApprovalInput, session: Session = Depends(get_session)
):
    """主管通过一条出差申请。"""
    return _decide(request_id, Status.approved, data, session)


@app.post("/travel-requests/{request_id}/reject", response_model=TravelRequest)
def reject_travel_request(
    request_id: int, data: ApprovalInput, session: Session = Depends(get_session)
):
    """主管驳回一条出差申请。"""
    return _decide(request_id, Status.rejected, data, session)


# 把 frontend 目录托管成网页：浏览器访问 http://127.0.0.1:8000/ui/ 就能打开界面。
# 页面和接口在同一个地址（同源），所以前端里的 fetch('/login') 直接就能调到上面的接口。
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
app.mount("/ui", StaticFiles(directory=FRONTEND_DIR, html=True), name="ui")
