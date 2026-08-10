class MediaServiceException(Exception):
    """Базовое исключение для media-service"""
    def __init__(self, message: str = "Media service error", status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class FileTooLargeException(MediaServiceException):
    def __init__(self, max_size: int):
        super().__init__(
            message=f"File too large. Max size: {max_size // (1024 * 1024)}MB",
            status_code=413
        )


class UnsupportedMediaTypeException(MediaServiceException):
    def __init__(self, allowed_types: list):
        super().__init__(
            message=f"Unsupported media type. Allowed: {', '.join(allowed_types)}",
            status_code=415
        )


class FileNotFoundException(MediaServiceException):
    def __init__(self, file_id: str):
        super().__init__(message=f"File not found: {file_id}", status_code=404)


class MinIOConnectionError(MediaServiceException):
    def __init__(self):
        super().__init__(message="MinIO connection error", status_code=503)


class ImageProcessingException(MediaServiceException):
    def __init__(self, message: str = "Image processing failed"):
        super().__init__(message=message, status_code=422)
        
class MaxAvatarsExceededException(MediaServiceException):
    def __init__(self, max_avatars: int):
        super().__init__(
            message=f"Maximum {max_avatars} avatars per user exceeded",
            status_code=400
        )