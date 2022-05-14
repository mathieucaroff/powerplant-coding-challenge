import json
import sys
import urllib.request

send_request = True
localhost_url = 'http://localhost:8888/productionplan'

def send_json(url: str, data: str):
    encoded_data = data.encode('utf-8')
    req = urllib.request.Request(url)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    req.add_header('Content-Length', len(encoded_data))
    response = urllib.request.urlopen(req, encoded_data)
    return response

def filename(suffix):
    return f"resource/example_payloads/payload{suffix}.json"

if __name__ == "__main__":
    for file in [*map(filename, range(1, 4))]:
        with open(file, "rt") as file_handler:
            problem_text = file_handler.read()
        problem = json.loads(problem_text)
        answer = send_json(localhost_url, problem_text)
        print(answer.status)
        text = answer.read()
        data = json.loads(text)
        print(text)
        print("load", problem["load"])
        print("power", sum(piece["p"] for piece in data))
