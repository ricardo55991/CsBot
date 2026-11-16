with open('tools/mlmove_pipeline/capture_all_16_screenshots.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('taskkill')
print(text[idx:idx+500])
