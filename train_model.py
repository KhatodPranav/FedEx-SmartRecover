import pandas as pd
import pickle
from sklearn.ensemble import RandomForestClassifier

# 1. LOAD THE DATASET YOU JUST CREATED
try:
    df = pd.read_csv('training_data.csv')
    print("✅ Loaded training_data.csv successfully.")
except FileNotFoundError:
    print("❌ Error: Could not find 'training_data.csv'. Did you create the file?")
    exit()

# 2. SEPARATE FEATURES (X) AND TARGET (y)
# Input: Amount Due, Days Overdue
X = df[['amount_due', 'days_overdue']]
# Output: 0 (Won't Pay) or 1 (Will Pay)
y = df['will_pay']

# 3. TRAIN THE MODEL
model = RandomForestClassifier(n_estimators=50, random_state=42)
model.fit(X, y)

# 4. SAVE THE BRAIN
pickle.dump(model, open('risk_model.pkl', 'wb'))

print("✅ AI Model Trained on CSV data! 'risk_model.pkl' saved.")