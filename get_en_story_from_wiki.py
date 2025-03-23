import requests
from bs4 import BeautifulSoup
import os
import json
import time
import random
import sys
from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager

# 英文版基础URL
BASE_URL = "https://reverse1999.fandom.com"  

# 输出目录配置
OUTPUT_DIR = "output"
EN_DIALOGUES_DIR = os.path.join(OUTPUT_DIR, "en_dialogues")
os.makedirs(EN_DIALOGUES_DIR, exist_ok=True)

def is_episode_crawled(chapter_dir, episode_en_title):
    """检查英文小节是否已爬取（复用中文版逻辑）"""
    episode_filename = f"{episode_en_title}.json"
    episode_filepath = os.path.join(chapter_dir, episode_filename)
    
    if os.path.exists(episode_filepath):
        try:
            with open(episode_filepath, 'r', encoding='utf-8') as f:
                return len(json.load(f)) > 0
        except:
            return False
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
    
    # 为每个会话创建唯一的用户数据目录
    import tempfile
    import uuid
    temp_dir = os.path.join(tempfile.gettempdir(), f"edge_user_data_{uuid.uuid4().hex}")
    edge_options.add_argument(f"--user-data-dir={temp_dir}")
    
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
            
            # 清理临时目录
            try:
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
                
            return BeautifulSoup(page_source, "lxml")
        except Exception as e:
            driver.quit() if 'driver' in locals() else None
            print(f"尝试 {attempt+1}/{max_retries} 失败: {e}")
            
            # 清理临时目录
            try:
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except:
                pass
                
            if attempt < max_retries - 1:
                wait_time = retry_delay * (attempt + 1)  # 指数退避
                print(f"等待 {wait_time} 秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"达到最大重试次数，无法获取页面 {url}")
                return None


def extract_english_dialogue(ENGLISH_URL):
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
            # 如果只有一个单元格且有colspan属性，这可能是旁白
            if len(cells) == 1 and cells[0].has_attr("colspan"):
                text = cells[0].text.strip()
                if text and text not in ["Pre-Battle", "Post-Battle"]:
                    dialogues.append({"english_speaker": "Narrator", "english_dialogue": text})
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
                    dialogues.append({"english_speaker": current_speaker, "english_dialogue": dialogue})
    
    
    
    return dialogues
    



def load_story_structure():
    """复用相同的故事结构加载方法"""
    structure_path = os.path.join(OUTPUT_DIR, "fandom_story_structure_en.json")
    try:
        with open(structure_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load story structure: {e}")
        return None

def save_to_json(data, filename):
    """保存数据到JSON文件"""
    filepath = os.path.join(OUTPUT_DIR, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"数据已保存到 {filepath}")
    return filepath

def main():
    res = extract_english_dialogue("https://reverse1999.fandom.com/wiki/NS-1")
    save_to_json(res, "ns-1.json")


def test(): 
    print("开始抓取重返未来1999游戏剧情的英文文本...")

    # 加载故事结构
    story_structure = load_story_structure()

    # 需要爬取的章节和小节
    crwaler_chapter_title = "Notes on Shuori"
    # crawler_episode_title = "客套话"
    
    # 遍历故事结构中的每个章节
    for chapter in story_structure["side_story"]:
        chapter_cn_title = chapter["english_title"]
        if chapter_cn_title != crwaler_chapter_title:
            continue
        # 创建章节目录
        chapter_dir = os.path.join(OUTPUT_DIR, chapter_cn_title)
        os.makedirs(chapter_dir, exist_ok=True)
        chapter_en_title = chapter["english_title"]
        print(f"\n开始处理章节: {chapter_cn_title} ({chapter_en_title})")
        
        # 遍历章节中的每个小节
        for episode in chapter["episodes"]:
            episode_cn_title = episode["english_title"]
            # if episode_cn_title != crawler_episode_title:
            #     continue
            episode_en_title = episode["english_title"]
            episode_link = episode["link"]
            
            # 检查是否已经爬取过
            if is_episode_crawled(chapter_dir, episode_cn_title):
                print(f"  跳过已爬取的小节: {episode_cn_title} ({episode_en_title})")
                continue
            
            # 构建完整URL
            full_url = f"{BASE_URL}{episode_link}"
            print(f"  处理小节: {episode_cn_title} ({episode_en_title})")
            
            try:
                # 提取对话
                dialogues = extract_english_dialogue(full_url)
                if not dialogues:
                    print(f"  警告: 未能从 {episode_cn_title} 提取到对话，将在下次运行时重试")
                    continue
                    
                print(f"  成功提取 {len(dialogues)} 条对话")
                
                # 保存小节对话
                episode_filename = f"{episode_cn_title}.json"
                episode_filepath = os.path.join(OUTPUT_DIR, chapter_cn_title, episode_filename)
                with open(episode_filepath, 'w', encoding='utf-8') as f:
                    json.dump(dialogues, f, ensure_ascii=False, indent=2)
                
                # 添加随机延迟，避免请求过于频繁
                delay = random.uniform(5, 10)  # 增加延迟时间
                print(f"  等待 {delay:.2f} 秒后继续...")
                time.sleep(delay)
                
            except Exception as e:
                print(f"  处理小节 {episode_cn_title} 时出错: {e}")
                print("  将在下次运行时重试该小节")
                continue
    
    
    print("\n抓取完成！所有对话已保存")




if __name__ == "__main__":
    test()