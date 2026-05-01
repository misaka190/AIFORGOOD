import io
import uuid
from pathlib import Path

import pydicom
from fastapi import HTTPException, UploadFile, status
from PIL import Image

from app.core.config import get_settings


ALLOWED_MIME_TYPES = {"image/png", "image/jpeg", "application/dicom", "application/octet-stream"}
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".dcm"}


def validate_upload_file(file: UploadFile) -> None:
    settings = get_settings()
    extension = Path(file.filename or "").suffix.lower()
    if file.content_type not in ALLOWED_MIME_TYPES or extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    if extension == ".dcm" and not settings.allow_dicom:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="DICOM uploads are disabled")


def anonymized_filename(original_name: str) -> str:
    extension = Path(original_name).suffix.lower()
    return f"{uuid.uuid4().hex}{extension}"


def remove_image_exif(contents: bytes, extension: str) -> bytes:
    image = Image.open(io.BytesIO(contents)).convert("L")
    buffer = io.BytesIO()
    save_format = "PNG" if extension == ".png" else "JPEG"
    image.save(buffer, format=save_format)
    return buffer.getvalue()


def sanitize_dicom(contents: bytes) -> bytes:
    dataset = pydicom.dcmread(io.BytesIO(contents), force=True)
    for field_name in [
        "PatientName",
        "PatientID",
        "PatientBirthDate",
        "PatientSex",
        "OtherPatientIDs",
        "InstitutionName",
        "ReferringPhysicianName",
        "AccessionNumber",
    ]:
        if field_name in dataset:
            dataset.data_element(field_name).value = "ANONYMIZED"

    output = io.BytesIO()
    dataset.save_as(output)
    return output.getvalue()


def detect_image_size(contents: bytes, extension: str) -> tuple[int | None, int | None, str | None]:
    if extension == ".dcm":
        dataset = pydicom.dcmread(io.BytesIO(contents), force=True)
        return int(getattr(dataset, "Columns", 0)) or None, int(getattr(dataset, "Rows", 0)) or None, str(getattr(dataset, "Modality", "DX"))

    image = Image.open(io.BytesIO(contents))
    return image.width, image.height, None
