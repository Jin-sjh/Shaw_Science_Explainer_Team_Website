"""
PO文件批量翻译工具
功能：自动翻译.po文件中的中文内容到英文
依赖：googletrans==3.1.0a0
安装：pip install googletrans==3.1.0a0
"""

import re
import time
import os
import argparse
from googletrans import Translator


def extract_translations(po_file_path):
    """从.po文件中提取所有msgstr的中文内容"""
    translations = []
    with open(po_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 匹配msgstr块（支持多行和转义字符）
    pattern = re.compile(
        r'msgstr\s+"((?:[^"\\]|\\"|\\\\)*)"',
        re.MULTILINE
    )

    for match in pattern.findall(content):
        # 处理转义字符
        text = match.replace('\\"', '"').replace('\\\\', '\\')
        if text.strip():  # 过滤空翻译
            translations.append(text)

    return translations


def translate_texts(texts, src='zh-CN', dest='en', delay=0.5):
    """使用Google翻译API进行批量翻译"""
    translator = Translator()
    translated = []

    for i, text in enumerate(texts):
        try:
            # 添加延迟避免频率限制
            if i > 0 and delay > 0:
                time.sleep(delay)

            result = translator.translate(text, src=src, dest=dest)
            translated.append(result.text)
            print(f"已翻译 {i + 1}/{len(texts)}")
        except Exception as e:
            print(f"翻译失败: {text[:30]}... | 错误: {str(e)[:50]}")
            translated.append(text)  # 保留原文

    return translated


def update_po_file(po_file_path, translations):
    """将翻译结果更新到.po文件"""
    with open(po_file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 分割msgstr占位符
    parts = re.split(r'(msgstr\s+")', content)

    new_content = []
    trans_index = 0

    for i in range(len(parts)):
        if parts[i].startswith('msgstr'):
            new_content.append(parts[i])
            if trans_index < len(translations):
                # 转义双引号并添加内容
                translated = translations[trans_index].replace('"', '\\"')
                new_content.append(translated)
                trans_index += 1
        else:
            new_content.append(parts[i])

    with open(po_file_path, 'w', encoding='utf-8') as file:
        file.write(''.join(new_content))


def find_po_files(directory):
    """递归查找目录下的所有.po文件"""
    po_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".po"):
                po_files.append(os.path.join(root, file))
    return po_files


def process_po_file(po_path, delay=0.5):
    """处理单个.po文件"""
    try:
        print(f"\n{'=' * 40}")
        print(f"开始处理文件: {po_path}")

        # 提取翻译内容
        source_texts = extract_translations(po_path)
        print(f"找到 {len(source_texts)} 条待翻译内容")

        if not source_texts:
            print("没有需要翻译的内容，跳过此文件")
            return True

        # 执行翻译
        translated_texts = translate_texts(source_texts, delay=delay)

        # 创建备份
        backup_path = po_path + ".bak"
        os.rename(po_path, backup_path)

        try:
            # 更新文件
            update_po_file(po_path, translated_texts)
            os.remove(backup_path)  # 处理成功删除备份
            print(f"文件处理成功: {po_path}")
            return True
        except Exception as e:
            # 恢复备份
            os.rename(backup_path, po_path)
            print(f"文件更新失败，已恢复原文件: {str(e)[:50]}")
            return False

    except Exception as e:
        print(f"处理文件时发生错误: {str(e)[:50]}")
        return False


def main():
    # 配置命令行参数
    parser = argparse.ArgumentParser(description="PO文件批量翻译工具")
    parser.add_argument("path", help="PO文件或目录路径")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="翻译请求间隔时间（默认0.5秒）")
    args = parser.parse_args()

    # 获取文件列表
    target_path = os.path.abspath(args.path)
    po_files = []

    if os.path.isfile(target_path) and target_path.endswith(".po"):
        po_files = [target_path]
    elif os.path.isdir(target_path):
        po_files = find_po_files(target_path)
    else:
        print("错误：路径不存在或不是PO文件")
        return

    print(f"\n=== 找到 {len(po_files)} 个PO文件需要处理 ===")

    # 处理统计
    success_count = 0
    fail_count = 0

    # 逐个处理文件
    for po_file in po_files:
        if process_po_file(po_file, args.delay):
            success_count += 1
        else:
            fail_count += 1

    # 输出总结报告
    print("\n" + "=" * 40)
    print("处理完成总结:")
    print(f"成功处理文件: {success_count} 个")
    print(f"失败文件: {fail_count} 个")
    if fail_count > 0:
        print("提示：失败文件已保持原状，请检查错误日志")


if __name__ == "__main__":
    main()

    #### 处理单个文件：
    # googletrans_translator.py project / single_file.po

    #### 处理整个目录（包含子目录）：
    # googletrans_translator.py project / locales --delay 1

    #### 带延时的处理（防止API限制）：
    # googletrans_translator.py project / locales --delay 1.5
