"""
스케줄러 서비스 - 매달 1일 자동 투표 요청
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.user_service import UserService
from app.services.vote_service import VoteService
from app.api.sse import send_sse_event


class SchedulerService:
    """스케줄러 서비스 - 자동 투표 요청 관리"""
    
    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)
        self.vote_service = VoteService(db)
    
    async def send_monthly_vote_request(self, month: str, vote_period_days: int = 7) -> Dict[str, Any]:
        """
        매달 1일 자동 투표 요청 전송
        
        Args:
            month: 투표 월 (YYYY-MM 형식)
            vote_period_days: 투표 기간 (일)
            
        Returns:
            전송 결과 정보
        """
        try:
            # 1. 모든 활성 사용자 조회
            active_users = self.user_service.get_active_users()
            user_count = len(active_users)
            
            # 2. 투표 마감일 계산
            vote_deadline = datetime.now() + timedelta(days=vote_period_days)
            
            # 3. SSE 이벤트 전송 (모든 사용자에게)
            sse_event = {
                "type": "auto_vote_request",
                "data": {
                    "message": f"이번 달({month}) 회식 투표를 시작합니다!",
                    "month": month,
                    "deadline": vote_deadline.isoformat(),
                    "vote_period_days": vote_period_days,
                    "total_users": user_count
                }
            }
            
            # 4. 모든 사용자에게 SSE 이벤트 전송
            sent_count = 0
            for user in active_users:
                try:
                    await send_sse_event(
                        client_id=user.emp_no,
                        event=sse_event,
                        channels=['votes', 'chat']
                    )
                    sent_count += 1
                except Exception as e:
                    print(f"SSE 전송 실패 - 사용자 {user.emp_no}: {e}")
            
            # 5. 투표 요청 이력 저장
            self.vote_service.save_vote_request_history(
                month=month,
                total_users=user_count,
                sent_users=sent_count,
                deadline=vote_deadline
            )
            
            return {
                "status": "S",
                "message": f"{month} 투표 요청이 전송되었습니다",
                "sent_to_users": sent_count,
                "total_users": user_count,
                "vote_deadline": vote_deadline.isoformat()
            }
            
        except Exception as e:
            return {
                "status": "E",
                "message": f"투표 요청 전송 실패: {str(e)}",
                "sent_to_users": 0,
                "total_users": 0
            }
    
    async def send_vote_reminder(self, month: str, days_remaining: int) -> Dict[str, Any]:
        """
        투표 마감 임박 알림 전송
        
        Args:
            month: 투표 월
            days_remaining: 남은 일수
        """
        try:
            # 아직 투표하지 않은 사용자 조회
            non_voted_users = self.vote_service.get_non_voted_users(month)
            
            reminder_event = {
                "type": "vote_reminder",
                "data": {
                    "message": f"투표 마감이 {days_remaining}일 남았습니다!",
                    "month": month,
                    "days_remaining": days_remaining,
                    "non_voted_count": len(non_voted_users)
                }
            }
            
            sent_count = 0
            for user in non_voted_users:
                try:
                    await send_sse_event(
                        client_id=user.emp_no,
                        event=reminder_event,
                        channels=['votes', 'chat']
                    )
                    sent_count += 1
                except Exception as e:
                    print(f"투표 알림 전송 실패 - 사용자 {user.emp_no}: {e}")
            
            return {
                "status": "S",
                "message": f"투표 알림이 {sent_count}명에게 전송되었습니다",
                "sent_to_users": sent_count,
                "non_voted_users": len(non_voted_users)
            }
            
        except Exception as e:
            return {
                "status": "E",
                "message": f"투표 알림 전송 실패: {str(e)}"
            }
    
    def get_vote_status(self, month: str) -> Dict[str, Any]:
        """
        투표 상태 조회
        
        Args:
            month: 투표 월
            
        Returns:
            투표 상태 정보
        """
        try:
            # 전체 사용자 수
            total_users = self.user_service.get_active_user_count()
            
            # 투표한 사용자 수
            voted_users = self.vote_service.get_voted_user_count(month)
            
            # 투표율 계산
            vote_rate = (voted_users / total_users * 100) if total_users > 0 else 0
            
            # 투표 요청 이력 조회
            vote_request = self.vote_service.get_vote_request_history(month)
            
            return {
                "month": month,
                "total_users": total_users,
                "voted_users": voted_users,
                "vote_rate": round(vote_rate, 1),
                "deadline": vote_request.deadline.isoformat() if vote_request else None,
                "remaining_days": self._calculate_remaining_days(vote_request.deadline) if vote_request else 0
            }
            
        except Exception as e:
            return {
                "month": month,
                "total_users": 0,
                "voted_users": 0,
                "vote_rate": 0,
                "error": str(e)
            }
    
    def _calculate_remaining_days(self, deadline: datetime) -> int:
        """마감일까지 남은 일수 계산"""
        if not deadline:
            return 0
        
        remaining = deadline - datetime.now()
        return max(0, remaining.days)
