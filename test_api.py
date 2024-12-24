import requests

#API Test
def test_recipe_api():
    url = "http://localhost:8000/ask"
    question = {"question": "What is the recipe for a carbonara"}

    response = requests.post(url, json=question)

    if response.status_code == 200:
        print("Answer:", response.json()["answer"])
    else:
        print("Error:", response.status_code, response.text)

if __name__ == "__main__":
    test_recipe_api()

