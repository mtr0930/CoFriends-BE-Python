"""
Restaurant suggestions API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.core.database import get_db
from app.services.restaurant_suggestion_service import RestaurantSuggestionService
from app.schemas import (
    RestaurantSuggestionRequest, 
    RestaurantSuggestionResponse, 
    RestaurantSuggestionListResponse
)

router = APIRouter(prefix="/places", tags=["Restaurant Suggestions"])


async def send_sse_event(event_type: str, data: dict):
    """SSE 이벤트 전송"""
    try:
        # SSE 이벤트 전송 로직 (향후 구현)
        print(f"📡 SSE Event: {event_type} - {json.dumps(data, ensure_ascii=False)}")
    except Exception as e:
        print(f"❌ SSE Event Error: {e}")


@router.post("/suggestions", response_model=RestaurantSuggestionResponse)
async def create_restaurant_suggestion(
    request: RestaurantSuggestionRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new restaurant suggestion
    식당 추천 추가
    """
    try:
        service = RestaurantSuggestionService(db)
        result = service.create_suggestion(request)
        
        # 🔥 SSE로 실시간 업데이트 전송
        print(f"📢 Restaurant suggestion added: {result.place_nm} by {result.emp_no}")
        
        # SSE 이벤트 전송
        await send_sse_event("restaurant_suggestion_added", {
            "suggestion_id": result.suggestion_id,
            "place_nm": result.place_nm,
            "emp_no": result.emp_no,
            "created_at": result.created_at.isoformat()
        })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions", response_model=dict)
