#!/usr/bin/env python3
"""
AWS Bedrock Mock 테스트 - 실제 AWS 자격 증명 없이 테스트
"""
import json
import os
from unittest.mock import Mock, patch

def test_bedrock_mock():
    """Bedrock Mock 테스트"""
    
    print("AWS Bedrock Mock Test")
    print("=" * 50)
    
    # Mock AWS 자격 증명 설정
    mock_credentials = {
        'AWS_ACCESS_KEY_ID': 'mock_access_key',
        'AWS_SECRET_ACCESS_KEY': 'mock_secret_key',
        'AWS_REGION': 'us-east-1',
        'BEDROCK_MODEL_ID': 'anthropic.claude-3-haiku-20240307-v1:0'
    }
    
    # 환경 변수 설정
    for key, value in mock_credentials.items():
        os.environ[key] = value
    
    print(f"Region: {mock_credentials['AWS_REGION']}")
    print(f"Model: {mock_credentials['BEDROCK_MODEL_ID']}")
    print(f"Access Key: {mock_credentials['AWS_ACCESS_KEY_ID'][:10]}...")
    print("-" * 50)
    
    try:
        # BedrockService import 및 테스트
        from app.services.bedrock_service import BedrockService
        
        print("Testing BedrockService initialization...")
        
        # Mock boto3 client
        with patch('boto3.client') as mock_boto_client:
            # Mock response 설정
            mock_response = {
                'body': Mock(),
                'contentType': 'application/json'
            }
            
            # Mock response body 설정
            mock_response_body = {
                'content': [
                    {
                        'text': '안녕하세요! 테스트 응답입니다. Bedrock이 정상적으로 작동하고 있습니다.'
                    }
                ],
                'usage': {
                    'input_tokens': 10,
                    'output_tokens': 20
                }
            }
            
            # Mock response body read 메서드 설정
            mock_response['body'].read.return_value = json.dumps(mock_response_body).encode('utf-8')
            
            # Mock boto3 client 설정
            mock_bedrock_client = Mock()
            mock_bedrock_client.invoke_model.return_value = mock_response
            mock_boto_client.return_value = mock_bedrock_client
            
            # BedrockService 초기화
            service = BedrockService()
            
            print("BedrockService initialized successfully")
            
            # 연결 테스트
            print("Testing connection...")
            connection_result = service.test_connection()
            
            if connection_result["success"]:
                print("SUCCESS! Connection test passed")
                print(f"Test response: {connection_result.get('test_response', 'No response')}")
            else:
                print(f"Connection test failed: {connection_result.get('message', 'Unknown error')}")
                return False
            
            # 실제 응답 생성 테스트
            print("Testing response generation...")
            test_prompt = "안녕하세요! 간단한 인사말을 해주세요."
            result = service.generate_response(test_prompt, max_tokens=100)
            
            if result["success"]:
                print("SUCCESS! Response generation test passed")
                print(f"AI Response: {result['response']}")
                print(f"Model: {result.get('model', 'Unknown')}")
                print(f"Usage: {result.get('usage', {})}")
                return True
            else:
                print(f"Response generation failed: {result.get('error', 'Unknown error')}")
                return False
                
    except ImportError as e:
        print(f"Import error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    print("AWS Bedrock Mock Test")
    print("=" * 50)
    
    success = test_bedrock_mock()
    
    if success:
        print("Test PASSED - Bedrock service is working!")
    else:
        print("Test FAILED - Bedrock service has issues")
    
    print("=" * 50)
