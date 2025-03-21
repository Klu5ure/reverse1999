import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re
import json
import time
import random
from selenium import webdriver
from selenium.webdriver.edge.options import Options  
from selenium.webdriver.edge.service import Service  
from webdriver_manager.microsoft import EdgeChromiumDriverManager  


# 定义网页URL
CHINESE_URL = "https://res1999.huijiwiki.com/wiki/NS-01"
ENGLISH_URL = "https://reverse1999.fandom.com/wiki/NS-1"

# 定义本地HTML文件路径
CHINESE_FILE = "chineseNs01.txt"
ENGLISH_FILE = "englishNs01.txt"

# 创建输出目录
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_page_content_from_url(url):
    """从URL获取网页内容并返回BeautifulSoup对象"""
    try:
        # 使用从浏览器复制的真实请求头
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "max-age=0",
            "priority": "u=0, i",
            "sec-ch-ua": "\"Chromium\";v=\"134\", \"Not:A-Brand\";v=\"24\", \"Microsoft Edge\";v=\"134\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0"
        }
        
        # 使用从浏览器复制的真实Cookie
        cookies = {
            "_ga": "GA1.2.742657181.1741685544",
            "_gid": "GA1.2.1317268045.1742265977",
            "__cf_bm": "grsundOqtsjxyfsLWtTwaEinwVJBpEMjAeYFqE03VmU-1742370020-1.0.1.1-0wvq7yDYYAxhmPICr2YUckQcaoKR1cJLrZ_x.NNhqi7Y.A5Ndktr_dyZdwAaDHWQUZ2W0dBPWP8d.4FcAX1z4TXyw7EKOtg_61j6EMeLe74",
            "_gat": "1",
            "_ga_N3DS04643Q": "GS1.2.1742370028.4.1.1742370038.50.0.0"
        }
        
        # 添加随机延时，避免频繁请求
        time.sleep(random.uniform(2, 5))
        
        # 创建会话对象，保持连接状态
        session = requests.Session()
        
        # 发送请求
        response = session.get(url, headers=headers, cookies=cookies, timeout=15)
        response.raise_for_status()  # 如果请求不成功则抛出异常
        

        # 返回BeautifulSoup对象
        return BeautifulSoup(response.text, "lxml")
    except Exception as e:
        print(f"获取网页 {url} 时出错: {e}")


def get_page_content_from_selenium(url):
    """使用Selenium从URL获取网页内容并返回BeautifulSoup对象"""
    print(f"使用Selenium访问 {url}...")
    
    # 配置Edge选项
    edge_options = Options()
    edge_options.add_argument("--headless")  # 无头模式，不显示浏览器窗口
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--window-size=1920,1080")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0")
    
    try:
        # 初始化Edge WebDriver
        driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=edge_options)
        
        # 访问URL
        driver.get(url)
        
        # 等待页面加载完成
        time.sleep(5)
        
        # 获取页面源代码
        page_source = driver.page_source
        
        # 关闭浏览器
        driver.quit()
        
        return BeautifulSoup(page_source, "lxml")
    except Exception as e:
        print(f"使用Selenium获取网页 {url} 时出错: {e}")



