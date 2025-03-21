import os
from bs4 import BeautifulSoup
import json

# 读取HTML文件
def read_html_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

# 提取故事结构
def extract_story_structure(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    
    # 查找主线故事容器
    main_story_tab = soup.find_all(class_='tabber-item')[1]
    chapters = main_story_tab.find_all('h2')
    
    story_structure = {
        "side_story": []
    }

    for chapter in chapters:
        # 提取章节信息
        title_span = chapter.find('span', class_='mw-headline')
        if not title_span:
            continue
            
        # 分离中英文标题
        full_title = title_span.text.strip()
        title_column = title_span.find('span', style='display: flex;flex-direction: column;')
        if title_column:
            ch_title = title_column.find('span').get_text(strip=True)
            en_title = title_column.find('small').span.get_text(strip=True)

        # 构建章节对象
        chapter_data = {
            "chinese_title": ch_title,
            "english_title": en_title,
            "episodes": []
        }

        # 提取子章节
        episode_list = chapter.find_next('div', class_='episode-list')
        episodes = episode_list.find_all('div', class_='episode-list--single')
        
        for idx, episode in enumerate(episodes, start=1):
            main_div = episode.find('div')
            title_links = [a for a in main_div.find_all('a', href=True) if a.text.strip() and not a.find('span', class_='span-link')]
            if title_links:
                cn_a = title_links[0]  
                link = cn_a['href']
                cn_title = cn_a.text.strip()
                
                eng_div = episode.find('div', class_='episode-list--eng')
                eng_title = eng_div.text.strip() if eng_div else ""
                
                episode_data = {
                    "chinese_title": cn_title,
                    "english_title": eng_title,
                    "link": link
                }
                chapter_data["episodes"].append(episode_data)

        story_structure["side_story"].append(chapter_data)

    return story_structure
# 保存为JSON文件
def save_to_json(data, output_path):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"数据已保存到 {output_path}")

def main():
    # 输入和输出文件路径
    html_file_path = "d:\\errorhassei\\project\\reverse_crawler\\storys.html"
    output_dir = "d:\\errorhassei\\project\\reverse_crawler\\output"
    output_file = os.path.join(output_dir, "side_story_structure.json")
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取HTML文件
    html_content = read_html_file(html_file_path)
    
    # 提取故事结构
    story_structure = extract_story_structure(html_content)
    
    if story_structure:
        # 保存为JSON文件
        save_to_json(story_structure, output_file)
        print("故事结构提取完成！")
    else:
        print("提取故事结构失败")

if __name__ == "__main__":
    main()