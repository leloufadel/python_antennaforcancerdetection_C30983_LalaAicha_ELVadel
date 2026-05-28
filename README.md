# NeuroScan AI — Brain Tumor Detection Flask App

A clean, production-ready Flask web app that wraps your ensemble tumor detection
models behind a polished drag-and-drop UI.

---

## Project Structure

```
brain_tumor_app/
├── app.py                  ← Flask backend
├── requirements.txt
├── templates/
│   └── index.html          ← UI (dark medical theme)
└── saved_models/           ← Put your .pkl files here
    ├── scaler.pkl
    ├── pca.pkl
    ├── model_svm.pkl
    ├── model_rf.pkl
    ├── model_gb.pkl
    ├── model_knn.pkl
    └── model_ensemble.pkl
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Copy your saved models
After running your training script, copy the `saved_models/` folder into
`brain_tumor_app/`:
```bash
cp -r saved_models/ brain_tumor_app/saved_models/
```

### 3. Run the app
```bash
cd brain_tumor_app
python app.py
```

Then open **http://localhost:5000** in your browser.

---

## How it works

1. User uploads a `.csv`, `.xlsx`, or `.xls` file (576 features per row).
2. Flask reads the file, flattens it to a 1D array.
3. If the array length ≠ 576, it's resampled via interpolation.
4. StandardScaler → PCA (100 components) → 4 classifiers + Ensemble.
5. Results are returned as JSON and rendered in the UI.

### Input format
- A single row of **576 float values** (the rich feature vector).
- Produced by `extract_rich_features_single()` from your training script.
- No header row needed (header=None).

---

## API endpoint

### `POST /predict`
**Form data:** `file` — a .csv/.xlsx file

**Response JSON:**
```json
{
  "verdict":       "Tumor" | "Healthy",
  "is_tumor":      true | false,
  "confidence":    87.3,
  "tumor_votes":   3,
  "healthy_votes": 1,
  "individual": [
    { "model": "SVM (RBF)", "prediction": "Tumor", "confidence": 91.2, "is_tumor": true },
    ...
  ],
  "warning":    "Strong model agreement — high suspicion of tumor" | null,
  "resampled":  false,
  "feature_count": 576,
  "filename":   "patient_scan.csv"
}
```

---

## Generating test files

Your training script already generates `patient_tumor.csv` and
`patient_healthy.csv`. Use those to test the app immediately.