def get_page_content_from_file(file_path):
    """从本地文件获取网页内容并返回BeautifulSoup对象"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return BeautifulSoup(content, "lxml")
    except Exception as e:
        print(f"读取文件 {file_path} 时出错: {e}")
        return None


def extract_chinese_dialogue():
    """从中文Wiki提取对话内容"""
    print("正在提取中文对话内容...")
    soup = get_page_content_from_selenium(CHINESE_URL)
    
    # 找到包含对话的主要内容区域
    content_div = soup.find("div", class_="mw-parser-output")
    if not content_div:
        print("未找到主要内容区域")
        return []
    
    # 找到所有story-text元素，这些元素包含对话内容
    story_texts = content_div.find_all("div", class_="story-text")
    
    dialogues = []
    
    for story in story_texts:
        content_divs = story.find_all("div")
        
        # 根据div数量处理不同情况
        if len(content_divs) == 1:
            # 只有对话内容没有说话者
            dialogue = content_divs[0].text.strip()
            if dialogue:
                dialogues.append({
                    "speaker": "旁白",
                    "dialogue": dialogue,
                    "language": "中文"
                })
        else:
            # 处理有说话者的情况
            speaker = "旁白"
            # 第一个div是说话者名称
            if len(content_divs) >= 1:
                speaker_div = content_divs[0]
                speaker = speaker_div.text.strip("： ")  # 去除冒号和空格
            
            # 提取后续div中的对话内容
            for div in content_divs[1:]:
                dialogue = div.text.strip()
                if dialogue:
                    dialogues.append({
                        "speaker": speaker,
                        "dialogue": dialogue,
                        "language": "中文"
                    })
    
    return dialogues


def extract_english_dialogue():
    """从英文Wiki提取对话内容"""
    print("正在提取英文对话内容...")
    soup = get_page_content_from_selenium(ENGLISH_URL)
    
    # 找到包含对话的主要内容区域 - 英文使用表格结构
    tables = soup.find_all("table", class_="wikitable")
    if not tables:
        print("未找到对话表格")
        return []
    
    dialogues = []
    current_speaker = ""
    
    # 遍历所有表格行
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            # 跳过标题行
            if row.find("td", colspan="5"):
                continue
                
            # 获取所有单元格
            cells = row.find_all("td")
            
            # 如果只有一个单元格且有colspan属性，这可能是旁白
            if len(cells) == 1 and cells[0].has_attr("colspan"):
                text = cells[0].text.strip()
                if text:
                    dialogues.append({"speaker": "Narrator", "dialogue": text, "language": "English"})
                continue
                
            # 正常的对话行应该有两个单元格：角色和对话内容
            if len(cells) == 2:
                # 第一个单元格包含角色信息
                speaker_cell = cells[0]
                # 尝试从单元格中提取角色名称
                speaker_div = speaker_cell.find("div", style=lambda s: s and "align-self: flex-end" in s)
                if speaker_div:
                    speaker = speaker_div.text.strip()
                else:
                    speaker = "Unknown"
                
                # 第二个单元格包含对话内容
                dialogue = cells[1].text.strip()
                
                if dialogue:
                    if speaker:
                        current_speaker = speaker
                    dialogues.append({"speaker": current_speaker, "dialogue": dialogue, "language": "English"})
    
    
    
    return dialogues


def align_dialogues(chinese_dialogues, english_dialogues):
    """基于数量校验的精确顺序匹配"""
    print("正在执行顺序匹配...")
    
    # 检查对话数量是否一致
    if len(chinese_dialogues) != len(english_dialogues):
        print(f"⚠️ 中英文对话数量不一致（中文：{len(chinese_dialogues)}，英文：{len(english_dialogues)}）")
        return pd.DataFrame()
    
    aligned_data = []
    
    # 使用zip进行精确顺序匹配
    for cn, en in zip(chinese_dialogues, english_dialogues):
        aligned_data.append({
            "chinese_speaker": cn["speaker"],
            "chinese_text": cn["dialogue"],
            "english_speaker": en["speaker"],
            "english_text": en["dialogue"]
        })
    
    return pd.DataFrame(aligned_data)


def save_to_csv(df, filename):
    """保存数据到CSV文件"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    print(f"数据已保存到 {filepath}")
    return filepath


def save_to_excel(df, filename):
    """保存数据到Excel文件"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        # 尝试保存到Excel文件
        df.to_excel(filepath, index=False, engine="openpyxl")
        print(f"数据已保存到 {filepath}")
    except PermissionError:
        # 如果文件被占用，尝试使用不同的文件名
        base, ext = os.path.splitext(filename)
        new_filename = f"{base}_new{ext}"
        new_filepath = os.path.join(OUTPUT_DIR, new_filename)
        print(f"文件 {filepath} 可能已被打开，尝试保存到 {new_filepath}")
        df.to_excel(new_filepath, index=False, engine="openpyxl")
        print(f"数据已保存到 {new_filepath}")
        return new_filepath
    except Exception as e:
        # 处理其他可能的异常
        print(f"保存Excel文件时出错: {e}")
        print("尝试仅保存CSV格式...")
        return None
    
    return filepath

def save_to_json(data, filename):
    """保存数据到JSON文件"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"数据已保存到 {filepath}")
    return filepath


def main():
    print("开始抓取重返未来1999游戏剧情的中英文本...")
    
    # 提取中文对话
    chinese_dialogues = extract_chinese_dialogue()
    print(f"成功提取 {len(chinese_dialogues)} 条中文对话")
    
    # 提取英文对话
    english_dialogues = extract_english_dialogue()
    print(f"成功提取 {len(english_dialogues)} 条英文对话")
    
    # 将中文对话和英文对话分别保存为JSON
    save_to_json(chinese_dialogues, "chinese_dialogues.json")
    save_to_json(english_dialogues, "english_dialogues.json")
    
    # 尝试对齐中英文对话并保存
    aligned_df = align_dialogues(chinese_dialogues, english_dialogues)
    if not aligned_df.empty:
        aligned_data = aligned_df.to_dict('records')
        save_to_json(aligned_data, "aligned_dialogues.json")
    
    print("抓取完成！")

if __name__ == "__main__":
    main()