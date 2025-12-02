"""
File validation utilities for secure file uploads.
Implements magic byte checking to prevent file type spoofing.
"""
from typing import BinaryIO, Optional
from fastapi import HTTPException, UploadFile
import logging

logger = logging.getLogger(__name__)


# Magic bytes for different file types
# Source: https://en.wikipedia.org/wiki/List_of_file_signatures
MAGIC_BYTES = {
    'xlsx': [
        bytes([0x50, 0x4B, 0x03, 0x04]),  # ZIP archive (XLSX is a ZIP)
        bytes([0x50, 0x4B, 0x05, 0x06]),  # ZIP archive (empty)
        bytes([0x50, 0x4B, 0x07, 0x08]),  # ZIP archive (spanned)
    ],
    'xls': [
        bytes([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1]),  # Microsoft Office document
    ],
}


def check_magic_bytes(file_content: bytes, expected_type: str) -> bool:
    """
    Check if file content starts with expected magic bytes.

    Args:
        file_content: The first few bytes of the file
        expected_type: Expected file type ('xlsx' or 'xls')

    Returns:
        True if magic bytes match, False otherwise
    """
    if expected_type not in MAGIC_BYTES:
        logger.warning(f"Unknown file type for magic byte check: {expected_type}")
        return False

    magic_byte_options = MAGIC_BYTES[expected_type]

    for magic_bytes in magic_byte_options:
        if file_content.startswith(magic_bytes):
            return True

    return False


def get_file_type_from_extension(filename: str) -> Optional[str]:
    """
    Get expected file type from filename extension.

    Args:
        filename: The filename with extension

    Returns:
        File type ('xlsx' or 'xls') or None if not recognized
    """
    filename_lower = filename.lower()
    if filename_lower.endswith('.xlsx'):
        return 'xlsx'
    elif filename_lower.endswith('.xls'):
        return 'xls'
    return None


async def validate_excel_upload(file: UploadFile) -> bytes:
    """
    Validate that an uploaded file is a genuine Excel file.
    Checks both extension and magic bytes.

    Args:
        file: The uploaded file

    Returns:
        The file content as bytes

    Raises:
        HTTPException: If file is not a valid Excel file
    """
    # Check file extension first
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing")

    expected_type = get_file_type_from_extension(file.filename)
    if not expected_type:
        raise HTTPException(
            status_code=400,
            detail="File must be an Excel file (.xlsx or .xls)"
        )

    # Read file content
    content = await file.read()

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="File is empty")

    # Check magic bytes
    if not check_magic_bytes(content, expected_type):
        logger.warning(
            f"File upload rejected: {file.filename} - "
            f"Extension suggests {expected_type} but magic bytes don't match. "
            f"First 8 bytes: {content[:8].hex()}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"File appears to be corrupted or is not a valid {expected_type.upper()} file. "
                   "The file signature doesn't match the file extension."
        )

    logger.info(f"File upload validated: {file.filename} ({expected_type})")
    return content


# Size limits (in bytes)
MAX_EXCEL_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


async def validate_excel_upload_with_size_limit(file: UploadFile, max_size: int = MAX_EXCEL_FILE_SIZE) -> bytes:
    """
    Validate Excel file upload with size limit.

    Args:
        file: The uploaded file
        max_size: Maximum allowed file size in bytes (default: 10 MB)

    Returns:
        The file content as bytes

    Raises:
        HTTPException: If file is invalid or too large
    """
    content = await validate_excel_upload(file)

    if len(content) > max_size:
        size_mb = len(content) / (1024 * 1024)
        max_mb = max_size / (1024 * 1024)
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {size_mb:.2f} MB. Maximum allowed size is {max_mb:.2f} MB"
        )

    return content
