import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
from difflib import SequenceMatcher
import pickle
import joblib


class EnhancedStrategyClassifier:
    # Using a local model that I have to research more about, will upload the model to HuggingFace once
    # I complete more robust testing

    def __init__(self, model_path="merge_strategy_model.pkl"):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.label_encoder = LabelEncoder()
        self.strategies = ['TAKE_A', 'TAKE_B', 'MERGE_BOTH', 'SMART_MERGE', 'NEEDS_LLM']
        try:
            self._load_model(model_path)
        except FileNotFoundError:
            self.model = RandomForestClassifier(n_estimators=100, max_depth=10)

    def _load_model(self, model_path):
        saved_data = joblib.load(model_path)
        self.model = saved_data['model']
        self.vectorizer = saved_data['vectorizer']
        self.label_encoder = saved_data['label_encoder']

    def save_model(self, model_path="merge_strategy_model.pkl"):
        saved_data = {
            'model': self.model,
            'vectorizer': self.vectorizer,
            'label_encoder': self.label_encoder
        }
        joblib.dump(saved_data, model_path)

    def _extract_features(self, conflict):
        # Code similarity features
        similarity = SequenceMatcher(None, conflict['a'], conflict['b']).ratio()
        combined_text = f"{conflict['a']} {conflict['b']}"
        text_features = self.vectorizer.transform([combined_text]).toarray()

        len_diff = abs(len(conflict['a']) - len(conflict['b'])) / max(len(conflict['a']), len(conflict['b']))
        has_imports_a = 'import' in conflict['a'] or 'from' in conflict['a']
        has_imports_b = 'import' in conflict['b'] or 'from' in conflict['b']

        additional_features = np.array([
            similarity,
            len_diff,
            has_imports_a,
            has_imports_b,
        ])

        return np.hstack([text_features[0], additional_features])

    def train(self, conflicts, labels):
        all_text = [f"{c['a']} {c['b']}" for c in conflicts]
        self.vectorizer.fit(all_text)

        X = np.array([self._extract_features(conflict) for conflict in conflicts])
        y = self.label_encoder.fit_transform(labels)
        self.model.fit(X, y)

        scores = cross_val_score(self.model, X, y, cv=5)
        print(f"Model accuracy: {scores.mean():.2f} (+/- {scores.std() * 2:.2f})")

    def predict(self, conflict):

        return 'NEEDS_LLM', 0

        # TODO: Update with new ML based model to help classify the appropriate file to choose

        # features = self._extract_features(conflict)
        #
        # prediction = self.model.predict([features])[0]
        # strategy = self.label_encoder.inverse_transform([prediction])[0]
        #
        # probs = self.model.predict_proba([features])[0]
        # confidence = max(probs)

        # if confidence < 0.7:
        #     return 'NEEDS_LLM', confidence
        #
        # return strategy, confidence

    def predict_with_explanation(self, conflict):
        strategy, confidence = self.predict(conflict)

        similarity = SequenceMatcher(None, conflict['a'], conflict['b']).ratio()

        explanation = {
            'strategy': strategy,
            'confidence': confidence,
            'similarity_score': similarity,
            'analysis': {
                'code_similarity': f"{similarity:.2f}",
                'size_difference': f"{abs(len(conflict['a']) - len(conflict['b']))} characters",
                'has_imports': 'import' in conflict['a'] or 'import' in conflict['b']
            }
        }

        return explanation


