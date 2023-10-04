import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By

# 전역 변수 선언
restaurant_data = {}
driver = None
restaurant_name = ""

# 식당 정보
def get_restaurant_info():
    global restaurant_name, restaurant_data  # 전역 변수 참조

    # (0). 식당 이름 --------------------------------------------------------------------
    restaurant_name = driver.find_elements(By.CSS_SELECTOR, '.tit_location')[1].text
    print(restaurant_name)
    
    restaurant_data = {restaurant_name: []}

# 상위 15개 리뷰 가져오기
def fetch_reviews():
    global restaurant_name, restaurant_data, driver  # 전역 변수 참조

    more_button_count = 0

    # 더보기 버튼이 있으면 4번만 클릭
    while True:
        more_button = driver.find_elements(By.XPATH, '//span[text()="후기 더보기"]')
        if not more_button or more_button_count >= 4:
            break

        more_button[0].click()
        more_button_count += 1
        time.sleep(1)

    # 리뷰들 리스트
    review_list = driver.find_elements(By.CSS_SELECTOR, '.list_evaluation > li')[:15]

    for index in range(len(review_list)):
        process_review_data(review_list[index], index + 1)

# 리뷰에서 정보 추출
def process_review_data(review, index):
    global restaurant_name, restaurant_data  # 전역 변수 참조

    # (1) 작성자 이름 --------------------------------------------------------------------
    name = review.find_elements(By.CSS_SELECTOR, '.link_user')[0].text

    # (2) 후기 작성 수 --------------------------------------------------------------------
    review_number = int(review.find_elements(By.CSS_SELECTOR, '.txt_desc')[0].text)

    # (3) 별점 평균 --------------------------------------------------------------------
    average_star = float(review.find_elements(By.CSS_SELECTOR, '.txt_desc')[1].text)

    # (4) 부여한 별점 --------------------------------------------------------------------
    star_element = driver.find_elements(By.CSS_SELECTOR, '.ico_star.inner_star')[index + 1]

    style_attribute = star_element.get_attribute('style')
    width_value = None

    if style_attribute:
        width_match = re.search(r'width: (\d+)%;', style_attribute)
        if width_match:
            width_value = width_match.group(1)

    star = int(width_value) / 20

    # (5) 추천 포인트 --------------------------------------------------------------------
    recommend_point = review.find_elements(By.CSS_SELECTOR, '.chip_likepoint')
    recommend_point_list = [rp.text for rp in recommend_point]

    # (6) 후기 내용 --------------------------------------------------------------------
    review_content = review.find_elements(By.CSS_SELECTOR, '.txt_comment > span')[0].text
    # --------------------------------------------------------------------

    # JSON 파일로 저장
    save_review_to_json(index, name, review_number, average_star, star, recommend_point_list, review_content)

    # 리뷰 정보 화면에 출력
    print_info(index, name, review_number, average_star, star, recommend_point_list, review_content)

# Json 파일로 저장
def save_review_to_json(index, name, review_number, average_star, star, recommend_point_list, review_content):
    global restaurant_name, restaurant_data  # 전역 변수 참조

    review_dict = {
        'id': index,
        'reviewer_name': name,
        'review_count': review_number,
        'average_rating': average_star,
        'rating': star,
        'recommend_point': recommend_point_list,
        'review_content': review_content
    }
    
    restaurant_data[restaurant_name].append(review_dict)

# 리뷰 정보 터미널에 출력
def print_info(index, name, review_number, average_star, star, recommend_point_list, review_content) :
    print('id : ', index)
    print('이름 : ', name)
    print('후기 작성 수 : ', review_number)
    print('별점 평균 : ', average_star)
    print('부여한 별점 : ', star)
    print('추천 포인트 : ', recommend_point_list)
    print('후기 내용 : ', review_content)
    print()


## 메인함수 ## 
def main():
    global driver  # 전역 변수 참조
    
    url = "https://place.map.kakao.com/248225764"
    driver = webdriver.Chrome()  # 드라이버 경로
    driver.get(url)
    time.sleep(1)

    get_restaurant_info()
    fetch_reviews()

    # JSON 파일로 저장
    with open('crawling_data.json', 'w', encoding='utf-8') as f:
        json.dump(restaurant_data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()