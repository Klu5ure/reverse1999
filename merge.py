import json

def load_story_dialogues(path):
    """加载故事结构数据"""
    structure_path = path
    try:
        with open(structure_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"加载故事结构数据失败: {e}")
        return None

def align_dialogues(chinese_dialogues, english_dialogues, filename):
    """基于数量校验的精确顺序匹配"""
    print(f"🔍 开始对齐校验 | 中文: {len(chinese_dialogues)}条 | 英文: {len(english_dialogues)}条")
    
    if len(chinese_dialogues) != len(english_dialogues):
        # 新增详细差异定位
        for i, (cn, en) in enumerate(zip(chinese_dialogues, english_dialogues)):
            if cn["dialogue"] != en["english_dialogue"]:
                print(f"⚠️ 第{i+1}条对话不匹配：")
                print(f"   中文：{cn['dialogue']}")
                print(f"   英文：{en['english_dialogue']}")
                import sys
                sys.exit(1)  # 新增系统退出
                break
        return
    
    aligned_data = []
    
    # 使用zip进行精确顺序匹配
    for cn, en in zip(chinese_dialogues, english_dialogues):
        aligned_data.append({
            "chinese_speaker": cn["speaker"],
            "chinese_text": cn["dialogue"],
            "english_speaker": en["english_speaker"],
            "english_text": en["english_dialogue"]
        })

    json.dump(aligned_data, open("output/en_side_dialogues/Notes on Shuori/" + filename + ".json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"✅ 已将对齐后的对话保存到 " + "outoutput/en_side_dialogues/Notes on Shuori/" + filename + ".json")
    

def test():
    # english_json = r"D:\\errorhassei\\project\\reverse1999\\output\\Notes on Shuori\\NS-01.json"
    # chinese_json = r"D:\\errorhassei\\project\\reverse1999\\output\\side_dialogues\\NS朔日手记\\启程的祷声.json"
    # # 加载故事结构
    # english_dialogue = load_story_dialogues(english_json)
    # chinese_dialogue = load_story_dialogues(chinese_json)
    # align_dialogues(chinese_dialogue, english_dialogue)

    side_story_structure = load_story_dialogues(r"D:\\errorhassei\\project\\reverse1999\\output\\side_story_structure.json")
    for chapter in side_story_structure["side_story"]:
        if chapter["chinese_title"] != "NS朔日手记":
            continue
        chapter_cn_title = chapter["chinese_title"]
        chapter_en_title = chapter["english_title"]
        for episode in chapter["episodes"]:
            episode_cn_title = episode["chinese_title"]
            episode_en_title = episode["english_title"]
            link = episode["link"]
            english_file_name = link.split('/')[-1]
            english_json = r"D:\\errorhassei\\project\\reverse1999\\output\\Notes on Shuori\\" + english_file_name + ".json"
            chinese_json = r"D:\\errorhassei\\project\\reverse1999\\output\\side_dialogues\\NS朔日手记\\" + episode_cn_title + ".json"
            # 加载故事结构
            english_dialogue = load_story_dialogues(english_json)
            chinese_dialogue = load_story_dialogues(chinese_json)
            align_dialogues(chinese_dialogue, english_dialogue, english_file_name + " " + episode_cn_title)
        # 加载故事结构          




if __name__ == "__main__":
    test()
