import logging
from typing import Any

from fastapi import Depends
from fastapi import APIRouter, status

from acm_service.dependencies import get_token_header, get_2fa_token_header, get_account_service
from acm_service.utils.logconf import DEFAULT_LOGGER
from acm_service.services.account_service import AccountService

logger = logging.getLogger(DEFAULT_LOGGER)

router = APIRouter(
    prefix="/dev",
    tags=["dev"],
    dependencies=[Depends(get_token_header)]
)


@router.post('/erase_db', status_code=status.HTTP_202_ACCEPTED)
async def clear(_two_fa_token: Any = Depends(get_2fa_token_header),
                accounts: AccountService = Depends(get_account_service)):
    await accounts.delete_all()
    logger.info('All accounts were deleted')
