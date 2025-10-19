"""
대화형 질문 처리 서비스
"""
import re
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.services.vote_service import VoteService
from app.services.ai_response_service import AIResponseService
from app.services.place_service import PlaceService
from app.services.menu_service import MenuService
from app.services.user_service import UserService


class ConversationalService:
    """대화형 질문 처리 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.vote_service = VoteService(db)
        self.place_service = PlaceService(db, None)  # Redis는 필요시 주입
        self.menu_service = MenuService(db)
        self.user_service = UserService(db)
        self.ai_response_service = AIResponseService(db)
    
    def process_question(self, emp_no: str, question: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        사용자 질문 처리 및 응답 생성
        
        Args:
            emp_no: 사용자 사번
            question: 사용자 질문
            context: 추가 컨텍스트 정보
            
        Returns:
            AI 응답 및 관련 데이터
        """
        try:
            # 질문 유형 분류
            question_type = self._classify_question(question)
            
            # 질문 유형별 처리
            if question_type == "vote_results":
                return self._handle_vote_results_question(emp_no, question, context)
            elif question_type == "my_vote_history":
                return self._handle_my_vote_history_question(emp_no, question, context)
            elif question_type == "past_dinner":
                return self._handle_past_dinner_question(emp_no, question, context)
            elif question_type == "restaurant_recommendation":
                return self._handle_restaurant_recommendation_question(emp_no, question, context)
            elif question_type == "vote_request":
                return self._handle_vote_request_question(emp_no, question, context)
            else:
                return self._handle_general_question(emp_no, question, context)
                
        except Exception as e:
            return {
                "status": "E",
                "message": "질문 처리 오류",
                "response_text": f"죄송합니다. 질문을 처리하는 중 오류가 발생했습니다: {str(e)}",
                "action_required": "none",
                "error": str(e)
            }
    
    def _classify_question(self, question: str) -> str:
        """LLM을 사용한 질문 의도 분류"""
        try:
            # LLM을 사용한 의도 분석
            intent_prompt = f"""
다음 사용자 질문을 분석하여 의도를 분류해주세요.

질문: "{question}"

가능한 의도:
1. vote_request - 투표 요청 (투표하고 싶다, 투표할래, 선호도 입력 등)
2. vote_results - 투표 결과 조회 (투표 결과 알려줘, 누가 투표했는지 등)
3. my_vote_history - 개인 투표 이력 (내가 어떻게 투표했는지, 내 투표 기록 등)
4. past_dinner - 과거 회식 정보 (저번달 어디서 했는지, 지난달 회식 등)
5. restaurant_recommendation - 식당 추천 (추천해줘, 맛집 알려줘, 어디 갈까 등)
6. general - 기타

응답 형식: 의도명만 출력하세요.
예시: vote_request
"""
            
            print(f"🔍 Original question: {question}")
            print(f"🔍 Question type: {type(question)}")
            print(f"🔍 Question encoding: {question.encode('utf-8')}")
            
            # 경량 모델로 의도 분석 (빠른 응답을 위해 토큰 수 제한)
            result = self.ai_response_service.bedrock_service.generate_response(intent_prompt, max_tokens=50)
            
            if result.get("success"):
                intent = result["response"].strip().lower()
                print(f"🤖 LLM Intent Analysis: {intent}")
                
                # 유효한 의도인지 확인
                valid_intents = ["vote_request", "vote_results", "my_vote_history", "past_dinner", "restaurant_recommendation", "general"]
                if intent in valid_intents:
                    print(f"✅ Classified as: {intent}")
                    return intent
                else:
                    print(f"❌ Invalid intent: {intent}, using fallback")
                    return self._classify_question_fallback(question)
            else:
                print(f"❌ LLM intent analysis failed: {result.get('error')}, using fallback")
                return self._classify_question_fallback(question)
                
        except Exception as e:
            print(f"❌ Error in LLM intent analysis: {str(e)}, using fallback")
            return self._classify_question_fallback(question)
    
    def _classify_question_fallback(self, question: str) -> str:
        """키워드 기반 의도 분류 (LLM 실패 시 폴백)"""
        question_lower = question.lower()
        print(f"🔍 Fallback classifying question: '{question}' -> '{question_lower}'")
        
        # 투표 요청 관련 질문 (최우선순위)
        if any(keyword in question_lower for keyword in ["투표할래", "투표하기", "투표하고", "투표해", "선호도 입력", "메뉴 선택", "이번달 투표"]):
            print("✅ Fallback classified as: vote_request")
            return "vote_request"
        
        # 식당 추천 관련 질문
        elif any(keyword in question_lower for keyword in ["추천 식당", "식당 추천", "맛집 추천", "추천해줘", "추천해", "추천", "이번달 추천"]):
            print("✅ Fallback classified as: restaurant_recommendation")
            return "restaurant_recommendation"
        
        # 투표 결과 관련 질문
        elif any(keyword in question_lower for keyword in ["투표 결과", "투표 현황", "투표 상황", "어떻게 투표", "투표율"]):
            print("✅ Fallback classified as: vote_results")
            return "vote_results"
        
        # 개인 투표 이력 관련 질문
        elif any(keyword in question_lower for keyword in ["내가 투표", "내 투표", "내가 어떻게", "내 선택", "내가 뭘"]):
            print("✅ Fallback classified as: my_vote_history")
            return "my_vote_history"
        
        # 과거 회식 관련 질문
        elif any(keyword in question_lower for keyword in ["저번달", "지난달", "과거", "이전", "어디서", "어디에서"]):
            print("✅ Fallback classified as: past_dinner")
            return "past_dinner"
        
        else:
            print("✅ Fallback classified as: general")
            return "general"
    
    def _handle_vote_results_question(self, emp_no: str, question: str, context: Optional[Dict]) -> Dict[str, Any]:
        """투표 결과 질문 처리"""
        try:
            # 현재 월 투표 결과 조회
            current_month = datetime.now().strftime("%Y-%m")
            vote_results = self.vote_service.get_vote_results(current_month)
            
            # 투표 통계 생성
            total_votes = sum(vote_results.get("menu_votes", {}).values())
            menu_ranking = sorted(
                vote_results.get("menu_votes", {}).items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # LLM을 사용한 자연스러운 응답 생성
            context_data = {
                "vote_results": vote_results,
                "total_votes": total_votes,
                "menu_ranking": menu_ranking,
                "month": current_month
            }
            
            answer = self.ai_response_service.generate_llm_response(
                question, context_data, "vote_results"
            )
            
            return {
                "status": "S",
                "message": "투표 결과 조회 완료",
                "response_text": answer,
                "data": {
                    "vote_results": vote_results,
                    "total_votes": total_votes,
                    "menu_ranking": menu_ranking
                },
                "suggested_actions": ["투표하기", "식당 추천 받기"]
            }
            
        except Exception as e:
            return {
                "status": "E",
                "message": "투표 결과 조회 실패",
                "response_text": f"투표 결과를 조회하는 중 오류가 발생했습니다: {str(e)}"
            }
    
    def _handle_my_vote_history_question(self, emp_no: str, question: str, context: Optional[Dict]) -> Dict[str, Any]:
        """개인 투표 이력 질문 처리"""
        try:
            # 사용자 투표 이력 조회
            vote_history = self.vote_service.get_user_vote_history(emp_no)
            
            if not vote_history:
                return {
                    "status": "S",
                    "message": "투표 이력 조회 완료",
                    "response_text": "아직 투표 이력이 없습니다. 투표를 시작해보세요!",
                    "data": {"vote_history": []}
                }
            
            # 최근 투표 이력 분석
            recent_votes = vote_history[-1] if vote_history else None
            
            if recent_votes:
                menu_votes = recent_votes.get("menu_votes", [])
                date_votes = recent_votes.get("date_votes", [])
                
                answer = f"최근 투표 이력을 알려드리겠습니다. "
                answer += f"선택한 메뉴: {', '.join(menu_votes) if menu_votes else '없음'}, "
                answer += f"선호 날짜: {', '.join(date_votes) if date_votes else '없음'}"
            else:
                answer = "투표 이력이 없습니다."
            
            return {
                "status": "S",
                "message": "개인 투표 이력 조회 완료",
                "response_text": answer,
                "data": {
                    "vote_history": vote_history,
                    "recent_votes": recent_votes
                },
                "suggested_actions": ["투표 수정하기", "새로운 투표하기"]
            }
            
        except Exception as e:
            print(f"❌ Error in _handle_my_vote_history_question: {str(e)}")
            return {
                "status": "S",
                "message": "투표 이력 조회 완료",
                "response_text": "아직 투표 이력이 없습니다. 투표를 시작해보세요!"
            }
    
    def _handle_past_dinner_question(self, emp_no: str, question: str, context: Optional[Dict]) -> Dict[str, Any]:
        """과거 회식 질문 처리"""
        try:
            # 과거 회식 이력 조회 (최근 3개월)
            past_dinners = self.vote_service.get_past_dinner_history(emp_no, months=3)
            
            if not past_dinners:
                return {
                    "status": "S",
                    "message": "과거 회식 이력 조회 완료",
                    "response_text": "과거 회식 이력이 없습니다.",
                    "data": {"past_dinners": []}
                }
            
            # 최근 회식 정보
            latest_dinner = past_dinners[0]
            
            answer = f"최근 회식 정보를 알려드리겠습니다. "
            answer += f"{latest_dinner.get('month', '알 수 없음')}에 "
            answer += f"{latest_dinner.get('place_name', '알 수 없는 장소')}에서 "
            answer += f"{latest_dinner.get('menu_type', '알 수 없는 메뉴')}를 드셨습니다."
            
            return {
                "status": "S",
                "message": "과거 회식 이력 조회 완료",
                "response_text": answer,
                "data": {
                    "past_dinners": past_dinners,
                    "latest_dinner": latest_dinner
                },
                "suggested_actions": ["이번 달 투표하기", "식당 추천 받기"]
            }
            
        except Exception as e:
            return {
                "status": "E",
                "message": "과거 회식 이력 조회 실패",
                "response_text": f"과거 회식 이력을 조회하는 중 오류가 발생했습니다: {str(e)}"
            }
    
    def _handle_restaurant_recommendation_question(self, emp_no: str, question: str, context: Optional[Dict]) -> Dict[str, Any]:
        """식당 추천 질문 처리"""
        try:
            # 사용자 선호도 기반 추천
            user_preferences = self.vote_service.get_user_preferences(emp_no)
            
            if not user_preferences:
                return {
                    "status": "S",
                    "message": "식당 추천 조회 완료",
                    "response_text": "아직 선호도 정보가 없습니다. 투표를 통해 선호도를 설정해보세요!",
                    "data": {"recommendations": []}
                }
            
            # LLM을 사용한 자연스러운 응답 생성
            restaurant_suggestions = user_preferences.get("restaurant_suggestions", [])
            context_data = {
                "user_preferences": user_preferences,
                "restaurant_suggestions": restaurant_suggestions,
                "menu_votes": user_preferences.get("menu_votes", [])
            }
            
            answer = self.ai_response_service.generate_llm_response(
                question, context_data, "restaurant_recommendation"
            )
            
            return {
                "status": "S",
                "message": "식당 추천 조회 완료",
                "response_text": answer,
                "data": {
                    "user_preferences": user_preferences,
                    "recommendations": restaurant_suggestions
                },
                "suggested_actions": ["투표하기", "상세 추천 받기"]
            }
            
        except Exception as e:
            return {
                "status": "E",
                "message": "식당 추천 조회 실패",
                "response_text": f"식당 추천을 처리하는 중 오류가 발생했습니다: {str(e)}"
            }
    
    def _handle_general_question(self, emp_no: str, question: str, context: Optional[Dict]) -> Dict[str, Any]:
        """일반 질문 처리"""
        return {
            "status": "S",
            "message": "일반 질문 처리됨",
            "response_text": "죄송합니다. 해당 질문에 대한 답변을 준비하지 못했습니다. "
                           "투표 결과, 개인 투표 이력, 과거 회식 정보, 식당 추천에 대해 질문해주세요!",
            "action_required": "none",
            "data": {},
            "suggested_actions": ["투표하기", "식당 추천 받기", "투표 결과 보기"]
        }
    
    def _handle_vote_request_question(self, emp_no: str, question: str, context: Optional[Dict]) -> Dict[str, Any]:
        """투표 요청 질문 처리"""
        try:
            # LLM을 사용한 자연스러운 응답 생성
            context_data = {
                "question": question,
                "emp_no": emp_no
            }
            
            answer = self.ai_response_service.generate_llm_response(
                question, context_data, "vote_request"
            )
            
            # 투표 키워드가 포함되도록 강제 추가
            if "투표" not in answer:
                answer = f"네, 이번 달 투표를 도와드리겠습니다! {answer} 투표 창을 열어드릴게요."
            else:
                answer = f"네, {answer} 투표 창을 열어드릴게요."
            
            return {
                "status": "S",
                "message": "투표 요청 처리 완료",
                "response_text": answer,
                "action_required": "vote",
                "data": {
                    "emp_no": emp_no,
                    "question": question
                },
                "suggested_actions": ["투표하기", "투표 결과 보기"]
            }
            
        except Exception as e:
            return {
                "status": "E",
                "message": "투표 요청 처리 실패",
                "response_text": f"투표 요청을 처리하는 중 오류가 발생했습니다: {str(e)}",
                "action_required": "none"
            }
