from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

def is_safe_for_diabetics(fruit):
    sugar = fruit.get("nutritions", {}).get("sugar", 0)
    return sugar < 10

def fetch_fruit_data():
    try:
        url = "https://www.fruityvice.com/api/fruit/all"
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print("API error")
            return []
    except Exception as e:
        print("API fetch error:", e)
        return []

@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        user = request.get_json()
        goal = (user.get("health_goal") or "immunity").lower()
        diabetic = (user.get("diabetic") or "no").lower()

        fruit_data = fetch_fruit_data()
        scored_fruits = []

        for fruit in fruit_data:
            name = fruit.get("name")
            sugar = fruit.get("nutritions", {}).get("sugar", 0)
            calories = fruit.get("nutritions", {}).get("calories", 0)
            protein = fruit.get("nutritions", {}).get("protein", 0)

            # Scoring logic based on new goals
            if goal == "weight loss":
                score = protein - calories
            elif goal == "immunity":
                score = protein
            elif goal == "energy":
                score = calories
            else:
                score = 0

            scored_fruits.append((name, sugar, calories, protein, score, fruit))

        scored_fruits.sort(key=lambda x: x[4], reverse=True)

        recommendations = []
        seen = set()

        for name, sugar, calories, protein, score, fruit in scored_fruits:
            if name in seen:
                continue
            if diabetic == "yes" and not is_safe_for_diabetics(fruit):
                continue
            if diabetic == "no" and is_safe_for_diabetics(fruit):
                continue
            recommendations.append({
                "fruit": name,
                "sugar": sugar,
                "calories": calories,
                "protein": protein
            })
            seen.add(name)
            if len(recommendations) >= 3:
                break

        # Fallback if no recommendations match
        if not recommendations:
            for name, sugar, calories, protein, score, fruit in scored_fruits:
                if name in seen:
                    continue
                recommendations.append({
                    "fruit": name,
                    "sugar": sugar,
                    "calories": calories,
                    "protein": protein
                })
                seen.add(name)
                if len(recommendations) >= 3:
                    break

        return jsonify({"recommendations": recommendations})

    except Exception as e:
        print("Server error:", e)
        return jsonify({"error": "Server error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
