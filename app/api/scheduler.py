"""
스케줄러 API - 자동 투표 요청 관리
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.services.scheduler_service import SchedulerService

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


class AutoVoteRequest(BaseModel):
    """자동 투표 요청 모델"""
    month: str
    vote_period_days: int = 7
    message: Optional[str] = None


class VoteReminderRequest(BaseModel):
    """투표 알림 요청 모델"""
    month: str
    days_remaining: int


@router.post("/auto-vote-request")
async def send_auto_vote_request(
    request: AutoVoteRequest,
    db: Session = Depends(get_db)
):
    """
    매달 1일 자동 투표 요청 전송
    """
    try:
        scheduler_service = SchedulerService(db)
        
        result = await scheduler_service.send_monthly_vote_request(
            month=request.month,
            vote_period_days=request.vote_period_days
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vote-reminder")
async def send_vote_reminder(
    request: VoteReminderRequest,
    db: Session = Depends(get_db)
):
    """
    투표 마감 임박 알림 전송
    """
    try:
        scheduler_service = SchedulerService(db)
        
        result = await scheduler_service.send_vote_reminder(
            month=request.month,
            days_remaining=request.days_remaining
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vote-status/{month}")
def get_vote_status(
    month: str,
    db: Session = Depends(get_db)
):
    """
    투표 상태 조회
    """
    try:
        scheduler_service = SchedulerService(db)
        
        result = scheduler_service.get_vote_status(month)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test-auto-vote")
async def test_auto_vote_request(
    db: Session = Depends(get_db)
):
    """
    테스트용 자동 투표 요청 (개발/테스트 환경에서만 사용)
    """
    try:
        from datetime import datetime
        
        # 현재 월로 테스트
        current_month = datetime.now().strftime("%Y-%m")
        
        scheduler_service = SchedulerService(db)
        
        result = await scheduler_service.send_monthly_vote_request(
            month=current_month,
            vote_period_days=7
        )
        
        return {
            "message": "테스트 자동 투표 요청이 전송되었습니다",
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
