# Repository Guidelines

## Project Structure & Module Organization

This repository is a flat Python workspace for preprocessing Windows PE files and inspecting LightGBM models. The `Data_Processing*.ipynb` notebooks contain the main exploratory and training workflows for PE32, PE64, and .NET samples. Standalone utilities live at the root: `feature_importance*.py` and `fi_new.py` inspect trained models, `check_regex_features.py` compares extraction results, and `parse_sample.py` explains a sample feature vector. Files named `PE32*`, `PE64*`, and `PENET*` are feature dictionaries or section vocabularies. Treat `*.mdl`, `*.csv`, and `cyaipe-training.zip` as generated or data artifacts, not source modules.

## Build, Test, and Development Commands

There is no build system or dependency manifest yet. Use an isolated environment and install the packages imported by the workflow (notably Jupyter, NumPy, and LightGBM):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install jupyter numpy lightgbm
jupyter lab
```

Run a focused utility with `python .\fi_new.py` or `python .\check_regex_features.py` after updating its input paths. Before submitting Python changes, perform a syntax check:

```powershell
python -m compileall -q .
```

## Coding Style & Naming Conventions

Follow PEP 8 with four-space indentation. Use `snake_case` for functions and variables, `UPPER_SNAKE_CASE` for configuration constants, and descriptive module names. Prefer `pathlib.Path` and repository-relative paths over hard-coded drive or user-directory paths. Keep reusable logic in functions guarded by `if __name__ == "__main__":`; notebooks should orchestrate those functions rather than duplicate them. Preserve UTF-8 encoding for Vietnamese comments and output.

## Testing Guidelines

No automated test suite or coverage target currently exists; `test.py` and `test2.py` are encryption/decryption utilities, not unit tests. New tests should use `pytest`, live under `tests/`, and follow `test_<behavior>.py` naming. Cover feature-vector dimensions, vocabulary ordering, malformed input, and encryption round trips. Do not execute unknown PE samples during tests.

## Commit & Pull Request Guidelines

The repository has no commits from which to infer a convention. Use short, imperative Conventional Commit messages, such as `fix: preserve PE32 feature ordering`. Pull requests should describe the dataset/model affected, commands run, and any feature-count or metric changes. Link relevant issues and attach concise notebook output or plots when results change. Avoid committing secrets, machine-specific paths, raw malware, notebook output bloat, or regenerated models unless the review explicitly requires them.