async def get_restaurant_suggestions(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    emp_no: Optional[str] = Query(None, description="Employee number for like status"),
    db: Session = Depends(get_db)
):
    """
    Get restaurant suggestions with pagination
    식당 추천 목록 조회 (페이지네이션)
    """
    try:
        service = RestaurantSuggestionService(db)
        suggestions = service.get_suggestions(page=page, size=size, emp_no=emp_no)
        total_count = service.get_total_count()
        
        # 프론트엔드 호환성을 위해 데이터 형식 변환
        ideas = []
        for suggestion in suggestions:
            ideas.append({
                "id": str(suggestion.suggestion_id),
                "name": suggestion.place_nm,
                "link": suggestion.link,
                "description": suggestion.memo,
                "likeCount": suggestion.like_count,
                "likedByMe": suggestion.is_liked,
                "createdAt": suggestion.created_at.isoformat(),
                "submittedBy": suggestion.emp_no,
                "comments": []  # 댓글은 별도 API로 처리
            })
        
        return {
            "ideas": ideas,
            "total_count": total_count,
            "page": page,
            "size": size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/{suggestion_id}", response_model=RestaurantSuggestionResponse)
async def get_restaurant_suggestion(
    suggestion_id: int,
    emp_no: Optional[str] = Query(None, description="Employee number for like status"),
    db: Session = Depends(get_db)
):
    """
    Get a specific restaurant suggestion by ID
    특정 식당 추천 조회
    """
    try:
        service = RestaurantSuggestionService(db)
        suggestion = service.get_suggestion_by_id(suggestion_id, emp_no)
        
        if not suggestion:
            raise HTTPException(status_code=404, detail="Restaurant suggestion not found")
        
        return suggestion
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/{suggestion_id}/like")
async def toggle_like_restaurant_suggestion(
    suggestion_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Toggle like status for a restaurant suggestion
    식당 추천 좋아요 토글
    """
    try:
        emp_no = request.get("empNo")
        like = request.get("like", True)
        
        if not emp_no:
            raise HTTPException(status_code=400, detail="empNo is required")
        
        service = RestaurantSuggestionService(db)
        result = service.toggle_like(suggestion_id, emp_no)
        
        # 댓글 정보도 함께 가져오기
        comments = service.get_comments(suggestion_id, emp_no)
        
        # 프론트엔드 호환성을 위해 RestaurantIdea 형식으로 변환
        frontend_response = {
            "id": str(result.suggestion_id),
            "name": result.place_nm,
            "link": result.link,
            "description": result.memo,
            "likeCount": result.like_count,
            "likedByMe": result.is_liked,
            "createdAt": result.created_at.isoformat(),
            "submittedBy": result.emp_no,
            "comments": comments  # 댓글 정보 포함
        }
        
        return frontend_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/suggestions/{suggestion_id}/like")
async def unlike_restaurant_suggestion(
    suggestion_id: int,
    emp_no: str = Query(..., description="Employee number"),
    db: Session = Depends(get_db)
):
    """
    Unlike a restaurant suggestion
    식당 추천 좋아요 취소
    """
    try:
        service = RestaurantSuggestionService(db)
        success = service.unlike_suggestion(suggestion_id, emp_no)
        
        if not success:
            raise HTTPException(status_code=400, detail="Cannot unlike this suggestion")
        
        return {"message": "Suggestion unliked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/suggestions/{suggestion_id}")
async def delete_restaurant_suggestion(
    suggestion_id: int,
    emp_no: str = Query(..., description="Employee number"),
    db: Session = Depends(get_db)
):
    """
    Delete a restaurant suggestion (only by the author)
    식당 추천 삭제 (작성자만 가능)
    """
    try:
        service = RestaurantSuggestionService(db)
        success = service.delete_suggestion(suggestion_id, emp_no)
        
        if not success:
            raise HTTPException(status_code=404, detail="Restaurant suggestion not found or not authorized")
        
        return {"message": "Suggestion deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/{suggestion_id}/comments")
async def add_restaurant_comment(
    suggestion_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Add a comment to a restaurant suggestion
    식당 추천에 댓글 추가
    """
    try:
        message = request.get("message")
        emp_no = request.get("empNo")
        
        if not message or not emp_no:
            raise HTTPException(status_code=400, detail="message and empNo are required")
        
        service = RestaurantSuggestionService(db)
        comment = service.add_comment(suggestion_id, message, emp_no)
        
        # 프론트엔드 호환성을 위해 형식 변환
        frontend_response = {
            "id": str(comment.comment_id),
            "message": comment.message,
            "author": comment.emp_no,
            "authorName": comment.emp_no,
            "createdAt": comment.created_at.isoformat(),
            "likeCount": 0,
            "likedByMe": False
        }
        
        return frontend_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggestions/{suggestion_id}/comments")
async def get_restaurant_comments(
    suggestion_id: int,
    emp_no: Optional[str] = Query(None, description="Employee number for like status"),
    db: Session = Depends(get_db)
):
    """
    Get comments for a restaurant suggestion
    식당 추천 댓글 조회
    """
    try:
        service = RestaurantSuggestionService(db)
        comments = service.get_comments(suggestion_id, emp_no)
        return {"comments": comments}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/suggestions/{suggestion_id}/comments/{comment_id}")
async def update_restaurant_comment(
    suggestion_id: int,
    comment_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Update a restaurant comment (only by the author)
    식당 추천 댓글 수정 (작성자만 가능)
    """
    try:
        message = request.get("message")
        emp_no = request.get("empNo")
        
        if not message or not emp_no:
            raise HTTPException(status_code=400, detail="message and empNo are required")
        
        service = RestaurantSuggestionService(db)
        comment = service.update_comment(comment_id, message, emp_no)
        
        # 프론트엔드 호환성을 위해 형식 변환
        frontend_response = {
            "id": str(comment.comment_id),
            "message": comment.message,
            "author": comment.emp_no,
            "authorName": comment.emp_no,
            "createdAt": comment.created_at.isoformat(),
            "likeCount": 0,  # 수정 시에는 좋아요 정보를 다시 조회해야 함
            "likedByMe": False
        }
        
        return frontend_response
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/suggestions/{suggestion_id}/comments/{comment_id}")
async def delete_restaurant_comment(
    suggestion_id: int,
    comment_id: int,
    emp_no: str = Query(..., description="Employee number"),
    db: Session = Depends(get_db)
):
    """
    Delete a restaurant comment (only by the author)
    식당 추천 댓글 삭제 (작성자만 가능)
    """
    try:
        service = RestaurantSuggestionService(db)
        success = service.delete_comment(comment_id, emp_no)
        
        if not success:
            raise HTTPException(status_code=404, detail="Comment not found or not authorized")
        
        return {"message": "Comment deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/suggestions/{suggestion_id}/comments/{comment_id}/like")
async def toggle_comment_like(
    suggestion_id: int,
    comment_id: int,
    request: dict,
    db: Session = Depends(get_db)
):
    """
    Toggle like status for a restaurant comment
    식당 추천 댓글 좋아요 토글
    """
    try:
        emp_no = request.get("empNo")
        if not emp_no:
            raise HTTPException(status_code=400, detail="empNo is required")
        
        service = RestaurantSuggestionService(db)
        result = service.toggle_comment_like(comment_id, emp_no)
        
        # 프론트엔드 호환성을 위해 형식 변환
        frontend_response = {
            "id": str(result.comment_id),
            "message": result.message,
            "author": result.emp_no,
            "authorName": result.emp_no,
            "createdAt": result.created_at.isoformat(),
            "likeCount": result.like_count,
            "likedByMe": result.is_liked
        }
        
        return frontend_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
