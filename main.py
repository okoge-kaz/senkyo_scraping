import time
import os


from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.select import Select
import pandas as pd

RESET_LIMIT: int = 600
reset_count: int = 0


def get_party_names(html_data):
    '''選挙ドットコムから政党名一覧を取得したのち、そのデータをstring[]で返す'''
    party_names: list = []
    party_names_html = html_data.find(id='p_seijika_search_party')
    # print(party_names_html.select) for debug
    party_names_option_tags = party_names_html.find_all('option')
    for party_name_option in party_names_option_tags:
        if party_name_option.string is None:
            continue
        party_names.append(party_name_option.string)
    return party_names


def change_id_into_name(id: int):
    mapping: dict = {
        1: '北海道',
        2: '青森県',
        3: '岩手県',
        4: '宮城県',
        5: '秋田県',
        6: '山形県',
        7: '福島県',
        8: '茨城県',
        9: '栃木県',
        10: '群馬県',
        11: '埼玉県',
        12: '千葉県',
        13: '東京都',
        14: '神奈川県',
        15: '新潟県',
        16: '富山県',
        17: '石川県',
        18: '福井県',
        19: '山梨県',
        20: '長野県',
        21: '岐阜県',
        22: '静岡県',
        23: '愛知県',
        24: '三重県',
        25: '滋賀県',
        26: '京都府',
        27: '大阪府',
        28: '兵庫県',
        29: '奈良県',
        30: '和歌山県',
        31: '鳥取県',
        32: '島根県',
        33: '岡山県',
        34: '広島県',
        35: '山口県',
        36: '徳島県',
        37: '香川県',
        38: '愛媛県',
        39: '高知県',
        40: '福岡県',
        41: '佐賀県',
        42: '長崎県',
        43: '熊本県',
        44: '大分県',
        45: '宮崎県',
        46: '鹿児島県',
        47: '沖縄県'
    }
    return mapping[id]


def is_exist_check(soup):
    target_html_data = soup.find(class_='p_seijika_search_result_table_wrapp')
    check_target_data = target_html_data.find(class_='ygreenk')
    if check_target_data is None:
        return False
    else:
        return True


def fetch_politician_data(driver):
    '''続きを見るがある限りずっと、それを押し続け、データを格納する。'''
    is_exist_flag: bool = True  # 続きを見る のフラグ
    while(is_exist_flag):
        new_html = driver.page_source
        soup = BeautifulSoup(new_html, 'lxml')

        is_exist_flag = is_exist_check(soup)
        if is_exist_flag:
            # 続きをみるを押す
            target_p_tag = driver.find_element_by_class_name('ygreenk')
            # target_p_tag.find_element_by_tag_name('span').click()
            driver.execute_script("arguments[0].click();", target_p_tag.find_element_by_tag_name('span'))
            time.sleep(3)
    # この時点で全てのデータが出ている
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')

    target_search_result_table_html = soup.find(class_='p_seijika_search_result_table')
    # print(target_search_result_table_html) # for debug
    data = extract_politician_detail_data(target_search_result_table_html)
    return data


def extract_politician_detail_data(html):
    '''beautiful soupで抽出したデータを使って基本情報をとっていく'''
    politician_data: dict = {}
    # dict型にするための工夫
    name: list = []
    party: list = []
    age: list = []
    sex: list = []
    picture_url: list = []
    kana_name: list = []
    detail_url: list = []
    blog_url: list = []
    #
    target_tables = html.find_all('tbody')
    for target_table in target_tables:
        targets = target_table.find_all('tr')
        for target in targets:
            # targetは政治家一人分のデータ
            res = politician_data_shaping(target)
            name.append(res.name)
            party.append(res.party)
            age.append(res.age)
            sex.append(res.sex)
            picture_url.append(res.picture_url)
            kana_name.append(res.kana_name)
            detail_url.append(res.detail_url)
            blog_url.append(res.blog_url)
    # dictにlistを代入
    politician_data['name'] = name
    politician_data['kana_name'] = kana_name
    politician_data['party'] = party
    politician_data['detail_url'] = detail_url
    politician_data['picture_url'] = picture_url
    politician_data['age'] = age
    politician_data['sex'] = sex
    politician_data['blog_url'] = blog_url
    return politician_data


