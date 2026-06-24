# Breast Tumor Detection - Flask Web App

This is a small Flask application I built to test the ensemble model from my
machine learning pipeline on new patient data. You upload a CSV or Excel file
with the extracted features and it runs the file through the same scaler, PCA,
and four classifiers used during training, then shows the prediction from
each model along with the final ensemble verdict.

## Folder structure

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
Copy the models you trained earlier into the app folder. If you ran the
training script already, the `saved_models/` folder should already exist -
just move it here:
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
Open `http://localhost:5000` in a browser.

## What the app actually does

When a file is uploaded, the backend:

1. Reads the CSV/Excel file and flattens it into a single array of numbers
2. Checks the length - it should be 576 (8 statistics x 72 antennas). If it's
   not exactly 576, the app resamples it using linear interpolation so it
   fits, and flags this in the response so the result isn't treated as fully
   reliable
3. Applies the same StandardScaler and PCA that were fit during training
4. Runs the 100-dimensional PCA vector through the four trained classifiers
   (SVM, Random Forest, Gradient Boosting, KNN) and the soft-voting ensemble
5. Sends back a JSON response with each model's individual prediction, the
   ensemble's final verdict, and a confidence score

## Input format

The uploaded file should contain one row of 576 values - the feature vector
produced by `extract_rich_features_single()` in the training script. No
header row.

## API

`POST /predict`, form field `file`.

Example response:
```json
{
  "verdict": "Tumor",
  "is_tumor": true,
  "confidence": 87.3,
  "tumor_votes": 3,
  "healthy_votes": 1,
  "individual": [
    { "model": "SVM (RBF)", "prediction": "Tumor", "confidence": 91.2, "is_tumor": true }
  ],
  "warning": "Strong model agreement - high suspicion of tumor",
  "resampled": false,
  "feature_count": 576,
  "filename": "patient_scan.csv"
}
```

`warning` is null if there's nothing to flag.

## Testing

The training script generates two test files, `patient_tumor.csv` and
`patient_healthy.csv`. These can be uploaded directly to check the app is
working correctly before testing with new data.
