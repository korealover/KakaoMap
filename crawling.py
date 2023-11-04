import json
import time
import re
from selenium import webdriver
from selenium.webdriver.common.by import By

# ���� ���� ����
restaurant_data = {}
driver = None
restaurant_name = ""

# �Ĵ� ����
def get_restaurant_info():
    global restaurant_name, restaurant_data  # ���� ���� ����

    # (0). �Ĵ� �̸� --------------------------------------------------------------------
    restaurant_name = driver.find_elements(By.CSS_SELECTOR, '.tit_location')[1].text
    print(restaurant_name)
    
    restaurant_data = {restaurant_name: []}

# ���� 15�� ���� ��������
def fetch_reviews():
    global restaurant_name, restaurant_data, driver  # ���� ���� ����

    more_button_count = 0

    # ������ ��ư�� ������ 4���� Ŭ��
    while True:
        more_button = driver.find_elements(By.XPATH, '//span[text()="�ı� ������"]')
        if not more_button or more_button_count >= 4:
            break

        more_button[0].click()
        more_button_count += 1
        time.sleep(1)

    # ����� ����Ʈ
    review_list = driver.find_elements(By.CSS_SELECTOR, '.list_evaluation > li')[:15]

    for index in range(len(review_list)):
        process_review_data(review_list[index], index + 1)

# ���信�� ���� ����
def process_review_data(review, index):
    global restaurant_name, restaurant_data  # ���� ���� ����

    # (1) �ۼ��� �̸� --------------------------------------------------------------------
    name = review.find_elements(By.CSS_SELECTOR, '.link_user')[0].text

    # (2) �ı� �ۼ� �� --------------------------------------------------------------------
    review_number = int(review.find_elements(By.CSS_SELECTOR, '.txt_desc')[0].text)

    # (3) ���� ��� --------------------------------------------------------------------
    average_star = float(review.find_elements(By.CSS_SELECTOR, '.txt_desc')[1].text)

    # (4) �ο��� ���� --------------------------------------------------------------------
    star_element = driver.find_elements(By.CSS_SELECTOR, '.ico_star.inner_star')[index + 1]

    style_attribute = star_element.get_attribute('style')
    width_value = None

    if style_attribute:
        width_match = re.search(r'width: (\d+)%;', style_attribute)
        if width_match:
            width_value = width_match.group(1)

    star = int(width_value) / 20

    # (5) ��õ ����Ʈ --------------------------------------------------------------------
    recommend_point = review.find_elements(By.CSS_SELECTOR, '.chip_likepoint')
    recommend_point_list = [rp.text for rp in recommend_point]

    # (6) �ı� ���� --------------------------------------------------------------------
    review_content = review.find_elements(By.CSS_SELECTOR, '.txt_comment > span')[0].text
    # --------------------------------------------------------------------

    # JSON ���Ϸ� ����
    save_review_to_json(index, name, review_number, average_star, star, recommend_point_list, review_content)

    # ���� ���� ȭ�鿡 ���
    print_info(index, name, review_number, average_star, star, recommend_point_list, review_content)

# Json ���Ϸ� ����
def save_review_to_json(index, name, review_number, average_star, star, recommend_point_list, review_content):
    global restaurant_name, restaurant_data  # ���� ���� ����

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

# ���� ���� �͹̳ο� ���
def print_info(index, name, review_number, average_star, star, recommend_point_list, review_content) :
    print('id : ', index)
    print('�̸� : ', name)
    print('�ı� �ۼ� �� : ', review_number)
    print('���� ��� : ', average_star)
    print('�ο��� ���� : ', star)
    print('��õ ����Ʈ : ', recommend_point_list)
    print('�ı� ���� : ', review_content)
    print()


## �����Լ� ## 
def main():
    global driver  # ���� ���� ����
    
    url = "https://place.map.kakao.com/248225764"
    driver = webdriver.Chrome()  # ����̹� ���
    driver.get(url)
    time.sleep(1)

    get_restaurant_info()
    fetch_reviews()

    # JSON ���Ϸ� ����
    with open('crawling_data.json', 'w', encoding='utf-8') as f:
        json.dump(restaurant_data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    main()