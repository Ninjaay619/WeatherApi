from flask import Flask, render_template, jsonify, request
import requests
import os
import re
from datetime import datetime

app = Flask(__name__)
# -------------------- 原本的函式 --------------------
def get_weather_data(location):
    url = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {
        "Authorization": "CWA-F12A0212-72D3-4224-9117-5E5836E197FE",  # 或直接放你的 API key
        "format": "JSON",
        "locationName": location
    }
    headers = {"accept": "application/json"}
    response = requests.get(url, params=params, headers=headers, verify=False)
    data = response.json()
    return data


def simplify_data(data):
    location_data = data['records']['location'][0]
    weather_elements = location_data['weatherElement']
    simplified_data = {'location': location_data['locationName']}

    for element in weather_elements:
        element_name = element['elementName']
        for time in element['time']:
            start_time = time['startTime']
            if start_time not in simplified_data:
                simplified_data[start_time] = {}
            parameter = time['parameter']
            parameter_str = parameter['parameterName']
            if 'parameterUnit' in parameter:
                parameter_str += f" {parameter['parameterUnit']}"
            end_time = time['endTime']
            if end_time not in simplified_data[start_time]:
                simplified_data[start_time][end_time] = {}
            simplified_data[start_time][end_time][element_name] = parameter_str
    return simplified_data


def get_current_weather(simplified_data):
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        for start_time in simplified_data:
            if start_time == 'location':
                continue
            for end_time in simplified_data[start_time]:
                if start_time <= now <= end_time:
                    return simplified_data[start_time][end_time]
        # 如果沒有符合時間，回傳第一個時間段的資料
        for start_time in simplified_data:
            if start_time != 'location':
                first_end = list(simplified_data[start_time].keys())[0]
                return simplified_data[start_time][first_end]
    except Exception as e:
        print(f"An error occurred: {e}")
    return None


def check_location_in_message(message):
    locations = [
        "臺北市", "臺中市", "臺南市", "高雄市",
        "新北市", "桃園市", "新竹市", "苗栗縣",
        "彰化縣", "南投縣", "雲林縣", "嘉義市",
        "嘉義縣", "屏東縣", "宜蘭縣", "花蓮縣",
        "臺東縣", "澎湖縣"
    ]
    corrected_message = re.sub("台", "臺", message)
    local = corrected_message.split("_")
    for location in locations:
        if re.search(local[0], location):
            return location
    return locations[0]  # 預設回傳第一個城市
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ping")
def ping():
    return {"status": "ok"}

@app.route("/weather", methods=["GET"])
def weather_api():
    city = request.args.get("city")
    if not city:
        return jsonify({"error": "請提供 city 參數"}), 400

    try:
        location = check_location_in_message(city)
        weather_data = get_weather_data(location)
        simplified_data = simplify_data(weather_data)
        current_weather = get_current_weather(simplified_data)

        if current_weather is None:
            return jsonify({"error": "無法取得天氣資料", "raw_data": weather_data}), 500

        return jsonify({
            "query": city,
            "location": location,
            "weather": current_weather
        })

    except Exception as e:
        # 回傳錯誤訊息給前端，方便除錯
        return jsonify({
            "error": str(e),
            "city": city
        }), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
