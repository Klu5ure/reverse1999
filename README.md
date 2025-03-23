extract_story_structure.py 获取中文故事结构，存储到output/story_structure.json, side.json 目前是main side分开获取，后续可能需要优化
get_cn_story.py 根据结构获取链接，根据链接爬虫获取故事文本，整合成json，存储到output/dialogues.json, side_dialogues

extract_story_structure.py 获取英文故事结构，存储到output/fandom_story.json, side.json 目前是main side分开获取，后续可能需要优化
get_en_story_from_wiki.py 根据结构获取链接以及文本，存储到output/en_side_dialogues.json


有一些链接需要加Story，可以直接改json

对比两边的并组合文本


各个文件夹有点乱，重新整理一下


后续或许可以做一个文件，可以单元测试调用这些所有的东西