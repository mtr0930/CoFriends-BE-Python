"""
Restaurant suggestion service layer
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.postgres import RestaurantSuggestion, RestaurantSuggestionLike
from app.schemas import RestaurantSuggestionRequest, RestaurantSuggestionResponse


class RestaurantSuggestionService:
    """Restaurant suggestion service for handling restaurant suggestions"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_suggestion(self, request: RestaurantSuggestionRequest) -> RestaurantSuggestionResponse:
        """Create a new restaurant suggestion"""
        suggestion = RestaurantSuggestion(
            place_nm=request.name,
            link=request.link,
            memo=request.description,
            emp_no=request.empNo
        )
        
        self.db.add(suggestion)
        self.db.commit()
        self.db.refresh(suggestion)
        
        return RestaurantSuggestionResponse(
            suggestion_id=suggestion.suggestion_id,
            place_nm=suggestion.place_nm,
            link=suggestion.link,
            memo=suggestion.memo,
            emp_no=suggestion.emp_no,
            created_at=suggestion.created_at,
            like_count=0,
            is_liked=False
        )
    
    def get_suggestions(self, page: int = 1, size: int = 10, emp_no: Optional[str] = None) -> List[RestaurantSuggestionResponse]:
        """Get restaurant suggestions with pagination"""
        offset = (page - 1) * size
        
        # Base query
        query = self.db.query(RestaurantSuggestion)
        
        # Apply pagination
        suggestions = query.order_by(desc(RestaurantSuggestion.created_at)).offset(offset).limit(size).all()
        
        result = []
        for suggestion in suggestions:
            # Get like count
            like_count = self.db.query(RestaurantSuggestionLike).filter(
                RestaurantSuggestionLike.suggestion_id == suggestion.suggestion_id
            ).count()
            
            # Check if current user liked this suggestion
            is_liked = False
            if emp_no:
                existing_like = self.db.query(RestaurantSuggestionLike).filter(
                    RestaurantSuggestionLike.suggestion_id == suggestion.suggestion_id,
                    RestaurantSuggestionLike.emp_no == emp_no
                ).first()
                is_liked = existing_like is not None
            
            result.append(RestaurantSuggestionResponse(
                suggestion_id=suggestion.suggestion_id,
                place_nm=suggestion.place_nm,
                link=suggestion.link,
                memo=suggestion.memo,
                emp_no=suggestion.emp_no,
                created_at=suggestion.created_at,
                like_count=like_count,
                is_liked=is_liked
            ))
        
        return result
    
    def get_suggestion_by_id(self, suggestion_id: int, emp_no: Optional[str] = None) -> Optional[RestaurantSuggestionResponse]:
        """Get a specific restaurant suggestion by ID"""
        suggestion = self.db.query(RestaurantSuggestion).filter(
            RestaurantSuggestion.suggestion_id == suggestion_id
        ).first()
        
        if not suggestion:
            return None
        
        # Get like count
        like_count = self.db.query(RestaurantSuggestionLike).filter(
            RestaurantSuggestionLike.suggestion_id == suggestion_id
        ).count()
        
        # Check if current user liked this suggestion
        is_liked = False
        if emp_no:
            existing_like = self.db.query(RestaurantSuggestionLike).filter(
                RestaurantSuggestionLike.suggestion_id == suggestion_id,
                RestaurantSuggestionLike.emp_no == emp_no
            ).first()
            is_liked = existing_like is not None
        
        return RestaurantSuggestionResponse(
            suggestion_id=suggestion.suggestion_id,
            place_nm=suggestion.place_nm,
            link=suggestion.link,
            memo=suggestion.memo,
            emp_no=suggestion.emp_no,
            created_at=suggestion.created_at,
            like_count=like_count,
            is_liked=is_liked
        )
    
    def like_suggestion(self, suggestion_id: int, emp_no: str) -> bool:
        """Like a restaurant suggestion"""
        # Check if suggestion exists
        suggestion = self.db.query(RestaurantSuggestion).filter(
            RestaurantSuggestion.suggestion_id == suggestion_id
        ).first()
        
        if not suggestion:
            return False
        
        # Check if already liked
        existing_like = self.db.query(RestaurantSuggestionLike).filter(
            RestaurantSuggestionLike.suggestion_id == suggestion_id,
            RestaurantSuggestionLike.emp_no == emp_no
        ).first()
        
        if existing_like:
            return False  # Already liked
        
        # Add like
        like = RestaurantSuggestionLike(
            suggestion_id=suggestion_id,
            emp_no=emp_no
        )
        
        self.db.add(like)
        self.db.commit()
        
        return True
    
    def unlike_suggestion(self, suggestion_id: int, emp_no: str) -> bool:
        """Unlike a restaurant suggestion"""
        # Check if like exists
        existing_like = self.db.query(RestaurantSuggestionLike).filter(
            RestaurantSuggestionLike.suggestion_id == suggestion_id,
            RestaurantSuggestionLike.emp_no == emp_no
        ).first()
        
        if not existing_like:
            return False  # Not liked
        
        # Remove like
        self.db.delete(existing_like)
        self.db.commit()
        
        return True
    
    def delete_suggestion(self, suggestion_id: int, emp_no: str) -> bool:
        """Delete a restaurant suggestion (only by the author)"""
        suggestion = self.db.query(RestaurantSuggestion).filter(
            RestaurantSuggestion.suggestion_id == suggestion_id,
            RestaurantSuggestion.emp_no == emp_no
        ).first()
        
        if not suggestion:
            return False
        
        # Delete suggestion (cascade will delete likes)
        self.db.delete(suggestion)
        self.db.commit()
        
        return True
    
    def toggle_like(self, suggestion_id: int, emp_no: str) -> RestaurantSuggestionResponse:
        """Toggle like status for a restaurant suggestion"""
        print(f"🔥 toggle_like called: suggestion_id={suggestion_id}, emp_no={emp_no}")
        
        suggestion = self.db.query(RestaurantSuggestion).filter(
            RestaurantSuggestion.suggestion_id == suggestion_id
        ).first()
        
        if not suggestion:
            print(f"❌ Suggestion not found: {suggestion_id}")
            raise ValueError("Suggestion not found")
        
        print(f"✅ Suggestion found: {suggestion.place_nm}")
        
        existing_like = self.db.query(RestaurantSuggestionLike).filter(
            RestaurantSuggestionLike.suggestion_id == suggestion_id,
            RestaurantSuggestionLike.emp_no == emp_no
        ).first()
        
        if existing_like:
            print(f"🗑️ Deleting existing like: {existing_like.like_id}")
            self.db.delete(existing_like)
            self.db.commit()
        else:
            print(f"➕ Creating new like for suggestion {suggestion_id}")
            new_like = RestaurantSuggestionLike(suggestion_id=suggestion_id, emp_no=emp_no)
            self.db.add(new_like)
            self.db.commit()
            print(f"✅ New like created: {new_like.like_id}")
        
        result = self.get_suggestion_by_id(suggestion_id, emp_no)
        print(f"📊 Final result: like_count={result.like_count}, is_liked={result.is_liked}")
        return result
    
    def get_total_count(self) -> int:
        """Get total number of suggestions"""
        return self.db.query(RestaurantSuggestion).count()
    
    def add_comment(self, suggestion_id: int, message: str, emp_no: str):
        """Add a comment to a restaurant suggestion"""
        from app.models.postgres import RestaurantSuggestionComment
        
        comment = RestaurantSuggestionComment(
            suggestion_id=suggestion_id,
            message=message,
            emp_no=emp_no
        )
        
        self.db.add(comment)
        self.db.commit()
        self.db.refresh(comment)
        
        return comment
    
    def get_comments(self, suggestion_id: int, emp_no: Optional[str] = None) -> List[dict]:
        """Get comments for a restaurant suggestion"""
        from app.models.postgres import RestaurantSuggestionComment, RestaurantCommentLike
        
        comments = self.db.query(RestaurantSuggestionComment).filter(
            RestaurantSuggestionComment.suggestion_id == suggestion_id
        ).order_by(RestaurantSuggestionComment.created_at.desc()).all()
        
        result = []
        for comment in comments:
            # 댓글 좋아요 수 조회
            like_count = self.db.query(RestaurantCommentLike).filter(
                RestaurantCommentLike.comment_id == comment.comment_id
            ).count()
            
            # 현재 사용자가 좋아요 했는지 확인
            is_liked = False
            if emp_no:
                existing_like = self.db.query(RestaurantCommentLike).filter(
                    RestaurantCommentLike.comment_id == comment.comment_id,
                    RestaurantCommentLike.emp_no == emp_no
                ).first()
                is_liked = existing_like is not None
            
            result.append({
                "id": str(comment.comment_id),
                "message": comment.message,
                "author": comment.emp_no,
                "authorName": comment.emp_no,  # 실제로는 사용자 이름을 조회해야 함
                "createdAt": comment.created_at.isoformat(),
                "likeCount": like_count,
                "likedByMe": is_liked
            })
        
        return result
    
    def toggle_comment_like(self, comment_id: int, emp_no: str):
        """Toggle like status for a restaurant comment"""
        from app.models.postgres import RestaurantSuggestionComment, RestaurantCommentLike
        
        print(f"🔥 toggle_comment_like called: comment_id={comment_id}, emp_no={emp_no}")
        
        comment = self.db.query(RestaurantSuggestionComment).filter(
            RestaurantSuggestionComment.comment_id == comment_id
        ).first()
        
        if not comment:
            print(f"❌ Comment not found: {comment_id}")
            raise ValueError("Comment not found")
        
        print(f"✅ Comment found: {comment.message}")
        
        existing_like = self.db.query(RestaurantCommentLike).filter(
            RestaurantCommentLike.comment_id == comment_id,
            RestaurantCommentLike.emp_no == emp_no
        ).first()
        
        if existing_like:
            print(f"🗑️ Deleting existing comment like: {existing_like.like_id}")
            self.db.delete(existing_like)
            self.db.commit()
        else:
            print(f"➕ Creating new comment like for comment {comment_id}")
            new_like = RestaurantCommentLike(comment_id=comment_id, emp_no=emp_no)
            self.db.add(new_like)
            self.db.commit()
            print(f"✅ New comment like created: {new_like.like_id}")
        
        # 업데이트된 댓글 정보 반환
        updated_comment = self.db.query(RestaurantSuggestionComment).filter(
            RestaurantSuggestionComment.comment_id == comment_id
        ).first()
        
        like_count = self.db.query(RestaurantCommentLike).filter(
            RestaurantCommentLike.comment_id == comment_id
        ).count()
        
        is_liked = self.db.query(RestaurantCommentLike).filter(
            RestaurantCommentLike.comment_id == comment_id,
            RestaurantCommentLike.emp_no == emp_no
        ).first() is not None
        
        print(f"📊 Final comment result: like_count={like_count}, is_liked={is_liked}")
        
        # RestaurantCommentResponse 형식으로 반환
        from app.schemas import RestaurantCommentResponse
        return RestaurantCommentResponse(
            comment_id=updated_comment.comment_id,
            suggestion_id=updated_comment.suggestion_id,
            emp_no=updated_comment.emp_no,
            message=updated_comment.message,
            created_at=updated_comment.created_at,
            like_count=like_count,
            is_liked=is_liked
        )
    
    def update_comment(self, comment_id: int, message: str, emp_no: str):
        """Update a restaurant comment (only by the author)"""
        from app.models.postgres import RestaurantSuggestionComment
        
        print(f"🔥 update_comment called: comment_id={comment_id}, emp_no={emp_no}")
        
        comment = self.db.query(RestaurantSuggestionComment).filter(
            RestaurantSuggestionComment.comment_id == comment_id
        ).first()
        
        if not comment:
            print(f"❌ Comment not found: {comment_id}")
            raise ValueError("Comment not found")
        
        # 작성자 확인
        if comment.emp_no != emp_no:
            print(f"❌ Unauthorized: comment author {comment.emp_no} != requester {emp_no}")
            raise ValueError("Only the author can update this comment")
        
        print(f"✅ Updating comment: {comment.message} -> {message}")
        
        # 댓글 내용 업데이트
        comment.message = message
        comment.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(comment)
        
        print(f"✅ Comment updated successfully")
        return comment
    
    def delete_comment(self, comment_id: int, emp_no: str) -> bool:
        """Delete a restaurant comment (only by the author)"""
        from app.models.postgres import RestaurantSuggestionComment
        
        print(f"🔥 delete_comment called: comment_id={comment_id}, emp_no={emp_no}")
        
        comment = self.db.query(RestaurantSuggestionComment).filter(
            RestaurantSuggestionComment.comment_id == comment_id
        ).first()
        
        if not comment:
            print(f"❌ Comment not found: {comment_id}")
            return False
        
        # 작성자 확인
        if comment.emp_no != emp_no:
            print(f"❌ Unauthorized: comment author {comment.emp_no} != requester {emp_no}")
            raise ValueError("Only the author can delete this comment")
        
        print(f"✅ Deleting comment: {comment.message}")
        
        # 댓글 삭제
        self.db.delete(comment)
        self.db.commit()
        
        print(f"✅ Comment deleted successfully")
        return True
