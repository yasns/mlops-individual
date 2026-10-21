# Spotify hitų prognozavimo platforma

Sistema prognozuoja, ar Spotify kūrinys yra "hitas" (`popularity >= 50`) arba "ne hitas" (`popularity < 50`), pagal jo garso požymius (`danceability`, `energy`, `tempo`, ir pan.), `explicit` žymą ir žanrą. 

## Reikalavimai
Docker, kind, kubectl, Python 3.11+, git. Apie 2 GB laisvo RAM.

## Paleidimas nuo nulio

### 1. Repo ir Python aplinka
```bash
git clone https://github.com/yasns/mlops-individual && cd mlops-individual
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Duomenys
Jei DVC remote (`~/dvcstore`) yra šiame kompiuteryje:
```bash
dvc pull
```
Jei ne (pvz., kitas kompiuteris) – atsisiųsti tą pačią rinkinio reviziją iš Hugging Face:
```bash
python src/fetch_data.py
```

### 3. Klasteris ir MLflow
```bash
kind create cluster --config k8s/kind-config.yaml
kubectl apply -f k8s/namespace.yaml -f k8s/mlflow.yaml
kubectl rollout status deployment/mlflow -n mlops
```
Pirmą kartą užtrunka kelias minutes, kol atsisiunčiamas MLflow vaizdas.

### 4. Prieiga prie MLflow
Atskirame terminale (palikti veikti):
```bash
kubectl port-forward -n mlops svc/mlflow 5000:5000
```
MLflow UI: http://127.0.0.1:5000

### 5. Pipeline'as
```bash
export MLFLOW_TRACKING_URI=http://127.0.0.1:5000
dvc repro
```
Jei niekas nepasikeitė, `dvc repro` praleidžia visus etapus. Naujam run'ui su tais pačiais parametrais – `dvc repro -f`.

### 6. Istorinio run'o atkūrimas
Run ID nukopijuoti iš MLflow UI (run'o puslapio antraštė). Darbinis medis turi būti švarus (`git status`).
```bash
time python reproduce.py <run_id>
```
Atkuria to run'o kodą (git), duomenis (DVC) ir parametrus, perleidžia pipeline'ą ir palygina metrikas. UI atsiranda naujas run'as su žyma `reproduces=<run_id>`.

## Rezultatai
| Kas | Kur |
|-----|-----|
| MLflow UI (run'ai, parametrai, metrikos, modeliai) | http://127.0.0.1:5000, eksperimentas `spotify-hits`, be prisijungimo |
| Pipeline'o metrikos | `metrics.json`, `dvc metrics show` |
| Reikalavimai (FR, NFR, KPI) | `docs/requirements.md` |
| Docker vaizdai | [`ghcr.io/yasns/u1-train`](https://github.com/users/yasns/packages/container/package/u1-train) |
| Vaizdo dydis, Trivy skenavimas | `docs/image-sizes.md`, `docs/security-scan.md` |

## Išjungimas
Dėmesio: ištrina ir visus MLflow run'us (PVC).
```bash
kind delete cluster --name mlops
```
