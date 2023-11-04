# -*- coding: utf-8 -*-

import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from fastapi import FastAPI
from transformers import pipeline
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
sentiment_model = pipeline(model="WhitePeak/bert-base-cased-Korean-sentiment")
sum_model = pipeline("summarization", model="psyche/KoT5-summarization")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 출처 허용, 보안을 위해 필요에 따라 수정
    allow_methods=["*"],  # 모든 HTTP 메서드 허용, 보안을 위해 필요에 따라 수정
)

def fetch_reviews(url):
    restaurant_data = {}
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    time.sleep(1)

    restaurant_name = ""
    least_review_number = 3
    ave_relative_score = 0
    total_review = 0

    restaurant_name = driver.find_elements(By.CSS_SELECTOR, ".tit_location")[1].text
    print(restaurant_name)

    restaurant_data = {restaurant_name: []}

    while True:
        more_button = driver.find_elements(By.XPATH, '//span[text()="후기 더보기"]')
        if not more_button:
            break

        more_button[0].click()
        time.sleep(0.3)

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

    driver.quit()

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

    review_content = review.find_elements(By.CSS_SELECTOR, ".txt_comment > span")[0].text

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
    url = data.url
    print('url is ', url)
    # start = time.time()
    data = fetch_reviews(url)
    # math.factorial(100000)
    
    # print(f"{end - start:.5f} sec")

    end=time.time()
    pos_con = []
    neg_con = []
    con = []
    res_name = data["restaurant_name"]
    for review in data["review_data"][res_name]:
        if review["review_content"] != "":
            con.append(review["review_content"])
    for review in con:
        # print(sentiment_model(review)[0]["label"])
        # print(review)
        if sentiment_model(review)[0]["label"] == "LABEL_1":
            pos_con.append(review)
        elif sentiment_model(review)[0]["label"] == "LABEL_0":
            neg_con.append(review)
    positive_sum = ""
    for review in pos_con:
        positive_sum += review + "\n"

    negative_sum = ""
    for review in neg_con:
        negative_sum += review + "\n"

    sum_review = []
    sum_review.append(sum_model(positive_sum))
    sum_review.append(sum_model(negative_sum))
    average_star=data["average_relative_score"]
    # sum_review = [sum_model(positive_sum), sum_model(negative_sum)]
    return sum_review, average_star

@app.post("/test")
def returnHi():
    averageStar=3
    return averageStar

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=5000)