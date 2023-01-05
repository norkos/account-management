from fastapi import HTTPException
from fastapi import status


def raise_not_found(detail: str = None):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def raise_bad_request(detail: str = None):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def raise_email_already_used():
    raise_bad_request('E-mail is already used')
