"""
Vote service layer for menu, place, and date votes
"""
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.postgres import User, Menu, Place, UserMenuVote, UserPlaceVote, UserDateVote
from app.schemas import MenuPreference, PlaceVoteRequest, PlaceVoteResponse


class VoteService:
    """Vote service for handling all types of votes"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_menu_date_preference(self, preference: MenuPreference, user: User):
        """Save user's menu and date preferences"""
        # Delete existing menu votes
        self.db.query(UserMenuVote).filter(UserMenuVote.user_id == user.user_id).delete()
        
        # Delete existing date votes
        self.db.query(UserDateVote).filter(UserDateVote.emp_no == preference.emp_no).delete()
        
        # Save new menu votes
        for menu_type in preference.menu_types:
            menu = self.db.query(Menu).filter(Menu.menu_type == menu_type).first()
            if menu:
                vote = UserMenuVote(user_id=user.user_id, menu_id=menu.menu_id)
                self.db.add(vote)
        
        # Save new date votes
        for date in preference.preferred_dates:
            vote = UserDateVote(emp_no=preference.emp_no, preferred_date=date)
            self.db.add(vote)
        
        self.db.commit()
    
    def get_voters_by_menu_type(self, menu_type: str) -> List[str]:
        """Get list of employee numbers who voted for a menu type"""
        votes = self.db.query(UserMenuVote).join(Menu).filter(
            Menu.menu_type == menu_type
        ).all()
        
        return [vote.user.emp_no for vote in votes]
    
    def get_voters_by_date(self, date: str) -> List[str]:
        """Get list of employee numbers who voted for a date"""
        votes = self.db.query(UserDateVote).filter(
            UserDateVote.preferred_date == date
        ).all()
        
        return [vote.emp_no for vote in votes]
    
    def process_place_vote(self, request: PlaceVoteRequest) -> PlaceVoteResponse:
        """Process place vote (like/unlike)"""
        user = self.db.query(User).filter(User.emp_no == request.emp_no).first()
        if not user:
            raise ValueError(f"User not found: {request.emp_no}")
        
        place = self.db.query(Place).filter(Place.place_id == request.place_id).first()
        if not place:
            raise ValueError(f"Place not found: {request.place_id}")
        
        existing_vote = self.db.query(UserPlaceVote).filter(
            UserPlaceVote.user_id == user.user_id,
            UserPlaceVote.place_id == request.place_id
        ).first()
        
        if request.action == "like":
            if not existing_vote:
                vote = UserPlaceVote(user_id=user.user_id, place_id=request.place_id)
                self.db.add(vote)
                self.db.commit()
            is_voted = True
        else:  # unlike
            if existing_vote:
                self.db.delete(existing_vote)
                self.db.commit()
            is_voted = False
        
        # Get updated vote count
        vote_count = self.db.query(UserPlaceVote).filter(
            UserPlaceVote.place_id == request.place_id
        ).count()
        
        return PlaceVoteResponse(
            placeId=request.place_id,
            voteCount=vote_count,
            isVoted=is_voted
        )
    
    def get_vote_results(self, month: str = None) -> Dict[str, Any]:
        """Get vote results for a specific month"""
        from datetime import datetime
        
        if not month:
            current_date = datetime.now()
            month = current_date.strftime("%Y-%m")
        
        # Get menu vote counts
        menu_votes = {}
        menus = self.db.query(Menu).all()
        for menu in menus:
            count = self.db.query(UserMenuVote).filter(
                UserMenuVote.menu_id == menu.menu_id
            ).count()
            menu_votes[menu.menu_type] = count
        
        # Get date vote counts
        date_votes = {}
        date_vote_records = self.db.query(UserDateVote).all()
        for vote in date_vote_records:
            # preferred_date가 이미 문자열이므로 strftime() 호출하지 않음
            date_str = vote.preferred_date
            date_votes[date_str] = date_votes.get(date_str, 0) + 1
        
        return {
            "month": month,
            "menu_votes": menu_votes,
            "date_votes": date_votes
        }
    
    def get_user_vote_history(self, emp_no: str) -> List[Dict[str, Any]]:
        """Get user's vote history"""
        try:
            user = self.db.query(User).filter(User.emp_no == emp_no).first()
            if not user:
                print(f"❌ User not found for emp_no: {emp_no}")
                return []
            
            print(f"✅ Found user: {user.emp_no}, user_id: {user.user_id}")
            
            # Get menu votes
            menu_votes = self.db.query(UserMenuVote).filter(
                UserMenuVote.user_id == user.user_id
            ).all()
            
            print(f"📊 Menu votes count: {len(menu_votes)}")
            
            # Get date votes
            date_votes = self.db.query(UserDateVote).filter(
                UserDateVote.emp_no == emp_no
            ).all()
            
            print(f"📅 Date votes count: {len(date_votes)}")
            
            result = [{
                "menu_votes": [vote.menu.menu_type for vote in menu_votes],
                "date_votes": [vote.preferred_date for vote in date_votes],  # 이미 문자열이므로 strftime() 불필요
                "emp_no": emp_no
            }]
            
            print(f"✅ Vote history result: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Error in get_user_vote_history: {str(e)}")
            return []
    
    def get_past_dinner_history(self, emp_no: str, months: int = 3) -> List[Dict[str, Any]]:
        """Get past dinner history"""
        # This is a placeholder implementation
        # In a real system, this would query actual dinner records
        return []
    
    def get_user_preferences(self, emp_no: str) -> Dict[str, Any]:
        """Get user preferences based on vote history"""
        try:
            user = self.db.query(User).filter(User.emp_no == emp_no).first()
            if not user:
                print(f"❌ User not found for emp_no: {emp_no}")
                return {}
            
            # Get menu preferences
            menu_votes = self.db.query(UserMenuVote).filter(
                UserMenuVote.user_id == user.user_id
            ).all()
            
            menu_preferences = [vote.menu.menu_type for vote in menu_votes]
            
            # Get restaurant suggestions (실제 데이터 활용)
            from app.models.postgres import RestaurantSuggestion
            restaurant_suggestions = self.db.query(RestaurantSuggestion).filter(
                RestaurantSuggestion.emp_no == emp_no
            ).all()
            
            print(f"🍽️ Restaurant suggestions count: {len(restaurant_suggestions)}")
            
            result = {
                "menu_votes": menu_preferences,
                "emp_no": emp_no,
                "restaurant_suggestions": [
                    {
                        "name": suggestion.place_nm,
                        "link": suggestion.link,
                        "memo": suggestion.memo,
                        "created_at": suggestion.created_at.isoformat() if suggestion.created_at else None
                    }
                    for suggestion in restaurant_suggestions
                ]
            }
            
            print(f"✅ User preferences result: {result}")
            return result
            
        except Exception as e:
            print(f"❌ Error in get_user_preferences: {str(e)}")
            return {}
    
    def reset_vote_history(self, emp_no: str):
        """Reset all vote history for a user"""
        user = self.db.query(User).filter(User.emp_no == emp_no).first()
        if not user:
            raise ValueError(f"User not found: {emp_no}")
        
        # Delete menu votes
        self.db.query(UserMenuVote).filter(UserMenuVote.user_id == user.user_id).delete()
        
        # Delete date votes
        self.db.query(UserDateVote).filter(UserDateVote.emp_no == emp_no).delete()
        
        # Delete place votes
        self.db.query(UserPlaceVote).filter(UserPlaceVote.user_id == user.user_id).delete()
        
        self.db.commit()
    
    def get_vote_statistics(self) -> dict:
        """Get comprehensive vote statistics"""
        # Menu vote statistics
        menu_votes = self.db.query(UserMenuVote).join(Menu).all()
        menu_stats = {}
        for vote in menu_votes:
            menu_type = vote.menu.menu_type
            if menu_type not in menu_stats:
                menu_stats[menu_type] = []
            menu_stats[menu_type].append(vote.user.emp_no)
        
        # Place vote statistics
        place_votes = self.db.query(UserPlaceVote).join(Place).all()
        place_stats = {}
        for vote in place_votes:
            place_name = vote.place.place_nm
            if place_name not in place_stats:
                place_stats[place_name] = []
            place_stats[place_name].append(vote.user.emp_no)
        
        # Date vote statistics
        date_votes = self.db.query(UserDateVote).all()
        date_stats = {}
        for vote in date_votes:
            date = vote.preferred_date
            if date not in date_stats:
                date_stats[date] = []
            date_stats[date].append(vote.emp_no)
        
        # Total voters
        total_voters = len(set([vote.user.emp_no for vote in menu_votes] + 
                             [vote.user.emp_no for vote in place_votes] + 
                             [vote.emp_no for vote in date_votes]))
        
        return {
            "menu_votes": menu_stats,
            "place_votes": place_stats,
            "date_votes": date_stats,
            "total_voters": total_voters,
            "active_voters": total_voters
        }
    
    def get_user_vote_history(self, emp_no: str) -> dict:
        """Get vote history for a specific user"""
        user = self.db.query(User).filter(User.emp_no == emp_no).first()
        if not user:
            raise ValueError(f"User not found: {emp_no}")
        
        # Get user's menu votes
        menu_votes = self.db.query(UserMenuVote).filter(UserMenuVote.user_id == user.user_id).join(Menu).all()
        menu_types = [vote.menu.menu_type for vote in menu_votes]
        
        # Get user's place votes
        place_votes = self.db.query(UserPlaceVote).filter(UserPlaceVote.user_id == user.user_id).join(Place).all()
        place_names = [vote.place.place_nm for vote in place_votes]
        
        # Get user's date votes
        date_votes = self.db.query(UserDateVote).filter(UserDateVote.emp_no == emp_no).all()
        preferred_dates = [vote.preferred_date for vote in date_votes]
        
        return {
            "emp_no": emp_no,
            "menu_types": menu_types,
            "place_names": place_names,
            "preferred_dates": preferred_dates,
            "total_votes": len(menu_votes) + len(place_votes) + len(date_votes)
        }

