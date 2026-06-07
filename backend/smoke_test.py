"""快速自检：不启动服务器，在内存里把「出差申请 + 审批」整条流程跑一遍。

跑法（在 backend 目录下）：
    python smoke_test.py
"""
from fastapi.testclient import TestClient

from main import app

# 用 with 包起来，FastAPI 的启动逻辑（建表 + 灌测试用户）才会真正执行。
with TestClient(app) as client:
    print("===== W1：登录 + 提交申请 =====")
    print("① 健康检查：", client.get("/").json())

    r = client.post("/login", json={"username": "zhangsan", "password": "123456"})
    print("② 张三登录：", r.status_code, r.json())

    new_req = {
        "applicant_id": 1, "destination": "上海",
        "start_date": "2026-06-10", "end_date": "2026-06-12",
        "reason": "拜访客户", "estimated_cost": 2000,
    }
    r = client.post("/travel-requests", json=new_req)
    req_id = r.json()["id"]
    print(f"③ 提交申请（id={req_id}）：", r.status_code, "状态 =", r.json()["status"])

    print("\n===== W2：审批流 =====")
    # 主管的待办 = “待审批”列表
    pending = client.get("/travel-requests", params={"status": "pending"}).json()
    print(f"④ 主管待办（{len(pending)} 条待审批）：", [x["destination"] for x in pending])

    # 权限校验：员工张三（id=1）想审批 → 应被拒绝 403
    r = client.post(f"/travel-requests/{req_id}/approve", json={"approver_id": 1})
    print("⑤ 员工越权审批（应 403）：", r.status_code, "→", r.json()["detail"])

    # 主管王经理（id=3）通过
    r = client.post(
        f"/travel-requests/{req_id}/approve",
        json={"approver_id": 3, "comment": "同意，注意控制费用"},
    )
    print("⑥ 主管通过：", r.status_code, "| 状态 =", r.json()["status"],
          "| 意见 =", r.json()["approval_comment"])

    # 状态机保护：已通过的再审一次 → 应被拒绝 400
    r = client.post(f"/travel-requests/{req_id}/approve", json={"approver_id": 3})
    print("⑦ 重复审批（应 400）：", r.status_code, "→", r.json()["detail"])

    # 员工查看自己的申请，确认状态已经流转
    mine = client.get("/travel-requests", params={"applicant_id": 1}).json()
    print("⑧ 张三看自己的申请：", [(x["destination"], x["status"]) for x in mine])
