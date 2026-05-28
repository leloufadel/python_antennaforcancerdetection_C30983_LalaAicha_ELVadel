import os
import numpy as np
import pandas as pd
import joblib
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
app.config['UPLOAD_FOLDER'] = 'uploads'

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def load_models():
    """Load all saved models and preprocessors."""
    base = 'saved_models'
    return {
        'scaler':   joblib.load(f'{base}/scaler.pkl'),
        'pca':      joblib.load(f'{base}/pca.pkl'),
        'svm':      joblib.load(f'{base}/model_svm.pkl'),
        'rf':       joblib.load(f'{base}/model_rf.pkl'),
        'gb':       joblib.load(f'{base}/model_gb.pkl'),
        'knn':      joblib.load(f'{base}/model_knn.pkl'),
        'ensemble': joblib.load(f'{base}/model_ensemble.pkl'),
    }


def predict_from_features(data: np.ndarray, models: dict) -> dict:
    """Run prediction pipeline on a 576-feature vector."""
    TARGET = 576

    # Resize if needed
    resampled = False
    if len(data) != TARGET:
        from scipy.interpolate import interp1d
        data = interp1d(
            np.linspace(0, 1, len(data)), data
        )(np.linspace(0, 1, TARGET))
        resampled = True

    # Preprocess
    data_sc  = models['scaler'].transform(data.reshape(1, -1))
    data_pca = models['pca'].transform(data_sc)

    model_map = {
        'SVM (RBF)':         'svm',
        'Random Forest':     'rf',
        'Gradient Boosting': 'gb',
        'KNN':               'knn',
    }

    individual = []
    votes = []
    for display_name, key in model_map.items():
        mdl  = models[key]
        pred = int(mdl.predict(data_pca)[0])
        prob = mdl.predict_proba(data_pca)[0]
        conf = float(prob[pred] * 100)
        individual.append({
            'model':      display_name,
            'prediction': 'Tumor' if pred == 1 else 'Healthy',
            'confidence': round(conf, 1),
            'is_tumor':   pred == 1,
        })
        votes.append(pred)

    # Ensemble
    ens   = models['ensemble']
    ep    = int(ens.predict(data_pca)[0])
    eprob = ens.predict_proba(data_pca)[0]
    ec    = float(eprob[ep] * 100)

    tumor_votes   = sum(votes)
    healthy_votes = 4 - tumor_votes

    warning = None
    if ec < 60:
        warning = 'Low confidence — recommend clinical review'
    elif tumor_votes >= 3 and ep == 1:
        warning = 'Strong model agreement — high suspicion of tumor'
    elif tumor_votes == 2:
        warning = 'Mixed results — further examination recommended'

    return {
        'verdict':       'Tumor' if ep == 1 else 'Healthy',
        'is_tumor':      ep == 1,
        'confidence':    round(ec, 1),
        'tumor_votes':   tumor_votes,
        'healthy_votes': healthy_votes,
        'individual':    individual,
        'warning':       warning,
        'resampled':     resampled,
        'feature_count': int(len(data)),
    }


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/predict', methods=['POST'])
def predict():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload .csv, .xlsx, or .xls'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        # Read file
        if filename.endswith('.csv'):
            df = pd.read_csv(filepath, header=None)
        else:
            df = pd.read_excel(filepath, header=None)

        data = df.values.astype(float).flatten()

        # Load models & predict
        models  = load_models()
        result  = predict_from_features(data, models)
        result['filename'] = file.filename
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

    finally:
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
