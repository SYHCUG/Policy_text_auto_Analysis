'''
Author:Yinghui,Shao
Date:2025-03-25
PROJECT_NAME: 爬取中国政府网站的政策文件信息并保存到 CSV 文件
'''

from selenium import webdriver
from selenium.common import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import sys
import urllib.parse

# 设置控制台输出编码以支持中文
sys.stdout.reconfigure(encoding='utf-8')

# 初始化浏览器
driver = webdriver.Edge()

# 查询参数配置
query = "人工智能"
encoded_query = urllib.parse.quote(query)
url = f'https://sousuo.www.gov.cn/zcwjk/policyDocumentLibrary?q={encoded_query}&t=zhengcelibrary&orpro='
print("访问的网址:", url)

# 重试请求以处理连接重置错误
def retry_request(max_retries=5):
    retries = 0
    while retries < max_retries:
        try:
            driver.get(url)
            return  # 成功请求后退出循环
        except (ConnectionResetError, Exception) as e:
            retries += 1
            print(f"第 {retries}/{max_retries} 次重试，错误: {e}")
            time.sleep(5)  # 等待后重试
            if retries == max_retries:
                print("达到最大重试次数，程序退出。")
                driver.quit()
                sys.exit()  # 终止程序

retry_request()

# 等待页面加载准备
wait = WebDriverWait(driver, 10)
data_list = []

while True:
    try:
        # 等待加载相关内容
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'dys_middle_result_content_item')))
        items = driver.find_elements(By.CLASS_NAME, 'dys_middle_result_content_item')

        for item in items:
            try:
                # 提取标题、链接、概要等信息
                a_tag = item.find_element(By.TAG_NAME, 'a')
                title = a_tag.find_element(By.CLASS_NAME, 'dysMiddleResultConItemTitle').text
                url = a_tag.get_attribute('href')
                summary = item.find_element(By.CLASS_NAME, 'dysMiddleResultConItemMemo').text

                # 提取类型和发布时间
                type_time_p = item.find_element(By.CLASS_NAME, 'dysMiddleResultConItemRelevant.clearfix1')
                spans = type_time_p.find_elements(By.TAG_NAME, 'span')

                policy_type = spans[0].text if len(spans) > 0 else ''
                publish_time = spans[1].text if len(spans) > 1 else ''

                # 将提取的数据存入列表
                data_list.append({
                    '标题': title,
                    '类型': policy_type,
                    '发布时间': publish_time,
                    '概要': summary,
                    'URL': url
                })
                print(f'成功爬取: {title}')
            except StaleElementReferenceException:
                print("过期元素引用异常，重试数据提取。")
                continue
            except Exception as e:
                print(f'提取项目时发生错误: {e}')

        # 处理翻页
        try:
            next_button = driver.find_element(By.CLASS_NAME, 'btn-next')
            # 直接检查接按钮的 disabled 属性
            if next_button.get_attribute('disabled') is not None:
                print("已到达最后一页，没有更多页面。")
                break
            else:
                next_button.click()
                # 等待新页面内容加载
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'dys_middle_result_content_item')))
        except NoSuchElementException:
            print("未找到下一页按钮，结束爬取。")
            break

    except Exception as e:
        print(f"爬取过程中发生错误: {e}")
        break

# 保存数据到 CSV 文件
data = pd.DataFrame(data_list, columns=['标题', '类型', '发布时间', '概要', 'URL'])
data.to_csv(f'{query}政策文件.csv', index=False, encoding='utf-8-sig')

# 关闭浏览器
driver.quit()