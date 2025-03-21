import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import re
import json
import time
import sys 
import random
from selenium import webdriver
from selenium.webdriver.edge.options import Options  
from selenium.webdriver.edge.service import Service  
from webdriver_manager.microsoft import EdgeChromiumDriverManager  


# 定义网页URL基础部分
BASE_URL = "https://res1999.huijiwiki.com"

# 创建输出目录
OUTPUT_DIR = "output"
DIALOGUES_DIR = os.path.join(OUTPUT_DIR, "dialogues")
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DIALOGUES_DIR, exist_ok=True)

# 添加一个新函数，用于检查小节是否已经爬取
def is_episode_crawled(chapter_dir, episode_cn_title):
    """检查小节是否已经爬取过"""
    episode_filename = f"{episode_cn_title}.json"
    episode_filepath = os.path.join(chapter_dir, episode_filename)
    
    # 检查文件是否存在且不为空
    if os.path.exists(episode_filepath):
        try:
            with open(episode_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 如果文件存在且包含对话数据，则认为已爬取
                return len(data) > 0
        except:
            # 如果文件存在但无法解析JSON，则认为未爬取
            return False
    
    # 文件不存在，未爬取
    return False


def get_page_content_from_selenium(url, max_retries=3, retry_delay=5):
    """使用Selenium从URL获取网页内容并返回BeautifulSoup对象，添加重试机制"""
    print(f"使用Selenium访问 {url}...")
    
    # 配置Edge选项
    edge_options = Options()
    edge_options.add_argument("--headless")  # 无头模式，不显示浏览器窗口
    edge_options.add_argument("--disable-gpu")
    edge_options.add_argument("--window-size=1920,1080")
    edge_options.add_argument("--no-sandbox")
    edge_options.add_argument("--disable-dev-shm-usage")
    edge_options.add_argument("--disable-extensions")  # 禁用扩展，减少错误
    edge_options.add_argument("--disable-logging")  # 减少日志输出
    edge_options.add_argument("--log-level=3")  # 仅显示致命错误
    edge_options.add_argument(f"user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0")
    
    for attempt in range(max_retries):
        try:
            # 初始化Edge WebDriver
            driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=edge_options)
            
            # 设置页面加载超时
            driver.set_page_load_timeout(60)
            
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
            driver.quit() if 'driver' in locals() else None
            print(f"尝试 {attempt+1}/{max_retries} 失败: {e}")
            if attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)  # 指数退避
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"达到最大重试次数，无法获取页面 {url}")
                return None


def extract_chinese_dialogue(url):
    """从指定URL提取对话内容"""
    print(f"正在提取页面 {url} 的对话内容...")
    soup = get_page_content_from_selenium(url)
    
    if not soup:
        print(f"无法获取页面 {url} 的内容")
        return []

    # 找到所有story-text元素，这些元素包含对话内容
    story_texts = soup.find_all("div", class_="story-text")
    
    dialogues = []
    
    for story in story_texts:
        content_divs = story.find_all("div")
        
        # 跳过空内容
        if not content_divs:
            continue
            
        # 提取对话内容
        if len(content_divs) == 1:
            dialogue = content_divs[0].text.strip()
            speaker = "旁白"
        else:
            speaker = content_divs[0].text.strip()
            dialogue = content_divs[1].text.strip()
        
        if dialogue:
            dialogues.append({
                "speaker": speaker,
                "dialogue": dialogue
            })
    
    return dialogues


def load_story_structure():
    """加载故事结构数据"""
    structure_path = os.path.join(OUTPUT_DIR, "story_structure.json")
    try:
        with open(structure_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载故事结构数据失败: {e}")
        return None


def save_to_json(data, filename):
    """保存数据到JSON文件"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"数据已保存到 {filepath}")
    return filepath


def main():
    print("开始抓取重返未来1999游戏剧情的文本...")
    
    # 加载故事结构
    story_structure = load_story_structure()
    if not story_structure:
        print("无法加载故事结构，程序退出")
        return
    
    # 统计变量
    total_episodes = 0
    already_crawled = 0
    newly_crawled = 0
    failed_episodes = 0
    
    # 遍历故事结构中的每个章节
    for chapter in story_structure["main_story"]:
        chapter_cn_title = chapter["chinese_title"]
        # 创建章节目录
        chapter_dir = os.path.join(DIALOGUES_DIR, chapter_cn_title)
        os.makedirs(chapter_dir, exist_ok=True)
        chapter_en_title = chapter["english_title"]
        print(f"\n开始处理章节: {chapter_cn_title} ({chapter_en_title})")
        
        # 遍历章节中的每个小节
        for episode in chapter["episodes"]:
            total_episodes += 1
            episode_cn_title = episode["chinese_title"]
            episode_en_title = episode["english_title"]
            episode_link = episode["link"]
            
            # 检查是否已经爬取过
            if is_episode_crawled(chapter_dir, episode_cn_title):
                print(f"  跳过已爬取的小节: {episode_cn_title} ({episode_en_title})")
                already_crawled += 1
                continue
            
            # 构建完整URL
            full_url = f"{BASE_URL}{episode_link}"
            print(f"  处理小节: {episode_cn_title} ({episode_en_title})")
            
            try:
                # 提取对话
                dialogues = extract_chinese_dialogue(full_url)
                if not dialogues:
                    print(f"  警告: 未能从 {episode_cn_title} 提取到对话，将在下次运行时重试")
                    failed_episodes += 1
                    continue
                    
                print(f"  成功提取 {len(dialogues)} 条对话")
                newly_crawled += 1
                
                # 保存小节对话
                episode_filename = f"{episode_cn_title}.json"
                episode_filepath = os.path.join(DIALOGUES_DIR, chapter_cn_title, episode_filename)
                with open(episode_filepath, 'w', encoding='utf-8') as f:
                    json.dump(dialogues, f, ensure_ascii=False, indent=2)
                
                # 添加随机延迟，避免请求过于频繁
                delay = random.uniform(5, 10)  # 增加延迟时间
                print(f"  等待 {delay:.2f} 秒后继续...")
                time.sleep(delay)
                
            except Exception as e:
                print(f"  处理小节 {episode_cn_title} 时出错: {e}")
                print("  将在下次运行时重试该小节")
                failed_episodes += 1
                continue
    
    # 打印统计信息
    print("\n爬取统计:")
    print(f"总小节数: {total_episodes}")
    print(f"已爬取小节数: {already_crawled}")
    print(f"新爬取小节数: {newly_crawled}")
    print(f"失败小节数: {failed_episodes}")
    print(f"完成率: {((already_crawled + newly_crawled) / total_episodes) * 100:.2f}%")
    
    print("\n抓取完成！所有对话已保存")

if __name__ == "__main__":
    main()