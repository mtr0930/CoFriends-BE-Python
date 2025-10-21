#!/usr/bin/env python3
"""
AWS Bedrock 직접 호출 테스트
"""
import json
import boto3
import os
from botocore.exceptions import ClientError, NoCredentialsError
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def test_bedrock_direct():
    """Bedrock 직접 호출 테스트"""
    
    # AWS 자격 증명 - 환경 변수에서 가져오기
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    region = "us-east-1"  # ap-northeast-2에서 모델 지원 문제로 us-east-1 사용
    model_id = "anthropic.claude-3-haiku-20240307-v1:0"  # 지원되는 모델 사용
    
    if not access_key or not secret_key:
        raise ValueError("AWS credentials not found. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables")
    
    print(f"Testing AWS Bedrock Direct Call")
    print(f"Region: {region}")
    print(f"Model: {model_id}")
    print(f"Access Key: {access_key[:10]}...")
    print("-" * 50)
    
    try:
        # Bedrock 클라이언트 생성
        bedrock_client = boto3.client(
            'bedrock-runtime',
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )
        print("Bedrock client created successfully")
        
        # 테스트 프롬프트
        test_prompt = "안녕하세요! 간단한 인사말을 해주세요."
        
        # Claude 3.5 Sonnet 모델용 요청 형식
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": [
                {
                    "role": "user",
                    "content": test_prompt
                }
            ]
        }
        
        print(f"Sending prompt: {test_prompt}")
        print(f"Request body: {json.dumps(request_body, indent=2)}")
        print("-" * 50)
        
        # Bedrock 모델 호출
        response = bedrock_client.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body),
            contentType='application/json'
        )
        
        print("Bedrock model invoked successfully")
        
        # 응답 파싱
        response_body = json.loads(response['body'].read())
        print(f"Raw response: {json.dumps(response_body, indent=2, ensure_ascii=False)}")
        
        if 'content' in response_body and len(response_body['content']) > 0:
            ai_response = response_body['content'][0]['text']
            print("-" * 50)
            print(f"SUCCESS! AI Response:")
            print(f"{ai_response}")
            print("-" * 50)
            return True
        else:
            print("No content in response")
            return False
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"AWS Bedrock ClientError:")
        print(f"   Code: {error_code}")
        print(f"   Message: {error_message}")
        return False
        
    except NoCredentialsError:
        print("AWS credentials not found")
        return False
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    print("AWS Bedrock Direct Call Test")
    print("=" * 50)
    
    success = test_bedrock_direct()
    
    if success:
        print("Test PASSED - Bedrock is working!")
    else:
        print("Test FAILED - Bedrock has issues")
    
    print("=" * 50)
