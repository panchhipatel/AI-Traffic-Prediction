"""
Traffic Congestion Prediction Model
ML pipeline for predicting traffic congestion levels
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

# File paths
DATASET_FILE = "Banglore_traffic_Dataset.csv"
MODEL_FILE = "traffic_model.joblib"
ENCODERS_FILE = "encoders.joblib"
SCALER_FILE = "scaler.joblib"


def load_and_preprocess_data():
    """Load and preprocess the traffic dataset"""
    df = pd.read_csv(DATASET_FILE)
    
    # Parse date
    df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')
    df['Day'] = df['Date'].dt.day
    df['Month'] = df['Date'].dt.month
    df['DayOfWeek'] = df['Date'].dt.dayofweek
    
    # Create congestion categories (Low: 0-40, Medium: 40-70, High: 70-100)
    df['Congestion_Category'] = pd.cut(
        df['Congestion Level'], 
        bins=[0, 40, 70, 100], 
        labels=['Low', 'Medium', 'High']
    )
    
    return df


def prepare_features(df):
    """Prepare features for ML model"""
    
    # Initialize encoders
    encoders = {}
    
    # Encode categorical columns
    categorical_cols = ['Area Name', 'Road/Intersection Name', 'Weather Conditions', 
                        'Roadwork and Construction Activity']
    
    for col in categorical_cols:
        le = LabelEncoder()
        df[f'{col}_encoded'] = le.fit_transform(df[col])
        encoders[col] = le
    
    # Select features for model
    feature_cols = [
        'Area Name_encoded', 'Road/Intersection Name_encoded',
        'Traffic_Volume', 'Average Speed', 'Travel Time Index',
        'Road Capacity Utilization', 'Incident Reports', 
        'Environmental Impact', 'Public Transport Usage',
        'Traffic Signal Compliance', 'Parking Usage',
        'Pedestrian and Cyclist Count', 'Weather Conditions_encoded',
        'Roadwork and Construction Activity_encoded',
        'Day', 'Month', 'DayOfWeek'
    ]
    
    X = df[feature_cols]
    y = df['Congestion_Category']
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, y, encoders, scaler, feature_cols


def train_model():
    """Train the congestion prediction model"""
    print("Loading and preprocessing data...")
    df = load_and_preprocess_data()
    
    print("Preparing features...")
    X, y, encoders, scaler, feature_cols = prepare_features(df)
    
    # Encode target variable
    target_encoder = LabelEncoder()
    y_encoded = target_encoder.fit_transform(y)
    encoders['target'] = target_encoder
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42
    )
    
    print("Training Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy: {accuracy:.2%}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=target_encoder.classes_))
    
    # Save model and encoders
    print("\nSaving model and encoders...")
    joblib.dump(model, MODEL_FILE)
    joblib.dump(encoders, ENCODERS_FILE)
    joblib.dump(scaler, SCALER_FILE)
    joblib.dump(feature_cols, 'feature_cols.joblib')
    
    print("Model training complete!")
    return model, encoders, scaler


def load_model():
    """Load trained model and encoders"""
    if not os.path.exists(MODEL_FILE):
        print("Model not found. Training new model...")
        return train_model()
    
    model = joblib.load(MODEL_FILE)
    encoders = joblib.load(ENCODERS_FILE)
    scaler = joblib.load(SCALER_FILE)
    
    return model, encoders, scaler


def predict_congestion(model, encoders, scaler, input_data):
    """
    Predict congestion level for given input
    
    input_data: dict with keys:
        - area_name, road_name, traffic_volume, avg_speed, 
        - travel_time_index, road_capacity, incidents, 
        - env_impact, public_transport, signal_compliance,
        - parking_usage, pedestrian_count, weather, roadwork,
        - day, month, day_of_week
    """
    
    # Encode categorical inputs
    area_encoded = encoders['Area Name'].transform([input_data['area_name']])[0]
    road_encoded = encoders['Road/Intersection Name'].transform([input_data['road_name']])[0]
    weather_encoded = encoders['Weather Conditions'].transform([input_data['weather']])[0]
    roadwork_encoded = encoders['Roadwork and Construction Activity'].transform([input_data['roadwork']])[0]
    
    # Create feature array
    features = np.array([[
        area_encoded, road_encoded,
        input_data['traffic_volume'], input_data['avg_speed'],
        input_data['travel_time_index'], input_data['road_capacity'],
        input_data['incidents'], input_data['env_impact'],
        input_data['public_transport'], input_data['signal_compliance'],
        input_data['parking_usage'], input_data['pedestrian_count'],
        weather_encoded, roadwork_encoded,
        input_data['day'], input_data['month'], input_data['day_of_week']
    ]])
    
    # Scale features
    features_scaled = scaler.transform(features)
    
    # Predict
    prediction = model.predict(features_scaled)
    probability = model.predict_proba(features_scaled)
    
    # Decode prediction
    congestion_level = encoders['target'].inverse_transform(prediction)[0]
    
    return congestion_level, probability[0]


if __name__ == "__main__":
    train_model()
