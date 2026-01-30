from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.audit import write_audit_log
from app.auth import get_current_user, require_admin, require_role
from app.models import AuditLog, User, Account, Transaction
from app.schemas import DepositRequest, TransferRequest

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------- Basic protected route ----------
@router.get("/me")
def me(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    write_audit_log(
        db=db,
        actor_email=current_user.get("email"),
        action="BANK.VIEW_ME.SUCCESS",
        endpoint=str(request.url.path),
        status="success",
        ip_address=request.client.host if request.client else None,
    )
    return {"message": "Authenticated access granted", "user": current_user}


# ---------- Admin endpoints ----------
@router.get("/admin/overview")
def admin_overview(admin_user: dict = Depends(require_role("admin"))):
    return {"message": "Admin access granted", "admin": admin_user}


@router.get("/admin/audit")
def get_audit_logs(
    request: Request,
    admin_user: dict = Depends(require_admin),
    db: Session = Depends(get_db),
):
    # Audit the audit-view itself (compliance vibe)
    write_audit_log(
        db=db,
        actor_email=admin_user.get("email"),
        action="ADMIN.AUDIT.VIEW.SUCCESS",
        endpoint=str(request.url.path),
        status="success",
        ip_address=request.client.host if request.client else None,
    )

    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(50).all()
    return [
        {
            "actor_email": l.actor_email,
            "action": l.action,
            "endpoint": l.endpoint,
            "status": l.status,
            "ip_address": l.ip_address,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]


# ---------- Helpers ----------
def get_or_create_account(db: Session, user_id: int) -> Account:
    acc = db.query(Account).filter(Account.user_id == user_id).first()
    if acc is None:
        acc = Account(user_id=user_id, balance=0.0)
        db.add(acc)
        db.commit()
        db.refresh(acc)
    return acc


# ---------- Banking actions ----------
@router.post("/deposit")
def deposit(
    payload: DepositRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.amount <= 0:
        # Optional deposit-fail audit (nice for completeness)
        write_audit_log(
            db=db,
            actor_email=current_user.get("email"),
            action="BANK.DEPOSIT.FAIL",
            endpoint=str(request.url.path),
            status="fail",
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=400, detail="Amount must be positive")

    user = db.query(User).filter(User.email == current_user["email"]).first()
    if user is None:
        write_audit_log(
            db=db,
            actor_email=current_user.get("email"),
            action="BANK.DEPOSIT.FAIL",
            endpoint=str(request.url.path),
            status="fail",
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=404, detail="User not found")

    account = get_or_create_account(db, user.id)

    account.balance += payload.amount
    db.add(
        Transaction(
            from_account_id=None,
            to_account_id=account.id,
            amount=payload.amount,
            status="success",
        )
    )
    db.commit()

    write_audit_log(
        db=db,
        actor_email=current_user["email"],
        action="BANK.DEPOSIT.SUCCESS",
        endpoint=str(request.url.path),
        status="success",
        ip_address=request.client.host if request.client else None,
    )

    return {"balance": account.balance}


@router.post("/transfer")
def transfer(
    payload: TransferRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.amount <= 0:
        write_audit_log(
            db=db,
            actor_email=current_user.get("email"),
            action="BANK.TRANSFER.FAIL",
            endpoint=str(request.url.path),
            status="fail",
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=400, detail="Amount must be positive")

    if payload.to_email == current_user["email"]:
        write_audit_log(
            db=db,
            actor_email=current_user.get("email"),
            action="BANK.TRANSFER.FAIL",
            endpoint=str(request.url.path),
            status="fail",
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=400, detail="Cannot transfer to yourself")

    sender_user = db.query(User).filter(User.email == current_user["email"]).first()
    if sender_user is None:
        write_audit_log(
            db=db,
            actor_email=current_user.get("email"),
            action="BANK.TRANSFER.FAIL",
            endpoint=str(request.url.path),
            status="fail",
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=404, detail="Sender user not found")

    receiver_user = db.query(User).filter(User.email == payload.to_email).first()
    if receiver_user is None:
        write_audit_log(
            db=db,
            actor_email=current_user.get("email"),
            action="BANK.TRANSFER.FAIL",
            endpoint=str(request.url.path),
            status="fail",
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=404, detail="Recipient not found")

    sender_acc = get_or_create_account(db, sender_user.id)
    receiver_acc = get_or_create_account(db, receiver_user.id)

    # Prevent overdraft
    if sender_acc.balance < payload.amount:
        db.add(
            Transaction(
                from_account_id=sender_acc.id,
                to_account_id=receiver_acc.id,
                amount=payload.amount,
                status="failed",
            )
        )
        db.commit()

        write_audit_log(
            db=db,
            actor_email=current_user["email"],
            action="BANK.TRANSFER.FAIL",
            endpoint=str(request.url.path),
            status="fail",
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Apply transfer
    sender_acc.balance -= payload.amount
    receiver_acc.balance += payload.amount

    db.add(
        Transaction(
            from_account_id=sender_acc.id,
            to_account_id=receiver_acc.id,
            amount=payload.amount,
            status="success",
        )
    )
    db.commit()

    write_audit_log(
        db=db,
        actor_email=current_user["email"],
        action="BANK.TRANSFER.SUCCESS",
        endpoint=str(request.url.path),
        status="success",
        ip_address=request.client.host if request.client else None,
    )

    return {"sender_balance": sender_acc.balance}


@router.get("/transactions")
def my_transactions(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == current_user["email"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    account = db.query(Account).filter(Account.user_id == user.id).first()
    if account is None:
        return []

    txs = (
        db.query(Transaction)
        .filter(
            (Transaction.from_account_id == account.id)
            | (Transaction.to_account_id == account.id)
        )
        .order_by(Transaction.created_at.desc())
        .limit(50)
        .all()
    )

    return [
        {
            "id": t.id,
            "from_account_id": t.from_account_id,
            "to_account_id": t.to_account_id,
            "amount": t.amount,
            "status": t.status,
            "created_at": t.created_at.isoformat(),
        }
        for t in txs
    ]
