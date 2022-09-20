from sqlalchemy.orm import Session
from . import models, schemas


def get_account(db: Session, account_id: int) -> models.Account:
    return db.query(models.Account).filter(models.Account.id == account_id).first()


def get_account_by_email(db: Session, account_email: str) -> models.Account:
    return db.query(models.Account).filter(models.Account.email == account_email).first()


def get_accounts(db: Session) -> list[models.Account]:
    return db.query(models.Account).all()


def create_account(db: Session, account: schemas.AccountCreate) -> models.Account:
    db_account = models.Account(email=account.email, name=account.name)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

