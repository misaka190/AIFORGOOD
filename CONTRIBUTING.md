# Contributing to MedVision-CXR

Thank you for contributing to MedVision-CXR.

This repository is positioned as a Responsible AI project for chest X-ray triage support. Contributions should improve reliability, transparency, usability, reproducibility, or documentation without making unsupported medical claims.

## Project Principles

- Do not describe the system as an automated diagnosis tool.
- Do not add language that suggests the model can confirm disease.
- Preserve the project's safety boundary: AI-assisted triage, screening support, and doctor review prioritization only.
- Prefer clear documentation, reproducible experiments, and auditable changes.
- Treat privacy, fairness, and clinician oversight as product requirements, not optional extras.

## Ways to Contribute

- Fix bugs in frontend, backend, training, or deployment workflows
- Improve tests and CI reliability
- Improve model evaluation, calibration, and fairness analysis
- Improve explainability workflows such as Grad-CAM output and wording
- Improve documentation, examples, and onboarding
- Add low-resource deployment or offline-first improvements

## Before You Start

1. Open an issue for large features or architecture changes.
2. Check existing documentation in README.md and docs/medvision-cxr-blueprint.md.
3. Keep PRs focused. Avoid mixing unrelated fixes.

## Development Setup

### Using Docker Compose

```bash
docker compose up --build
```

### Frontend

```bash
cd medvision-cxr/frontend
npm install
npm run dev
```

### Backend

```bash
cd medvision-cxr/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Model Training

```bash
cd medvision-cxr/ml-training
pip install -r requirements.txt
python src/train.py --config configs/cxr_densenet121.yaml
```

## Pull Request Guidelines

1. Fork the repository and create a feature branch.
2. Make the smallest change that fully addresses the issue.
3. Validate your changes locally.
4. Update documentation when behavior, setup, or APIs change.
5. Submit a pull request with:

- a concise problem statement
- a short change summary
- validation notes
- screenshots or sample payloads when relevant

## Validation Expectations

Contributors should validate the narrowest relevant surface before submitting.

- Frontend: page rendering, route behavior, and build checks
- Backend: syntax checks, targeted API validation, and tests when available
- Training: script execution path, config compatibility, and metrics output where relevant

## Medical Safety and Language Policy

Please follow these wording rules consistently:

- Use “risk prompt”, “AI-assisted findings”, “review recommendation”, or “triage support”.
- Do not use “diagnosis”, “confirmed disease”, “AI found the lesion”, or “treatment recommendation” in user-facing copy unless the context is explicitly discussing prohibited wording.
- Keep Grad-CAM wording aligned with: model attention for risk prompts, not proof of pathology.

## Privacy and Data Handling

- Do not commit identifiable medical data.
- Use public de-identified datasets for demos and experiments.
- Avoid storing unnecessary personal information in logs, fixtures, or examples.
- If you add DICOM handling, ensure identity metadata is removed or masked.

## Code Style

- Preserve existing naming and file organization.
- Prefer small, readable modules over large utility dumps.
- Add comments only where the code would otherwise be hard to interpret.
- Keep API schemas explicit and medically safe.

## Reporting Security or Safety Issues

If you discover a security, privacy, or medical safety issue, do not open a public exploit-style issue. Report it privately to the maintainers listed in the repository README and include enough detail to reproduce the risk.

## License

By contributing to this repository, you agree that your contributions will be licensed under the MIT License in this repository.