"""
PO文件批量自动化翻译工具（支持目录遍历）
安装依赖：pip install polib google-cloud-translate deepl tenacity
"""

import os
import re
import argparse
import polib
from tenacity import retry, stop_after_attempt, wait_exponential
from google.cloud import translate_v2 as translate
import deepl


class POTranslator:
    def __init__(self, api_provider="google", api_key=None, target_lang="zh"):
        """
        :param api_provider: 可选 "google" 或 "deepl"
        :param api_key: 对应API的密钥
        :param target_lang: 目标语言代码（Google: zh/zh-CN, DeepL: ZH）
        """
        self.api_provider = api_provider
        self.target_lang = target_lang if api_provider == "google" else "ZH"

        # 初始化翻译客户端
        if api_provider == "google":
            self.client = translate.Client(credentials=api_key) if isinstance(api_key, dict) \
                else translate.Client(api_key)
        elif api_provider == "deepl":
            self.client = deepl.Translator(api_key)
        else:
            raise ValueError("不支持的API提供商")

        # Markdown保留格式正则表达式（可扩展）
        self.markdown_patterns = [
            r"$$.*?$$$https?://\S+$",  # 链接
            r"\*\*.*?\*\*",  # 加粗
            r"\*.*?\*",  # 斜体
            r"`.*?`",  # 行内代码
            r"@\w+",  # @提及
            r"#\w+"  # 话题标签
        ]
        self.preserve_regex = re.compile("|".join(self.markdown_patterns), flags=re.DOTALL)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _translate_text(self, text):
        """带重试机制的翻译核心方法"""
        try:
            if self.api_provider == "google":
                result = self.client.translate(text, target_language=self.target_lang)
                return result['translatedText']
            elif self.api_provider == "deepl":
                result = self.client.translate_text(text, target_lang=self.target_lang)
                return result.text
        except Exception as e:
            print(f"翻译失败: {str(e)}")
            raise

    def _protect_special_format(self, text):
        """使用占位符保护特殊格式"""
        placeholders = {}

        def replace_match(match):
            key = f"__MD_{len(placeholders)}__"
            placeholders[key] = match.group(0)
            return key

        protected = self.preserve_regex.sub(replace_match, text)
        return protected, placeholders

    def _process_single_file(self, input_path, output_path):
        """处理单个PO文件"""
        po = polib.pofile(input_path)

        for entry in po.untranslated_entries():
            original = entry.msgid
            if not original:
                continue

            # 保护特殊格式 -> 翻译 -> 恢复格式
            protected_text, placeholders = self._protect_special_format(original)
            translated = self._translate_text(protected_text)
            for ph, value in placeholders.items():
                translated = translated.replace(ph, value)

            # 处理常见转义问题
            translated = translated.replace('％', '%').replace('＃', '#')
            entry.msgstr = translated

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        po.save(output_path)
        print(f"已处理: {input_path} -> {output_path}")

    def process_directory(self, input_path, output_path, suffix="_translated"):
        """
        处理目录中的所有PO文件
        :param suffix: 输出文件名后缀（如 input.po -> input_translated.po）
        """
        if os.path.isfile(input_path):
            if input_path.endswith(".po"):
                output = f"{os.path.splitext(input_path)[0]}{suffix}.po"
                self._process_single_file(input_path, output)
            return

        for root, _, files in os.walk(input_path):
            for file in files:
                if file.endswith(".po"):
                    input_fullpath = os.path.join(root, file)
                    relative_path = os.path.relpath(input_fullpath, input_path)
                    output_fullpath = os.path.join(output_path, relative_path)
                    output_fullpath = output_fullpath.replace(".po", f"{suffix}.po")
                    self._process_single_file(input_fullpath, output_fullpath)


# ================== 使用示例 ==================
if __name__ == "__main__":
    # 命令行参数解析
    parser = argparse.ArgumentParser(description="PO文件批量翻译工具")
    parser.add_argument("-i", "--input", required=True, help="输入文件/目录路径")
    parser.add_argument("-o", "--output", required=True, help="输出目录路径")
    parser.add_argument("--api", choices=["google", "deepl"], default="google", help="翻译API提供商")
    parser.add_argument("--key", required=True, help="API密钥（或Google的JSON密钥路径）")
    parser.add_argument("--target", default="zh-CN", help="目标语言代码")
    args = parser.parse_args()

    # 初始化翻译器
    translator = POTranslator(
        api_provider=args.api,
        api_key=args.key,
        target_lang=args.target
    )

    # 执行批量处理
    translator.process_directory(
        input_path=args.input,
        output_path=args.output,
        suffix="_translated"
    )

    # python  po_translator.py - i locales / -o translated / --api  deepl - -key $DEEPL_KEY