"""
AWS Bedrock 서비스 - LLM API 호출
"""
import json
import boto3
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError, NoCredentialsError
import os

class BedrockService:
    """AWS Bedrock 서비스"""
    
    def __init__(self):
        # 환경 변수 디버깅
        aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
        aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        aws_region = os.getenv('AWS_REGION')
        model_id = os.getenv('BEDROCK_MODEL_ID')
        
        print(f"🔍 Environment Variables Debug:")
        print(f"   AWS_ACCESS_KEY_ID: {aws_access_key[:10] if aws_access_key else 'None'}...")
        print(f"   AWS_SECRET_ACCESS_KEY: {aws_secret_key[:10] if aws_secret_key else 'None'}...")
        print(f"   AWS_REGION: {aws_region}")
        print(f"   BEDROCK_MODEL_ID: {model_id}")
        
        # 환경 변수가 없으면 하드코딩된 값 사용
        self.region = aws_region or 'us-east-1'
        self.model_id = model_id or 'anthropic.claude-3-haiku-20240307-v1:0'  # 경량 모델
        
        # 환경 변수가 제대로 로드되지 않으면 에러 발생
        if not aws_access_key or not aws_secret_key:
            raise ValueError("AWS credentials not found in environment variables. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        
        # 잘못된 모델 ID 강제 수정
        if "claude-sonnet-4" in self.model_id or "claude-3-5" in self.model_id:
            print("⚠️ Invalid model ID detected, forcing correct model")
            self.model_id = "anthropic.claude-3-haiku-20240307-v1:0"  # 경량 모델
            self.region = "us-east-1"
        
        # AWS 자격 증명 설정
        try:
            self.bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name=self.region,
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key
            )
            print(f"✅ AWS Bedrock client initialized in region: {self.region}")
            print(f"✅ Using model: {self.model_id}")
        except NoCredentialsError:
            print("❌ AWS credentials not found")
            self.bedrock_client = None
        except Exception as e:
            print(f"❌ Error initializing Bedrock client: {str(e)}")
            self.bedrock_client = None
    
    def generate_response(self, prompt: str, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Bedrock을 사용한 LLM 응답 생성
        
        Args:
            prompt: 입력 프롬프트
            max_tokens: 최대 토큰 수
            
        Returns:
            LLM 응답 결과
        """
        if not self.bedrock_client:
            return {
                "success": False,
                "error": "Bedrock client not initialized",
                "response": "죄송합니다. AI 서비스에 연결할 수 없습니다."
            }
        
        try:
            # Claude 3 Sonnet 모델용 요청 형식
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            print(f"🚀 Sending request to Bedrock: {self.model_id}")
            print(f"📝 Prompt: {prompt[:100]}...")
            
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps(request_body),
                contentType='application/json'
            )
            
            # 응답 파싱
            response_body = json.loads(response['body'].read())
            
            if 'content' in response_body and len(response_body['content']) > 0:
                ai_response = response_body['content'][0]['text']
                print(f"✅ Bedrock response received: {ai_response[:100]}...")
                
                return {
                    "success": True,
                    "response": ai_response,
                    "model": self.model_id,
                    "usage": response_body.get('usage', {})
                }
            else:
                return {
                    "success": False,
                    "error": "No content in response",
                    "response": "죄송합니다. AI 응답을 생성할 수 없습니다."
                }
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            print(f"❌ AWS Bedrock ClientError: {error_code} - {error_message}")
            
            return {
                "success": False,
                "error": f"AWS Error: {error_code}",
                "response": "죄송합니다. AI 서비스에 일시적인 문제가 발생했습니다."
            }
            
        except Exception as e:
            print(f"❌ Unexpected error in Bedrock: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response": "죄송합니다. 예상치 못한 오류가 발생했습니다."
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """Bedrock 연결 테스트"""
        if not self.bedrock_client:
            return {
                "success": False,
                "message": "Bedrock client not initialized"
            }
        
        try:
            # 간단한 테스트 요청
            test_prompt = "안녕하세요! 간단한 인사말을 해주세요."
            result = self.generate_response(test_prompt, max_tokens=50)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": "Bedrock connection successful",
                    "test_response": result["response"]
                }
            else:
                return {
                    "success": False,
                    "message": f"Bedrock test failed: {result.get('error', 'Unknown error')}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Bedrock test error: {str(e)}"
            }
