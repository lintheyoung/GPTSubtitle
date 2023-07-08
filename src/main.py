# 导入需要的模块
import streamlit as st
import openai
import os
import re
import time
import string

openai.api_key = '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'

# 用于存储所有消息的列表
messages = []

def extract_role_and_messages(file_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    role = ' '.join(line.strip() for line in lines if line.strip())
    messages.append({"role": "system", "content": role})

    return role

def chat_with_gpt(message):
    messages.append({"role": "user", "content": "请结合上下文将如下文中的这句话翻译为中文，并只返回翻译结果"+message})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-16k",
        messages=messages
    )

    assistant_message = response['choices'][0]['message']['content']
    messages.append({"role": "assistant", "content": assistant_message})

    return assistant_message

def extract_text(file_name):
    with open(file_name, 'r', encoding='utf-8') as file:
        data = file.read()

    data = re.sub(r'\d+\n\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+\n', '', data)
    data = re.sub(r'\n+', ' ', data)
    sentences = [sentence.strip() for sentence in data.split('.') if sentence]

    return sentences

def translate_and_print(sentences):
    translations = {}

    for sentence in sentences:
        while True:
            try:
                st.write(f'正在翻译: {sentence}')
                translation = chat_with_gpt(sentence)
                translations[sentence] = translation
                with open('translations.txt', 'a', encoding='utf-8') as file:
                    file.write(f'Original: {sentence}\nTranslation: {translation}\n\n')
                break
            except openai.error.ServiceUnavailableError:
                st.write("The server is overloaded or not ready yet. Waiting for 20 seconds before retrying.")
                time.sleep(20)

    return translations

def parse_translation_file(file_path):
    with open(file_path, 'r') as file:
        content = file.readlines()

    translation_dict = {}
    for line in content:
        if "Original: " in line:
            original = line[len("Original: "):].strip()
        if "Translation: " in line:
            translation = line[len("Translation: "):].strip()
            original = original.lower()
            original = original.translate(str.maketrans('', '', string.punctuation))
            original = original.replace('\n', ' ').replace('\t', ' ').strip()
            translation_dict[original] = translation

    return translation_dict

def parse_srt(file_path, translation_dict):
    with open(file_path, 'r') as file:
        content = file.read()

    pattern = re.compile(r'(\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d\n)([\s\S]*?)(?=\n\n)')
    matches = pattern.findall(content)

    with open('translated_subtitle.srt', 'w') as file:
        for i, match in enumerate(matches, 1):
            lines = match[1].split('\n')
            long_sentences = []
            for j in range(len(lines)):
                if j == 0 or lines[j-1][-1] != lines[j][0]:
                    long_sentences.append(lines[j])
                else:
                    long_sentences[-1] += lines[j]
            
            file.write(str(i) + '\n' + match[0])
            for long_sentence in long_sentences:
                sentences = long_sentence.split('.')
                sentences = [sentence.strip() for sentence in sentences if sentence.strip()]
                for sentence in sentences:
                    sentence_to_compare = sentence.lower()
                    sentence_to_compare = sentence_to_compare.translate(str.maketrans('', '', string.punctuation))
                    sentence_to_compare = sentence_to_compare.replace('\n', ' ').replace('\t', ' ').strip()

                    for key in translation_dict.keys():
                        if sentence_to_compare in key:
                            original_start = max(0, key.index(sentence_to_compare) - 1)
                            original_end = min(len(key), original_start + len(sentence_to_compare) + 2)
                            original_length = len(key)

                            translation_length = len(translation_dict[key])
                            translation_start = int(original_start / original_length * translation_length)
                            translation_end = int(original_end / original_length * translation_length)

                            partial_translation = translation_dict[key][translation_start:translation_end]

                            file.write(sentence + '\n')
                            file.write(partial_translation + '\n')
                            break
            file.write('\n')

# 主程序开始，创建Streamlit应用界面
def main():
    st.title("SRT文件翻译")
    
    uploaded_file = st.file_uploader("上传你的SRT文件", type=["srt"])
    
    if uploaded_file is not None:
        file_details = {"FileName":uploaded_file.name,"FileType":uploaded_file.type,"FileSize":uploaded_file.size}
        st.write(file_details)
        
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("文件上传成功!")
        
        if st.button('开始翻译'):
            # 检查是否存在translations.txt文件，如果不存在则创建一个空白的文件，如果存在则清空文件内容
            if not os.path.exists('translations.txt'):
                open('translations.txt', 'w', encoding='utf-8').close()
            else:
                open('translations.txt', 'w', encoding='utf-8').close()
            st.write("开始翻译...这可能需要一些时间，请耐心等待.")
            sentences = extract_text(uploaded_file.name)
            translations = translate_and_print(sentences)
            translation_dict = parse_translation_file('translations.txt')
            parse_srt(uploaded_file.name, translation_dict)
            st.success('翻译完成并且已生成新的srt文件!')
        
        if os.path.exists('translated_subtitle.srt'):
            with open('translated_subtitle.srt', 'rb') as f:
                btn = st.download_button(
                    label='下载翻译后的srt文件',
                    data=f,
                    file_name='translated_subtitle.srt',
                    mime='application/octet-stream'
                )

if __name__ == "__main__":
    main()