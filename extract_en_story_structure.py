import os
import json
from bs4 import BeautifulSoup

# 读取HTML文件
html_path = "D:\\errorhassei\\project\\reverse1999\\html\\fandom_storys.html"
with open(html_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

# 使用BeautifulSoup解析HTML
soup = BeautifulSoup(html_content, 'html.parser')

# 查找所有的表格行
rows = soup.select('.wikitable tbody tr')

side_stories = []
current_story = None

# 遍历表格行
for row in rows:
    # 检查是否是标题行（colspan="10"的行）
    title_cell = row.select_one('td[colspan="10"]')
    if title_cell:
        # 如果已经有一个故事，将其添加到列表中
        if current_story:
            side_stories.append(current_story)
        
        # 创建新的故事对象
        story_link = title_cell.select_one('a')
        if story_link:
            current_story = {
                "english_title": story_link.text.strip(),
                "episodes": []
            }
    
    # 检查是否是包含章节的行
    episode_cells = row.select('td a')
    if current_story and episode_cells and not row.select_one('td[colspan="10"]'):
        # 跳过第一个单元格（如果它包含图片）
        start_index = 0
        if row.select_one('td[rowspan]'):
            start_index = 1
        
        # 添加章节信息
        for cell in episode_cells[start_index:]:
            if cell.get('href') and cell.get('title'):
                current_story["episodes"].append({
                    "english_title": cell.text.strip(),
                    "link": cell.get('href')
                })

# 添加最后一个故事
if current_story:
    side_stories.append(current_story)

# 创建最终的JSON结构
result = {
    "side_story": side_stories
}

# 将结果保存为JSON文件
output_path = "D:\\errorhassei\\project\\reverse1999\\output\\fandom_story_structure_en.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as file:
    json.dump(result, file, ensure_ascii=False, indent=2)

print(f"解析完成，结果已保存到 {output_path}")