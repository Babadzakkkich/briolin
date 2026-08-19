# app/services/minio_client.py
import io
import json
from typing import Optional, Tuple, BinaryIO
from minio import Minio
from minio.error import S3Error
import asyncio
from functools import partial

from app.core.config import settings
from app.core.logger import logger
from app.core.exceptions import MinIOConnectionError, FileNotFoundException


class MinIOClient:
    """Асинхронный клиент для MinIO"""
    
    def __init__(self):
        self._client: Optional[Minio] = None
        self._lock = asyncio.Lock()
        self._bucket = settings.minio.bucket
    
    def _get_sync_client(self) -> Minio:
        """Получение синхронного клиента"""
        if self._client is None:
            try:
                self._client = Minio(
                    endpoint=settings.minio.endpoint,
                    access_key=settings.minio.access_key,
                    secret_key=settings.minio.secret_key,
                    secure=settings.minio.secure,
                    region=settings.minio.region
                )
                
                # Создаем bucket если не существует
                if not self._client.bucket_exists(self._bucket):
                    self._client.make_bucket(self._bucket)
                    logger.info(f"Created bucket: {self._bucket}")
                    
                    policy = {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"AWS": ["*"]},
                                "Action": ["s3:GetObject"],
                                "Resource": [f"arn:aws:s3:::{self._bucket}/*"]
                            }
                        ]
                    }
                    policy_json = json.dumps(policy)
                    self._client.set_bucket_policy(self._bucket, policy_json)
                    logger.info(f"Set public read policy for bucket: {self._bucket}")
                    
            except Exception as e:
                logger.error(f"Failed to connect to MinIO: {e}")
                raise MinIOConnectionError()
        
        return self._client
    
    async def upload_file(
        self,
        file_data: bytes,
        object_name: str,
        content_type: str
    ) -> Tuple[str, int]:
        """
        Загружает файл в MinIO
        
        Returns:
            Tuple[str, int]: (object_name, size)
        """
        try:
            loop = asyncio.get_event_loop()
            client = self._get_sync_client()
            
            file_size = len(file_data)
            file_stream = io.BytesIO(file_data)
            
            await loop.run_in_executor(
                None,
                partial(
                    client.put_object,
                    bucket_name=self._bucket,
                    object_name=object_name,
                    data=file_stream,
                    length=file_size,
                    content_type=content_type
                )
            )
            
            logger.info(f"Uploaded file: {object_name} ({file_size} bytes)")
            return object_name, file_size
            
        except S3Error as e:
            logger.error(f"MinIO upload error: {e}")
            raise MinIOConnectionError()
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            raise
    
    async def get_file(self, object_name: str) -> Tuple[bytes, str]:
        """
        Получает файл из MinIO
        
        Returns:
            Tuple[bytes, str]: (file_data, content_type)
        """
        try:
            loop = asyncio.get_event_loop()
            client = self._get_sync_client()
            
            response = await loop.run_in_executor(
                None,
                partial(client.get_object, self._bucket, object_name)
            )
            
            try:
                data = await loop.run_in_executor(None, response.read)
                content_type = response.headers.get('Content-Type', 'application/octet-stream')
                return data, content_type
            finally:
                response.close()
                response.release_conn()
                
        except S3Error as e:
            if e.code == 'NoSuchKey':
                raise FileNotFoundException(object_name)
            logger.error(f"MinIO get error: {e}")
            raise MinIOConnectionError()
        except Exception as e:
            logger.error(f"Get file failed: {e}")
            raise
    
    async def delete_file(self, object_name: str) -> bool:
        """Удаляет файл из MinIO"""
        try:
            loop = asyncio.get_event_loop()
            client = self._get_sync_client()
            
            await loop.run_in_executor(
                None,
                partial(client.remove_object, self._bucket, object_name)
            )
            
            logger.info(f"Deleted file: {object_name}")
            return True
            
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return False
            logger.error(f"MinIO delete error: {e}")
            raise MinIOConnectionError()
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            raise
    
    async def get_url(self, object_name: str, expires: int = 3600) -> str:
        """Получает временную ссылку на файл"""
        try:
            loop = asyncio.get_event_loop()
            client = self._get_sync_client()
            
            url = await loop.run_in_executor(
                None,
                partial(
                    client.presigned_get_object,
                    self._bucket,
                    object_name,
                    expires=expires
                )
            )
            
            return url
            
        except S3Error as e:
            logger.error(f"MinIO presigned URL error: {e}")
            raise FileNotFoundException(object_name)
        except Exception as e:
            logger.error(f"Get URL failed: {e}")
            raise


# Глобальный экземпляр
_minio_client = None

def get_minio_client() -> MinIOClient:
    global _minio_client
    if _minio_client is None:
        _minio_client = MinIOClient()
    return _minio_client