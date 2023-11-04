import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from fastapi import FastAPI
from transformers import pipeline
from helium import *
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

print("Server loading...")
app = FastAPI()
# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용, 보안을 위해 필요에 따라 수정
    allow_methods=["*"],  # 모든 HTTP 메서드 허용, 보안을 위해 필요에 따라 수정
)
print("Server loaded")

# 모델 로드
print("model loading...")
sentiment_model = pipeline(model="WhitePeak/bert-base-cased-Korean-sentiment")
sum_model = pipeline("summarization", model="psyche/KoT5-summarization")
print("model loaded")

# 웹 드라이버 생성
print("web driver loading...")
options = webdriver.ChromeOptions()
options.page_load_strategy = "none"
prefs = {
    "profile.default_content_setting_values": {
        "cookies": 2,
        "images": 2,
        "plugins": 2,
        "popups": 2,
        "geolocation": 2,
        "notifications": 2,
        "auto_select_certificate": 2,
        "fullscreen": 2,
        "mouselock": 2,
        "mixed_script": 2,
        "media_stream": 2,
        "media_stream_mic": 2,
        "media_stream_camera": 2,
        "protocol_handlers": 2,
        "ppapi_broker": 2,
        "automatic_downloads": 2,
        "midi_sysex": 2,
        "push_messaging": 2,
        "ssl_cert_decisions": 2,
        "metro_switch_to_desktop": 2,
        "protected_media_identifier": 2,
        "app_banner": 2,
        "site_engagement": 2,
        "durable_storage": 2,
    }
}
options.add_experimental_option("prefs", prefs)
options.add_argument("start-maximized")
options.add_argument("disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--headless")
driver = start_chrome(options=options)
print("web driver loaded")


def fetch_reviews(url):
    restaurant_data = {}
    driver.get(url)
    # 페이지 로딩 대기
    wait_until(Text("전체").exists, timeout_secs=10)

    restaurant_name = ""
    least_review_number = 3
    ave_relative_score = 0
    total_review = 0

    restaurant_name = driver.find_elements(By.CSS_SELECTOR, ".tit_location")[1].text

    restaurant_data = {restaurant_name: []}
    print("리뷰 조회 시작")
    while True:
        if Text("후기 더보기").exists():
            click(Text("후기 더보기"))
            time.sleep(0.1)
        else:
            print("더이상 후기가 없습니다.")
            break

    review_list = driver.find_elements(By.CSS_SELECTOR, ".list_evaluation > li")

    for index in range(len(review_list)):
        (
            name,
            review_number,
            average_star,
            star,
            recommend_point_list,
            review_content,
        ) = process_review_data(
            driver, review_list[index], least_review_number, total_review
        )

        if review_number < least_review_number:
            continue

        save_review_to_json(
            restaurant_name,
            restaurant_data,
            total_review,
            name,
            review_number,
            average_star,
            star,
            recommend_point_list,
            review_content,
        )

        total_review += 1
        ave_relative_score += average_star - star

    with open("crawling_data.json", "w", encoding="utf-8") as f:
        json.dump(restaurant_data, f, indent=4, ensure_ascii=False)

    return {
        "restaurant_name": restaurant_name,
        "average_relative_score": round(ave_relative_score / total_review, 2),
        "review_data": restaurant_data,
    }


def process_review_data(driver, review, least_review_number, total_review):
    name = review.find_elements(By.CSS_SELECTOR, ".link_user")[0].text
    review_number_text = review.find_elements(By.CSS_SELECTOR, ".txt_desc")[0].text
    review_number = int(review_number_text.replace(",", ""))
    average_star = float(review.find_elements(By.CSS_SELECTOR, ".txt_desc")[1].text)

    star_element = driver.find_elements(By.CSS_SELECTOR, ".ico_star.inner_star")[
        total_review + 1
    ]
    style_attribute = star_element.get_attribute("style")
    width_value = None

    if style_attribute:
        width_match = re.search(r"width: (\d+)%;", style_attribute)
        if width_match:
            width_value = width_match.group(1)

    star = int(width_value) / 20

    recommend_point = review.find_elements(By.CSS_SELECTOR, ".chip_likepoint")
    recommend_point_list = [rp.text for rp in recommend_point]

    review_content = review.find_elements(By.CSS_SELECTOR, ".txt_comment > span")[
        0
    ].text

    return name, review_number, average_star, star, recommend_point_list, review_content


def save_review_to_json(
    restaurant_name,
    restaurant_data,
    total_review,
    name,
    review_number,
    average_star,
    star,
    recommend_point_list,
    review_content,
):
    review_dict = {
        "id": total_review,
        "name": name,
        "review_count": review_number,
        "average_rating": average_star,
        "rating": star,
        "relative_score": star - average_star,
        "recommend_point": recommend_point_list,
        "review_content": review_content,
    }

    restaurant_data[restaurant_name].append(review_dict)

class InputData(BaseModel):
    url: str

@app.post("/")
def scrape_and_get_reviews(data: InputData):
    url=data.url
    start_time = time.time()
    print("fetch_reviews start")
    data = fetch_reviews(url)
    print("fetch_reviews end")

    pos_con = []
    neg_con = []
    con = []
    res_name = data["restaurant_name"]

    # 공백인 리뷰 제거
    for review in data["review_data"][res_name]:
        if review["review_content"] != "":
            con.append(review["review_content"])

    # 긍정 부정 리뷰 분류
    print("감정 분류 시작")
    for review in con:
        # print(sentiment_model(review)[0]["label"])
        # print(review)
        if sentiment_model(review)[0]["label"] == "LABEL_1":  # 긍정
            pos_con.append(review)
        elif sentiment_model(review)[0]["label"] == "LABEL_0":  # 부정
            neg_con.append(review)
    print("감정 분류 완료")

    positive_sum = ""
    for review in pos_con:
        positive_sum += review + "\n"
    negative_sum = ""
    for review in neg_con:
        negative_sum += review + "\n"

    sum_review = []
    print("리뷰 요약 시작")
    sum_review.append(sum_model(positive_sum, max_length=100, min_length=5))
    sum_review.append(sum_model(negative_sum, max_length=100, min_length=5))
    sum_review.append(data["average_relative_score"])
    print("리뷰 요약 완료")
    end_time = time.time()
    print("소요 시간 : ", end_time - start_time)
    average_star=data["average_relative_score"]

    return sum_review, average_star


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)