def politician_data_shaping(html):
    '''1人分のデータになったhtmlを整形し、適切な型に変換する'''
    detail_data = html.find_all('td')
    # 詳細
    image_tag = detail_data[0]
    name_tag = detail_data[1]
    party = detail_data[2].string
    age = detail_data[3].string
    sex = detail_data[4].string
    blog_url = detail_data[5]
    # 整形
    picture_url = image_tag.find('img')['src']
    name = name_tag.find('a').string
    kana_name = name_tag.find('span').string
    detail_url = 'https://go2senkyo.com/' + name_tag.find('a')['href']
    try:
        blog_url = 'https://go2senkyo.com/' + blog_url.find('a')['href']
    except TypeError:
        blog_url = None
    # Politician型に代入
    res: Politician = Politician(name, party, age, sex, picture_url, kana_name, detail_url, blog_url)
    return res


class Politician:
    def __init__(self, name, party, age, sex, picture_url, kana_name, detail_url, blog_url):
        self.name = name
        self.party = party
        self.age = age
        self.sex = sex
        self.picture_url = picture_url
        self.kana_name = kana_name
        self.detail_url = detail_url
        self.blog_url = blog_url


def get_city_names(driver):
    '''都道府県名から市町村につながる情報をえる'''
    city_names_data: dict = {}
    for prefecture_id in range(1, 48):
        # selenium select
        search_prefecture_select = Select(driver.find_element_by_id('p_seijika_search_pref'))
        # select by value
        search_prefecture_select.select_by_value(str(prefecture_id))
        time.sleep(0.5)
        # 市区町村・町名を調べる
        city_names_list: list = []  # string[]
        # page source を取得
        html = driver.page_source
        soup = BeautifulSoup(html, 'lxml')
        # 処理 start
        city_names_html = soup.find(id='p_seijika_search_city')
        city_names_option_tags = city_names_html.find_all('option')
        for city_name_option_tag in city_names_option_tags:
            if city_name_option_tag.string == "市区町村・町名を選択":
                continue
            city_names_list.append(city_name_option_tag.string)
        # 処理end
        city_names_data[prefecture_id] = city_names_list
    return city_names_data


def main():
    CurrentPath = os.getcwd()
    driver = webdriver.Chrome()
    url: str = 'https://go2senkyo.com/seijika'
    driver.get(url)
    time.sleep(2)
    html = driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    # target_tbody = soup.find('tbody')
    party_names = get_party_names(soup)
    # print(party_names) # for debug

    # 市区町村・町名を選択
    city_names_data = get_city_names(driver)
    # print(city_names_data) # for debug

    # main処理
    for party_name in party_names:
        for prefecture_id in range(1, 48):
            for city_name in city_names_data[prefecture_id]:
                # init driver
                driver = webdriver.Chrome()
                driver.get(url)
                time.sleep(2)
                # selenium select
                search_party_select = Select(driver.find_element_by_id('p_seijika_search_party'))
                search_prefecture_select = Select(driver.find_element_by_id('p_seijika_search_pref'))
                search_city_select = Select(driver.find_element_by_id('p_seijika_search_city'))
                # select by visible text
                search_party_select.select_by_visible_text(party_name)
                time.sleep(0.5)
                # select by value
                search_prefecture_select.select_by_value(str(prefecture_id))
                time.sleep(0.5)
                # select by visible text
                search_city_select.select_by_visible_text(city_name)
                time.sleep(0.5)
                # 検索
                search_button = driver.find_element_by_id('search_submit')
                search_button.click()
                # 検索の表示に時間がかかる
                time.sleep(5)
                # 情報取得
                data = fetch_politician_data(driver)
                # output
                df = pd.DataFrame(data)
                df.to_csv(CurrentPath + '/out/' + party_name + '_' + change_id_into_name(prefecture_id) + '_' + city_name + '.csv', encoding='utf-8_sig')
                df.to_json(CurrentPath + '/output/' + party_name + '_' + change_id_into_name(prefecture_id) + '_' + city_name + '.json', force_ascii=False)
                # end
                break
            break
        break

    # 詳細データ収集
    


if __name__ == '__main__':
    start = time.time()
    main()
    print(time.time() - start)
