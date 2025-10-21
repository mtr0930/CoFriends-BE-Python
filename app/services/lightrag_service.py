"""
LightRAG Service - 관계 기반 추천 설명 시스템
"""
import neo4j
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import logging
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.schema import Document
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class LightRAGService:
    """LightRAG 서비스 - 관계 기반 추천 설명"""
    
    def __init__(self, neo4j_uri: str = "bolt://localhost:7687", neo4j_user: str = "neo4j", neo4j_password: str = "password"):
        """
        LightRAG 서비스 초기화
        
        Args:
            neo4j_uri: Neo4j 데이터베이스 URI
            neo4j_user: Neo4j 사용자명
            neo4j_password: Neo4j 비밀번호
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        
        # Neo4j 드라이버 초기화
        try:
            self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            logger.info("Neo4j driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j driver: {str(e)}")
            self.driver = None
        
        # LLM 초기화
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0.7,
                max_tokens=500
            )
            logger.info("LLM initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            self.llm = None
    
    def create_entity_node(self, entity_type: str, entity_id: str, properties: Dict[str, Any]) -> bool:
        """
        엔티티 노드 생성
        
        Args:
            entity_type: 엔티티 타입 (User, Restaurant, Menu, etc.)
            entity_id: 엔티티 ID
            properties: 엔티티 속성
            
        Returns:
            생성 성공 여부
        """
        try:
            if not self.driver:
                logger.error("Neo4j driver not initialized")
                return False
            
            with self.driver.session() as session:
                # 노드 생성 또는 업데이트
                query = f"""
                MERGE (n:{entity_type} {{id: $entity_id}})
                SET n += $properties
                RETURN n
                """
                
                result = session.run(query, entity_id=entity_id, properties=properties)
                result.single()
                
                logger.info(f"Created/updated {entity_type} node: {entity_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error creating entity node: {str(e)}")
            return False
    
    def create_relationship(self, from_entity: str, to_entity: str, relationship_type: str, properties: Dict[str, Any] = None) -> bool:
        """
        엔티티 간 관계 생성
        
        Args:
            from_entity: 시작 엔티티 ID
            to_entity: 끝 엔티티 ID
            relationship_type: 관계 타입
            properties: 관계 속성
            
        Returns:
            생성 성공 여부
        """
        try:
            if not self.driver:
                logger.error("Neo4j driver not initialized")
                return False
            
            with self.driver.session() as session:
                # 관계 생성 또는 업데이트
                query = f"""
                MATCH (a {{id: $from_entity}})
                MATCH (b {{id: $to_entity}})
                MERGE (a)-[r:{relationship_type}]->(b)
                SET r += $properties
                RETURN r
                """
                
                result = session.run(query, from_entity=from_entity, to_entity=to_entity, properties=properties or {})
                result.single()
                
                logger.info(f"Created relationship: {from_entity} -[{relationship_type}]-> {to_entity}")
                return True
                
        except Exception as e:
            logger.error(f"Error creating relationship: {str(e)}")
            return False
    
    def build_vote_graph(self, votes_data: List[Dict[str, Any]]) -> bool:
        """
        투표 데이터로부터 그래프 구축
        
        Args:
            votes_data: 투표 데이터 리스트
            
        Returns:
            구축 성공 여부
        """
        try:
            if not self.driver:
                logger.error("Neo4j driver not initialized")
                return False
            
            with self.driver.session() as session:
                # 기존 데이터 삭제 (선택사항)
                session.run("MATCH (n) DETACH DELETE n")
                
                # 투표 데이터 처리
                for vote in votes_data:
                    user_id = vote.get("emp_no")
                    place_id = vote.get("place_id")
                    menu_type = vote.get("menu_type")
                    vote_action = vote.get("action", "like")
                    vote_date = vote.get("date")
                    
                    # 사용자 노드 생성
                    self.create_entity_node(
                        "User", 
                        user_id, 
                        {
                            "name": f"User_{user_id}",
                            "created_at": datetime.now().isoformat()
                        }
                    )
                    
                    # 식당 노드 생성
                    self.create_entity_node(
                        "Restaurant", 
                        str(place_id), 
                        {
                            "name": vote.get("place_name", f"Restaurant_{place_id}"),
                            "menu_type": menu_type,
                            "created_at": datetime.now().isoformat()
                        }
                    )
                    
                    # 메뉴 타입 노드 생성
                    if menu_type:
                        self.create_entity_node(
                            "MenuType", 
                            menu_type, 
                            {
                                "name": menu_type,
                                "created_at": datetime.now().isoformat()
                            }
                        )
                    
                    # 관계 생성
                    # 사용자 -[VOTED]-> 식당
                    self.create_relationship(
                        user_id, 
                        str(place_id), 
                        "VOTED",
                        {
                            "action": vote_action,
                            "date": vote_date,
                            "created_at": datetime.now().isoformat()
                        }
                    )
                    
                    # 식당 -[SERVES]-> 메뉴타입
                    if menu_type:
                        self.create_relationship(
                            str(place_id), 
                            menu_type, 
                            "SERVES",
                            {
                                "created_at": datetime.now().isoformat()
                            }
                        )
                
                logger.info(f"Built vote graph with {len(votes_data)} votes")
                return True
                
        except Exception as e:
            logger.error(f"Error building vote graph: {str(e)}")
            return False
    
    def find_related_entities(self, entity_id: str, entity_type: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        관련 엔티티 찾기
        
        Args:
            entity_id: 엔티티 ID
            entity_type: 엔티티 타입
            max_depth: 최대 탐색 깊이
            
        Returns:
            관련 엔티티 리스트
        """
        try:
            if not self.driver:
                logger.error("Neo4j driver not initialized")
                return []
            
            with self.driver.session() as session:
                # 관련 엔티티 찾기
                query = f"""
                MATCH (start:{entity_type} {{id: $entity_id}})
                MATCH path = (start)-[*1..{max_depth}]-(related)
                RETURN DISTINCT related, length(path) as distance
                ORDER BY distance
                LIMIT 20
                """
                
                result = session.run(query, entity_id=entity_id)
                related_entities = []
                
                for record in result:
                    entity = record["related"]
                    distance = record["distance"]
                    
                    related_entities.append({
                        "id": entity.get("id"),
                        "labels": list(entity.labels),
                        "properties": dict(entity),
                        "distance": distance
                    })
                
                logger.info(f"Found {len(related_entities)} related entities for {entity_type}:{entity_id}")
                return related_entities
                
        except Exception as e:
            logger.error(f"Error finding related entities: {str(e)}")
            return []
    
    def get_recommendation_context(self, user_id: str, recommended_item_id: str) -> Dict[str, Any]:
        """
        추천 컨텍스트 생성
        
        Args:
            user_id: 사용자 ID
            recommended_item_id: 추천 아이템 ID
            
        Returns:
            추천 컨텍스트
        """
        try:
            if not self.driver:
                logger.error("Neo4j driver not initialized")
                return {}
            
            with self.driver.session() as session:
                # 사용자의 과거 투표 패턴
                user_votes_query = """
                MATCH (u:User {id: $user_id})-[:VOTED]->(r:Restaurant)
                RETURN r.name as restaurant_name, r.menu_type as menu_type, 
                       collect(u.action) as actions, count(*) as vote_count
                ORDER BY vote_count DESC
                LIMIT 5
                """
                
                user_votes = session.run(user_votes_query, user_id=user_id)
                user_vote_history = [dict(record) for record in user_votes]
                
                # 추천 아이템의 관련 정보
                item_context_query = """
                MATCH (r:Restaurant {id: $item_id})
                OPTIONAL MATCH (r)-[:SERVES]->(m:MenuType)
                OPTIONAL MATCH (similar:User)-[:VOTED]->(r)
                RETURN r.name as restaurant_name, r.menu_type as menu_type,
                       collect(DISTINCT m.name) as menu_types,
                       count(DISTINCT similar) as similar_users
                """
                
                item_context = session.run(item_context_query, item_id=recommended_item_id)
                item_info = dict(item_context.single()) if item_context.single() else {}
                
                # 유사한 사용자들의 선호도
                similar_users_query = """
                MATCH (u:User {id: $user_id})-[:VOTED]->(r:Restaurant)<-[:VOTED]-(similar:User)
                MATCH (similar)-[:VOTED]->(other:Restaurant)
                WHERE other.id <> $item_id
                RETURN other.name as restaurant_name, other.menu_type as menu_type,
                       count(DISTINCT similar) as similar_user_count
                ORDER BY similar_user_count DESC
                LIMIT 3
                """
                
                similar_preferences = session.run(similar_users_query, user_id=user_id, item_id=recommended_item_id)
                similar_prefs = [dict(record) for record in similar_preferences]
                
                context = {
                    "user_vote_history": user_vote_history,
                    "recommended_item": item_info,
                    "similar_user_preferences": similar_prefs,
                    "generated_at": datetime.now().isoformat()
                }
                
                logger.info(f"Generated recommendation context for user {user_id}")
                return context
                
        except Exception as e:
            logger.error(f"Error generating recommendation context: {str(e)}")
            return {}
    
    def generate_explanation(self, user_id: str, recommended_item_id: str, context: Dict[str, Any]) -> str:
        """
        추천 설명 생성
        
        Args:
            user_id: 사용자 ID
            recommended_item_id: 추천 아이템 ID
            context: 추천 컨텍스트
            
        Returns:
            추천 설명 텍스트
        """
        try:
            if not self.llm:
                logger.error("LLM not initialized")
                return "추천 설명을 생성할 수 없습니다."
            
            # 프롬프트 구성
            prompt = f"""
            다음 정보를 바탕으로 추천 이유를 자연스러운 한국어로 설명해주세요:
            
            사용자 ID: {user_id}
            추천 아이템: {context.get('recommended_item', {}).get('restaurant_name', 'Unknown')}
            
            사용자 투표 이력:
            {json.dumps(context.get('user_vote_history', []), ensure_ascii=False, indent=2)}
            
            추천 아이템 정보:
            {json.dumps(context.get('recommended_item', {}), ensure_ascii=False, indent=2)}
            
            유사한 사용자들의 선호도:
            {json.dumps(context.get('similar_user_preferences', []), ensure_ascii=False, indent=2)}
            
            다음 형식으로 설명해주세요:
            1. 사용자의 과거 선호도 패턴
            2. 추천 아이템의 특징
            3. 유사한 사용자들의 선호도
            4. 최종 추천 이유
            
            친근하고 자연스러운 톤으로 작성해주세요.
            """
            
            # LLM으로 설명 생성
            response = self.llm.invoke(prompt)
            explanation = response.content
            
            logger.info(f"Generated explanation for user {user_id}")
            return explanation
            
        except Exception as e:
            logger.error(f"Error generating explanation: {str(e)}")
            return f"추천 설명 생성 중 오류가 발생했습니다: {str(e)}"
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        그래프 통계 정보 조회
        
        Returns:
            그래프 통계
        """
        try:
            if not self.driver:
                logger.error("Neo4j driver not initialized")
                return {}
            
            with self.driver.session() as session:
                # 노드 수 조회
                node_counts = session.run("""
                    MATCH (n)
                    RETURN labels(n) as label, count(n) as count
                    ORDER BY count DESC
                """)
                
                # 관계 수 조회
                relationship_counts = session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as relationship_type, count(r) as count
                    ORDER BY count DESC
                """)
                
                # 전체 통계
                total_stats = session.run("""
                    MATCH (n)
                    RETURN count(n) as total_nodes
                    UNION ALL
                    MATCH ()-[r]->()
                    RETURN count(r) as total_relationships
                """)
                
                stats = {
                    "node_counts": [dict(record) for record in node_counts],
                    "relationship_counts": [dict(record) for record in relationship_counts],
                    "total_stats": [dict(record) for record in total_stats]
                }
                
                logger.info("Retrieved graph statistics")
                return stats
                
        except Exception as e:
            logger.error(f"Error getting graph statistics: {str(e)}")
            return {}
    
    def close(self):
        """Neo4j 드라이버 종료"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j driver closed")
