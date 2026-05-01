from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml


def build_schema() -> dict:
    repo_root = Path(__file__).resolve().parents[1]
    backend_root = repo_root / "backend"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

    from app.main import app

    schema = app.openapi()
    schema["openapi"] = "3.1.0"
    schema["info"]["summary"] = "OpenAPI 3.1 specification for the MedVision-CXR backend"
    schema["info"]["description"] = (
        "MedVision-CXR is an AI-assisted chest X-ray triage system. This specification covers "
        "authentication, upload, AI-assisted risk assessment, Grad-CAM, doctor review, audit logs, "
        "model metadata, direct delete, health, and the governed deletion approval workflow."
    )
    schema["servers"] = [{"url": "http://localhost:8000", "description": "Local development server"}]
    return schema


def write_yaml(output_path: Path, schema: dict) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(schema, handle, sort_keys=False, allow_unicode=True)


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    workspace_root = repo_root.parent

    parser = argparse.ArgumentParser(description="Generate synchronized OpenAPI YAML for backend docs and frontend viewers.")
    parser.add_argument(
        "--output",
        action="append",
        dest="outputs",
        help="Optional explicit output path. Can be provided multiple times.",
    )
    args = parser.parse_args()

    outputs = [
        workspace_root / "docs" / "medvision-cxr-openapi.yaml",
        repo_root / "frontend" / "public" / "openapi" / "medvision-cxr-openapi.yaml",
    ]
    if args.outputs:
        outputs = [Path(path).resolve() for path in args.outputs]

    schema = build_schema()
    for output_path in outputs:
        write_yaml(output_path, schema)
        print(f"Generated {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())