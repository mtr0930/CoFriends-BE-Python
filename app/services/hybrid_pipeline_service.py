"""
Hybrid Pipeline Service - 실무 최적화 하이브리드 추천 시스템
"""
import asyncio
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
import logging
from datetime import datetime

from app.services.collaborative_filtering_service import CollaborativeFilteringService
from app.services.vector_db_service import VectorDBService
from app.services.lightrag_service import LightRAGService
from app.services.sse_manager import SSEManager

logger = logging.getLogger(__name__)

class HybridPipelineService:
    """하이브리드 파이프라인 서비스 - 실무 최적화"""
    
    def __init__(self):
        self.cf_service = CollaborativeFilteringService()
        self.vector_service = VectorDBService()
        self.lightrag_service = LightRAGService()
        self.sse_manager = SSEManager()
        
        logger.info("HybridPipelineService initialized")
    
    async def process_user_message(self, user_message: str, emp_no: str, client_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        사용자 메시지를 분석하고 적절한 파이프라인 실행
        
        Args:
            user_message: 사용자 메시지
            emp_no: 사용자 사번
            client_id: SSE 클라이언트 ID
            
        Yields:
            SSE 스트림 데이터
        """
        try:
            # 1. 메시지 분석
            task_type = await self._analyze_message(user_message)
            
            # 분석 결과를 SSE로 전송
            yield {
                "type": "analysis",
                "data": {
                    "message": user_message,
                    "task_type": task_type,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # 2. 작업 타입에 따른 파이프라인 실행
            if task_type == "reason_explanation":
                async for result in self._execute_reason_explanation_pipeline(user_message, emp_no, client_id):
                    yield result
                    
            elif task_type == "recommendation":
                async for result in self._execute_recommendation_pipeline(user_message, emp_no, client_id):
                    yield result
                    
            elif task_type == "general_chat":
                async for result in self._execute_general_chat_pipeline(user_message, emp_no, client_id):
                    yield result
                    
        except Exception as e:
            logger.error(f"Error processing user message: {str(e)}")
            yield {
                "type": "error",
                "data": {
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def _analyze_message(self, message: str) -> str:
        """
        사용자 메시지 분석하여 작업 타입 결정
        
        Args:
            message: 사용자 메시지
            
        Returns:
            작업 타입 ("reason_explanation", "recommendation", "general_chat")
        """
        message_lower = message.lower()
        
        # 추천 관련 키워드
        recommendation_keywords = [
            "추천", "recommend", "어디", "식당", "음식", "맛있는", "좋은",
            "회식", "점심", "저녁", "식사", "메뉴"
        ]
        
        # 설명 요청 키워드
        explanation_keywords = [
            "왜", "이유", "왜냐하면", "설명", "어떻게", "어떤", "기준",
            "근거", "이전", "과거", "패턴"
        ]
        
        # 키워드 매칭
        has_recommendation = any(keyword in message_lower for keyword in recommendation_keywords)
        has_explanation = any(keyword in message_lower for keyword in explanation_keywords)
        
        if has_recommendation and has_explanation:
            return "reason_explanation"  # 추천 + 설명
        elif has_recommendation:
            return "recommendation"  # 추천만
        elif has_explanation:
            return "reason_explanation"  # 설명만
        else:
            return "general_chat"  # 일반 대화
    
    async def _execute_reason_explanation_pipeline(self, message: str, emp_no: str, client_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        추천 이유 설명 파이프라인 (LightRAG 직접 호출)
        
        Args:
            message: 사용자 메시지
            emp_no: 사용자 사번
            client_id: SSE 클라이언트 ID
        """
        try:
            # 1. 사용자 컨텍스트 수집
            yield {
                "type": "pipeline_start",
                "data": {
                    "pipeline": "reason_explanation",
                    "message": "사용자 컨텍스트를 분석하고 있습니다...",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # 2. LightRAG를 통한 관계 분석
            user_context = self.lightrag_service.get_recommendation_context(emp_no, "dummy_item")
            
            yield {
                "type": "context_analysis",
                "data": {
                    "message": "사용자 선호도 패턴을 분석하고 있습니다...",
                    "context": user_context,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # 3. LLM을 통한 설명 생성
            explanation = self.lightrag_service.generate_explanation(emp_no, "dummy_item", user_context)
            
            yield {
                "type": "explanation_generated",
                "data": {
                    "message": "추천 이유를 분석했습니다.",
                    "explanation": explanation,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # 4. 최종 응답
            yield {
                "type": "pipeline_complete",
                "data": {
                    "pipeline": "reason_explanation",
                    "result": {
                        "explanation": explanation,
                        "user_context": user_context
                    },
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in reason explanation pipeline: {str(e)}")
            yield {
                "type": "pipeline_error",
                "data": {
                    "pipeline": "reason_explanation",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def _execute_recommendation_pipeline(self, message: str, emp_no: str, client_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        추천 파이프라인 (CF + Embedding)
        
        Args:
            message: 사용자 메시지
            emp_no: 사용자 사번
            client_id: SSE 클라이언트 ID
        """
        try:
            # 1. 협업 필터링 추천
            yield {
                "type": "pipeline_start",
                "data": {
                    "pipeline": "recommendation",
                    "message": "협업 필터링 추천을 생성하고 있습니다...",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            cf_recommendations = self.cf_service.get_hybrid_recommendations(emp_no, n_recommendations=5)
            
            yield {
                "type": "cf_recommendations",
                "data": {
                    "message": f"협업 필터링으로 {len(cf_recommendations)}개 추천을 생성했습니다.",
                    "recommendations": cf_recommendations,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # 2. 벡터 기반 개인화 추천
            yield {
                "type": "vector_processing",
                "data": {
                    "message": "개인화 추천을 생성하고 있습니다...",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            vector_recommendations = self.vector_service.get_personalized_recommendations(
                emp_no=emp_no,
                query_text=message
            )
            
            yield {
                "type": "vector_recommendations",
                "data": {
                    "message": f"개인화 추천으로 {len(vector_recommendations)}개 추천을 생성했습니다.",
                    "recommendations": vector_recommendations,
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # 3. 하이브리드 추천 통합
            yield {
                "type": "hybrid_integration",
                "data": {
                    "message": "하이브리드 추천을 통합하고 있습니다...",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # 추천 통합 로직
            combined_recommendations = self._combine_recommendations(cf_recommendations, vector_recommendations)
            
            yield {
                "type": "pipeline_complete",
                "data": {
                    "pipeline": "recommendation",
                    "result": {
                        "total_recommendations": len(combined_recommendations),
                        "recommendations": combined_recommendations,
                        "cf_count": len(cf_recommendations),
                        "vector_count": len(vector_recommendations)
                    },
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in recommendation pipeline: {str(e)}")
            yield {
                "type": "pipeline_error",
                "data": {
                    "pipeline": "recommendation",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    async def _execute_general_chat_pipeline(self, message: str, emp_no: str, client_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        일반 대화 파이프라인
        
        Args:
            message: 사용자 메시지
            emp_no: 사용자 사번
            client_id: SSE 클라이언트 ID
        """
        try:
            yield {
                "type": "pipeline_start",
                "data": {
                    "pipeline": "general_chat",
                    "message": "일반 대화를 처리하고 있습니다...",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # 간단한 응답 생성 (실제로는 LLM 사용)
            response = f"안녕하세요! '{message}'에 대해 말씀해주셨네요. 더 구체적인 추천이나 설명이 필요하시면 말씀해주세요!"
            
            yield {
                "type": "pipeline_complete",
                "data": {
                    "pipeline": "general_chat",
                    "result": {
                        "response": response
                    },
                    "timestamp": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error in general chat pipeline: {str(e)}")
            yield {
                "type": "pipeline_error",
                "data": {
                    "pipeline": "general_chat",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def _combine_recommendations(self, cf_recs: List[Dict], vector_recs: List[Dict]) -> List[Dict[str, Any]]:
        """
        협업 필터링과 벡터 추천 통합
        
        Args:
            cf_recs: 협업 필터링 추천
            vector_recs: 벡터 추천
            
        Returns:
            통합된 추천 리스트
        """
        try:
            combined_scores = {}
            
            # 협업 필터링 추천 (가중치: 0.6)
            for rec in cf_recs:
                item_id = rec.get("item_id")
                score = rec.get("score", 0)
                
                if item_id not in combined_scores:
                    combined_scores[item_id] = {
                        "item_id": item_id,
                        "score": 0,
                        "sources": [],
                        "metadata": {}
                    }
                
                combined_scores[item_id]["score"] += score * 0.6
                combined_scores[item_id]["sources"].append("collaborative_filtering")
                combined_scores[item_id]["metadata"]["cf_score"] = score
            
            # 벡터 추천 (가중치: 0.4)
            for rec in vector_recs:
                item_id = rec.get("metadata", {}).get("place_id")
                if not item_id:
                    continue
                
                score = rec.get("personalization_score", 0)
                
                if item_id not in combined_scores:
                    combined_scores[item_id] = {
                        "item_id": item_id,
                        "score": 0,
                        "sources": [],
                        "metadata": {}
                    }
                
                combined_scores[item_id]["score"] += score * 0.4
                combined_scores[item_id]["sources"].append("vector_similarity")
                combined_scores[item_id]["metadata"]["vector_score"] = score
            
            # 최종 추천 정렬
            final_recommendations = []
            for item_id, data in sorted(combined_scores.items(), key=lambda x: x[1]["score"], reverse=True):
                final_recommendations.append({
                    "item_id": item_id,
                    "score": data["score"],
                    "sources": data["sources"],
                    "metadata": data["metadata"],
                    "recommendation_type": "hybrid"
                })
            
            return final_recommendations[:10]  # 상위 10개만 반환
            
        except Exception as e:
            logger.error(f"Error combining recommendations: {str(e)}")
            return []
