# AWS Secrets Manager 설정 가이드

이 프로젝트는 AWS Secrets Manager를 사용하여 프로덕션 환경에서 민감한 정보를 안전하게 관리합니다.

## 필요한 AWS Secrets

### 1. Slack 설정 (Secret ID: `prod/buildpechatbot/slack`)

다음 JSON 형식으로 AWS Secrets Manager에 저장:

```json
{
  "CLIENT_ID": "your_slack_client_id",
  "CLIENT_SECRET": "your_slack_client_secret",
  "REDIRECT_URI": "https://buildpechatbot.com/auth/slack/callback"
}
```

### 2. AWS Bedrock 설정 (Secret ID: `prod/buildpechatbot/bedrock`)

다음 JSON 형식으로 AWS Secrets Manager에 저장:

```json
{
  "ACCESS_KEY_ID": "your_aws_access_key_id",
  "SECRET_ACCESS_KEY": "your_aws_secret_access_key",
  "REGION": "ap-northeast-2",
  "MODEL_ID": "anthropic.claude-3-haiku-20240307-v1:0"
}
```

## AWS CLI를 사용한 Secret 생성

### Slack Secret 생성
```bash
aws secretsmanager create-secret \
    --name "prod/buildpechatbot/slack" \
    --description "Slack API credentials for CoFriends" \
    --secret-string '{"CLIENT_ID":"your_slack_client_id","CLIENT_SECRET":"your_slack_client_secret","REDIRECT_URI":"https://buildpechatbot.com/auth/slack/callback"}'
```

### Bedrock Secret 생성
```bash
aws secretsmanager create-secret \
    --name "prod/buildpechatbot/bedrock" \
    --description "AWS Bedrock credentials for CoFriends" \
    --secret-string '{"ACCESS_KEY_ID":"your_aws_access_key_id","SECRET_ACCESS_KEY":"your_aws_secret_access_key","REGION":"ap-northeast-2","MODEL_ID":"anthropic.claude-3-haiku-20240307-v1:0"}'
```

## EC2 IAM Role 설정 (권장)

### 1. EC2 인스턴스에 IAM Role 할당
1. AWS 콘솔 → EC2 → 인스턴스 → Actions → Security → Modify IAM role
2. IAM Role 생성 또는 기존 역할 선택

### 2. IAM Role에 다음 권한 추가
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": [
        "arn:aws:secretsmanager:ap-northeast-2:*:secret:prod/buildpechatbot/slack*",
        "arn:aws:secretsmanager:ap-northeast-2:*:secret:prod/buildpechatbot/bedrock*"
      ]
    }
  ]
}
```

### 3. Jenkinsfile 설정
IAM Role을 사용하므로 Jenkins에서 AWS 자격 증명 설정이 불필요합니다:

```groovy
environment {
    AWS_DEFAULT_REGION = 'ap-northeast-2'
    // IAM Role을 사용하므로 AWS 자격 증명 설정 불필요
}
```

## 환경별 동작

- **로컬 환경** (`ENVIRONMENT=local`): 
  - `.env` 파일에서 환경변수 로드
  - CORS Origins: `http://localhost:3000,http://localhost:5173`
- **프로덕션 환경** (`ENVIRONMENT=prod`): 
  - AWS Secrets Manager에서 환경변수 로드
  - CORS Origins: `http://54.180.71.13:3000,http://54.180.71.13:5173,https://buildpechatbot.com:5000,https://buildpechatbot.com:5173`

## 테스트

로컬에서 Secrets Manager 연동을 테스트하려면:

```bash
# AWS 자격 증명 설정
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=ap-northeast-2

# 환경변수 설정
export ENVIRONMENT=prod

# 애플리케이션 실행
python main.py
```

## 보안 고려사항

1. **최소 권한 원칙**: IAM Role은 필요한 Secrets에만 접근 권한 부여
2. **Secret Rotation**: 정기적으로 Secret 값 변경
3. **암호화**: Secrets Manager는 기본적으로 암호화되어 저장
4. **접근 로깅**: CloudTrail을 통해 Secret 접근 로그 모니터링