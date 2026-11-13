from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
import os

app = Flask(__name__)
CORS(app)

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'dropout_risk_model.sav')
ORDER_PATH = os.path.join(os.path.dirname(__file__), 'feature_order.sav')
DEFAULTS_PATH = os.path.join(os.path.dirname(__file__), 'feature_defaults.sav')

model = pickle.load(open(MODEL_PATH, 'rb'))
feature_order = pickle.load(open(ORDER_PATH, 'rb'))
feature_defaults = pickle.load(open(DEFAULTS_PATH, 'rb'))

@app.route('/')
def home():
    return jsonify({"status": "ok", "message": "Dropout Risk API is running"})

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()

        age = float(data.get('age'))
        admission_grade = float(data.get('admissionGrade'))
        previous_grade = float(data.get('previousQualificationGrade'))
        sem1_enrolled = float(data.get('sem1Enrolled', feature_defaults.get('Curricular units 1st sem (enrolled)', 6)))
        sem1_approved = float(data.get('sem1Approved', feature_defaults.get('Curricular units 1st sem (approved)', 5)))
        sem2_enrolled = float(data.get('sem2Enrolled', feature_defaults.get('Curricular units 2nd sem (enrolled)', 6)))
        sem2_approved = float(data.get('sem2Approved', feature_defaults.get('Curricular units 2nd sem (approved)', 5)))

        input_dict = feature_defaults.copy()
        input_dict['Age at enrollment'] = age
        input_dict['Admission grade'] = admission_grade
        input_dict['Previous qualification (grade)'] = previous_grade
        input_dict['Curricular units 1st sem (enrolled)'] = sem1_enrolled
        input_dict['Curricular units 1st sem (approved)'] = sem1_approved
        input_dict['Curricular units 2nd sem (enrolled)'] = sem2_enrolled
        input_dict['Curricular units 2nd sem (approved)'] = sem2_approved

        input_df = pd.DataFrame([input_dict])
        input_df = input_df[feature_order]

        prediction = model.predict(input_df)[0]
        score = round(float(prediction), 2)
        score = max(0, min(100, score))

        if score < 33:
            category = "Low"
        elif score < 66:
            category = "Medium"
        else:
            category = "High"

        return jsonify({
            "score": score,
            "category": category,
            "success": True
        })

    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
