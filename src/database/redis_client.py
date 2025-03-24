import os
import redis
from typing import Optional

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', 'mypassword')
REDIS_DB = int(os.getenv('REDIS_DB', 0))

_redis_client = None

RATE_LIMIT_EXPIRATION = 60 * 60 * 24 * 7  # 7 days
SIMILARITY_CACHE_EXPIRATION = 60 * 60 * 24 * 5  # 5 days
SESSION_EXPIRATION = 60 * 60 * 24  # 1 day


def get_redis_client() -> redis.Redis:
    """
    Retorna uma instância compartilhada do cliente Redis.
    Cria a conexão se ainda não existir.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASSWORD,
            db=REDIS_DB,
            decode_responses=True,
            socket_timeout=5,
            retry_on_timeout=True
        )
    return _redis_client


def set_with_expiry(key: str, value: str, expiration: int) -> bool:
    """
    Define um valor no Redis com expiração.

    Args:
        key: Chave do Redis
        value: Valor a ser armazenado
        expiration: Tempo de expiração em segundos

    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário
    """
    try:
        client = get_redis_client()
        return client.setex(key, expiration, value)
    except Exception as e:
        print(f"Error in defined value in Redis: {e}")
        return False


def get_value(key: str) -> Optional[str]:
    """
    Obtém um valor do Redis.

    Args:
        key: Chave do Redis

    Returns:
        Optional[str]: Valor armazenado ou None se a chave não existir ou ocorrer erro
    """
    try:
        client = get_redis_client()
        return client.get(key)
    except Exception as e:
        print(f"Error in defined value in Redis: {e}")
        return None


def get_ttl(key: str) -> int:
    """
    Obtém o tempo restante de expiração de uma chave.

    Args:
        key: Chave do Redis

    Returns:
        int: Tempo restante em segundos, -1 se não tiver expiração, -2 se a chave não existir
    """
    try:
        client = get_redis_client()
        return client.ttl(key)
    except Exception as e:
        print(f"Error in get TTL value in Redis: {e}")
        return -2


def delete_key(key: str) -> bool:
    """
    Remove uma chave do Redis.

    Args:
        key: Chave do Redis

    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário
    """
    try:
        client = get_redis_client()
        return client.delete(key) > 0
    except Exception as e:
        print(f"Error in delete Redis key: {e}")
        return False