"""
AI 응답 생성 서비스 - LLM 통합
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
import json

from app.tools.mcp_tools import MCPTools
from app.services.bedrock_service import BedrockService


class AIResponseService:
    """AI 응답 생성 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.mcp_tools = MCPTools(db)
        self.bedrock_service = BedrockService()
    
    def generate_llm_response(self, question: str, context_data: Dict[str, Any], question_type: str) -> str:
        """
        LLM을 사용한 자연스러운 응답 생성
        
        Args:
            question: 사용자 질문
            context_data: 컨텍스트 데이터 (투표 결과, 식당 추천 등)
            question_type: 질문 유형
            
        Returns:
            LLM 생성된 자연스러운 응답
        """
        try:
            # 시스템 프롬프트 설정
            system_prompt = f"""
당신은 회식 투표 시스템의 AI 어시스턴트입니다.
사용자의 질문에 대해 친근하고 도움이 되는 답변을 제공해주세요.

질문 유형: {question_type}
사용자 질문: {question}

컨텍스트 데이터:
{json.dumps(context_data, ensure_ascii=False, indent=2)}

다음 지침을 따라 답변해주세요:
1. 친근하고 자연스러운 톤으로 답변
2. 데이터가 없으면 "아직 데이터가 없습니다"라고 명확히 안내
3. 구체적인 정보가 있으면 상세히 설명
4. 다음 단계나 추천 액션 제시
5. 한국어로 답변
"""
            
            # AWS Bedrock을 사용한 실제 LLM 호출 (Fallback 제거)
            bedrock_result = self.bedrock_service.generate_response(system_prompt)
            if bedrock_result["success"]:
                return bedrock_result["response"]
            else:
                print(f"❌ Bedrock error: {bedrock_result.get('error')}")
                return f"죄송합니다. AI 서비스에 연결할 수 없습니다. (에러: {bedrock_result.get('error', 'Unknown error')})"
            
        except Exception as e:
            print(f"❌ Error in generate_llm_response: {str(e)}")
            return "죄송합니다. 응답을 생성하는 중 오류가 발생했습니다."
    
    def _generate_template_response(self, question: str, context_data: Dict[str, Any], question_type: str) -> str:
        """템플릿 기반 응답 생성 (LLM 대체)"""
        
        if question_type == "vote_results":
            vote_results = context_data.get("vote_results", {})
            total_votes = context_data.get("total_votes", 0)
            menu_ranking = context_data.get("menu_ranking", [])
            
            if total_votes == 0:
                return "아직 투표가 시작되지 않았습니다. 투표를 시작해보세요!"
            
            response = f"이번 달 투표 결과를 알려드리겠습니다! 총 {total_votes}명이 참여했어요. "
            if menu_ranking:
                response += f"1위는 {menu_ranking[0][0]}({menu_ranking[0][1]}표)입니다."
                if len(menu_ranking) > 1:
                    response += f" 2위는 {menu_ranking[1][0]}({menu_ranking[1][1]}표)입니다."
            return response
            
        elif question_type == "my_vote_history":
            vote_history = context_data.get("vote_history", [])
            if not vote_history:
                return "아직 투표 이력이 없습니다. 투표를 시작해보세요!"
            
            recent_votes = vote_history[-1] if vote_history else None
            if recent_votes:
                menu_votes = recent_votes.get("menu_votes", [])
                date_votes = recent_votes.get("date_votes", [])
                
                response = "최근 투표 이력을 알려드리겠습니다. "
                if menu_votes:
                    response += f"선택한 메뉴: {', '.join(menu_votes)} "
                if date_votes:
                    response += f"선호 날짜: {', '.join(date_votes)}"
                return response
            return "투표 이력이 없습니다."
            
        elif question_type == "restaurant_recommendation":
            restaurant_suggestions = context_data.get("restaurant_suggestions", [])
            if restaurant_suggestions:
                restaurant_names = [suggestion.get("name", "") for suggestion in restaurant_suggestions]
                return f"이번 달 추천 식당을 알려드리겠습니다! 추천 식당: {', '.join(restaurant_names)}"
            return "아직 추천 식당이 없습니다. 투표를 통해 선호도를 설정하고 추천을 받아보세요!"
            
        elif question_type == "past_dinner":
            return "과거 회식 이력이 없습니다."
            
        elif question_type == "vote_request":
            return "네, 이번 달 투표를 도와드리겠습니다! 투표 창을 열어드릴게요. 메뉴와 날짜를 선택해주세요."
            
        else:
            return "죄송합니다. 해당 질문에 대한 답변을 준비하지 못했습니다. 투표 결과, 개인 투표 이력, 과거 회식 정보, 식당 추천에 대해 질문해주세요!"
    
    def generate_vote_summary(self, vote_data: Dict[str, Any]) -> str:
        """
        투표 결과 요약 생성
        
        Args:
            vote_data: 투표 데이터
            
        Returns:
            AI 생성된 투표 요약
        """
        try:
            month = vote_data.get("month", "알 수 없는 월")
            total_votes = vote_data.get("total_votes", 0)
            menu_ranking = vote_data.get("menu_ranking", [])
            
            if not menu_ranking:
                return f"{month} 투표 결과가 아직 없습니다. 투표를 시작해보세요!"
            
            # 1위 메뉴 정보
            top_menu = menu_ranking[0]
            top_menu_name = top_menu[0]
            top_menu_votes = top_menu[1]
            
            # AI 응답 생성
            response = f"이번 달({month}) 투표 결과를 알려드리겠습니다! "
            response += f"총 {total_votes}명이 투표했으며, "
            response += f"{top_menu_name}이 {top_menu_votes}표로 1위를 차지했습니다. "
            
            # 2위, 3위 정보 추가
            if len(menu_ranking) > 1:
                second_menu = menu_ranking[1]
                response += f"2위는 {second_menu[0]}({second_menu[1]}표)입니다. "
            
            if len(menu_ranking) > 2:
                third_menu = menu_ranking[2]
                response += f"3위는 {third_menu[0]}({third_menu[1]}표)입니다. "
            
            # 투표율 정보 추가
            vote_rate = (total_votes / 100) * 100  # 가정: 100명 기준
            response += f"현재 투표율은 {vote_rate:.1f}%입니다. "
            
            return response
            
        except Exception as e:
            return f"투표 결과를 분석하는 중 오류가 발생했습니다: {str(e)}"
    
    def generate_personal_vote_summary(self, user_data: Dict[str, Any]) -> str:
        """
        개인 투표 이력 요약 생성
        
        Args:
            user_data: 사용자 투표 데이터
            
        Returns:
            AI 생성된 개인 투표 요약
        """
        try:
            emp_no = user_data.get("emp_no", "알 수 없는 사용자")
            vote_history = user_data.get("vote_history", [])
            recent_votes = user_data.get("recent_votes")
            
            if not recent_votes:
                return f"{emp_no}님의 투표 이력이 없습니다. 투표를 시작해보세요!"
            
            # 최근 투표 분석
            menu_votes = recent_votes.get("menu_votes", [])
            date_votes = recent_votes.get("date_votes", [])
            
            response = f"{emp_no}님의 최근 투표 이력을 알려드리겠습니다. "
            
            if menu_votes:
                response += f"선택한 메뉴: {', '.join(menu_votes)}. "
            else:
                response += "선택한 메뉴가 없습니다. "
            
            if date_votes:
                response += f"선호 날짜: {', '.join(date_votes)}. "
            else:
                response += "선호 날짜가 없습니다. "
            
            # 총 투표 횟수
            total_votes = len(vote_history)
            response += f"총 {total_votes}번 투표하셨습니다."
            
            return response
            
        except Exception as e:
            return f"개인 투표 이력을 분석하는 중 오류가 발생했습니다: {str(e)}"
    
    def generate_past_dinner_summary(self, dinner_data: Dict[str, Any]) -> str:
        """
        과거 회식 요약 생성
        
        Args:
            dinner_data: 회식 데이터
            
        Returns:
            AI 생성된 과거 회식 요약
        """
        try:
            emp_no = dinner_data.get("emp_no", "알 수 없는 사용자")
            past_dinners = dinner_data.get("past_dinners", [])
            latest_dinner = dinner_data.get("latest_dinner")
            
            if not latest_dinner:
                return f"{emp_no}님의 과거 회식 이력이 없습니다."
            
            # 최근 회식 정보
            place_name = latest_dinner.get("place_name", "알 수 없는 장소")
            menu_type = latest_dinner.get("menu_type", "알 수 없는 메뉴")
            month = latest_dinner.get("month", "알 수 없는 월")
            
            response = f"{emp_no}님의 최근 회식 정보를 알려드리겠습니다. "
            response += f"{month}에 {place_name}에서 {menu_type}을 드셨습니다. "
            
            # 총 회식 횟수
            total_dinners = len(past_dinners)
            response += f"총 {total_dinners}번의 회식 이력이 있습니다."
            
            return response
            
        except Exception as e:
            return f"과거 회식 이력을 분석하는 중 오류가 발생했습니다: {str(e)}"
    
    def generate_restaurant_recommendation(self, recommendation_data: Dict[str, Any]) -> str:
        """
        식당 추천 생성
        
        Args:
            recommendation_data: 추천 데이터
            
        Returns:
            AI 생성된 식당 추천
        """
        try:
            emp_no = recommendation_data.get("emp_no", "알 수 없는 사용자")
            menu_types = recommendation_data.get("menu_types", [])
            recommendations = recommendation_data.get("recommendations", [])
            
            if not recommendations:
                return f"{emp_no}님의 선호도에 맞는 식당 추천이 없습니다. 투표를 통해 선호도를 설정해보세요!"
            
            # 선호 메뉴 타입 기반 추천
            response = f"{emp_no}님의 선호 메뉴 타입({', '.join(menu_types)})을 기반으로 추천드리겠습니다. "
            
            # 상위 추천 식당들
            top_recommendations = recommendations[:3]  # 상위 3개
            
            for i, restaurant in enumerate(top_recommendations, 1):
                place_name = restaurant.get("place_name", "알 수 없는 식당")
                menu_type = restaurant.get("menu_type", "알 수 없는 메뉴")
                address = restaurant.get("address", "주소 정보 없음")
                
                response += f"{i}. {place_name} ({menu_type}) - {address}. "
            
            response += "더 자세한 추천을 받으려면 투표를 완료해주세요!"
            
            return response
            
        except Exception as e:
            return f"식당 추천을 생성하는 중 오류가 발생했습니다: {str(e)}"
    
    def generate_conversational_response(self, question: str, context: Dict[str, Any]) -> str:
        """
        대화형 응답 생성
        
        Args:
            question: 사용자 질문
            context: 컨텍스트 정보
            
        Returns:
            AI 생성된 대화형 응답
        """
        try:
            # 질문 유형별 응답 생성
            if "투표 결과" in question or "투표 현황" in question:
                vote_data = self.mcp_tools.get_vote_results(context.get("month", "2025-10"))
                return self.generate_vote_summary(vote_data)
            
            elif "내가 투표" in question or "내 투표" in question:
                user_data = self.mcp_tools.get_user_vote_history(context.get("emp_no", "84927"))
                return self.generate_personal_vote_summary(user_data)
            
            elif "저번달" in question or "과거" in question:
                dinner_data = self.mcp_tools.get_past_dinner_info(context.get("emp_no", "84927"))
                return self.generate_past_dinner_summary(dinner_data)
            
            elif "추천" in question or "식당" in question:
                recommendation_data = self.mcp_tools.get_restaurant_recommendations(
                    context.get("emp_no", "84927")
                )
                return self.generate_restaurant_recommendation(recommendation_data)
            
            else:
                return "죄송합니다. 해당 질문에 대한 답변을 준비하지 못했습니다. " \
                       "투표 결과, 개인 투표 이력, 과거 회식 정보, 식당 추천에 대해 질문해주세요!"
                
        except Exception as e:
            return f"대화형 응답을 생성하는 중 오류가 발생했습니다: {str(e)}"
