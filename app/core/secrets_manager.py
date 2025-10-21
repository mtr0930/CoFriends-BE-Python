"""
AWS Secrets Manager integration for loading environment variables
"""
import json
import os
import logging
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)


class SecretsManager:
    """AWS Secrets Manager client wrapper"""
    
    def __init__(self, region_name: str = "ap-northeast-2"):
        """
        Initialize Secrets Manager client
        
        Args:
            region_name: AWS region name
        """
        self.region_name = region_name
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize boto3 client for Secrets Manager"""
        try:
            self.client = boto3.client(
                'secretsmanager',
                region_name=self.region_name
            )
            logger.info(f"Secrets Manager client initialized for region: {self.region_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            self.client = None
        except Exception as e:
            logger.error(f"Failed to initialize Secrets Manager client: {e}")
            self.client = None
    
    def get_secret(self, secret_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve secret from AWS Secrets Manager
        
        Args:
            secret_id: Secret identifier
            
        Returns:
            Dictionary containing secret values or None if failed
        """
        if not self.client:
            logger.error("Secrets Manager client not initialized")
            return None
            
        try:
            response = self.client.get_secret_value(SecretId=secret_id)
            secret_string = response.get('SecretString')
            
            if secret_string:
                return json.loads(secret_string)
            else:
                logger.error(f"No secret string found for {secret_id}")
                return None
                
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                logger.error(f"Secret {secret_id} not found")
            elif error_code == 'InvalidRequestException':
                logger.error(f"Invalid request for secret {secret_id}")
            elif error_code == 'InvalidParameterException':
                logger.error(f"Invalid parameter for secret {secret_id}")
            elif error_code == 'DecryptionFailure':
                logger.error(f"Decryption failed for secret {secret_id}")
            elif error_code == 'InternalServiceError':
                logger.error(f"AWS internal service error for secret {secret_id}")
            else:
                logger.error(f"Error retrieving secret {secret_id}: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from secret {secret_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret {secret_id}: {e}")
            return None
    
    def load_environment_variables(self, secret_ids: Dict[str, str]) -> Dict[str, str]:
        """
        Load environment variables from multiple secrets
        
        Args:
            secret_ids: Dictionary mapping environment variable prefix to secret ID
                       e.g., {"SLACK_": "prod/buildpechatbot/slack", "AWS_": "prod/buildpechatbot/bedrock"}
        
        Returns:
            Dictionary of environment variables
        """
        env_vars = {}
        
        for prefix, secret_id in secret_ids.items():
            logger.info(f"Loading secrets from {secret_id}")
            secret_data = self.get_secret(secret_id)
            
            if secret_data:
                # Add prefix to each key and convert to uppercase
                for key, value in secret_data.items():
                    env_key = f"{prefix}{key}".upper()
                    env_vars[env_key] = str(value)
                    logger.debug(f"Loaded {env_key}")
            else:
                logger.warning(f"Failed to load secrets from {secret_id}")
        
        return env_vars


def load_secrets_to_environment():
    """
    Load secrets from AWS Secrets Manager and set as environment variables
    This function should be called at application startup
    """
    # Define secret mappings
    secret_mappings = {
        "SLACK_": "prod/buildpechatbot/slack",
        "AWS_": "prod/buildpechatbot/bedrock"
    }
    
    # Check if we're in production environment
    environment = os.getenv("ENVIRONMENT", "local")
    
    if environment.lower() in ["prod", "production"]:
        logger.info("Loading secrets from AWS Secrets Manager")
        secrets_manager = SecretsManager()
        env_vars = secrets_manager.load_environment_variables(secret_mappings)
        
        # Set environment variables only if they are not already set
        for key, value in env_vars.items():
            if not os.getenv(key):  # Only set if not already set
                os.environ[key] = value
                logger.info(f"Set environment variable: {key}")
            else:
                logger.info(f"Environment variable {key} already set, skipping")
        
        logger.info(f"Loaded {len(env_vars)} environment variables from Secrets Manager")
    else:
        logger.info(f"Skipping Secrets Manager in {environment} environment")


# Convenience function for direct secret access
def get_secret_value(secret_id: str, key: str, default: str = "") -> str:
    """
    Get a specific value from a secret
    
    Args:
        secret_id: Secret identifier
        key: Key within the secret
        default: Default value if not found
        
    Returns:
        Secret value or default
    """
    secrets_manager = SecretsManager()
    secret_data = secrets_manager.get_secret(secret_id)
    
    if secret_data and key in secret_data:
        return str(secret_data[key])
    
    return default
