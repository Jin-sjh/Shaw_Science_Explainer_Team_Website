"""
PO文件批量自动化翻译工具（原位保存模式）
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

        # Markdown保留格式正则表达式（已修复）
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

    def _process_single_file(self, file_path, suffix="_translated"):
        """处理单个PO文件（原位保存）"""
        # 生成输出路径
        dir_name = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        output_path = os.path.join(dir_name, f"{os.path.splitext(base_name)[0]}{suffix}.po")

        po = polib.pofile(file_path)

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

        po.save(output_path)
        print(f"已生成: {output_path}")

    def process_files(self, input_path, suffix="_translated"):
        """
        处理指定路径下的所有PO文件
        :param input_path: 文件或目录路径
        :param suffix: 输出文件后缀
        """
        if os.path.isfile(input_path) and input_path.endswith(".po"):
            self._process_single_file(input_path, suffix)
            return

        for root, _, files in os.walk(input_path):
            for file in files:
                if file.endswith(".po"):
                    file_path = os.path.join(root, file)
                    self._process_single_file(file_path, suffix)


# ================== 使用示例 ==================
if __name__ == "__main__":
    # 命令行参数解析
    parser = argparse.ArgumentParser(description="PO文件批量翻译工具（原位保存版）")
    parser.add_argument("-i", "--input", required=True, help="输入文件/目录路径")
    parser.add_argument("--api", choices=["google", "deepl"], default="google", help="翻译API提供商")
    parser.add_argument("--key", required=True, help="API密钥（或Google的JSON密钥路径）")
    parser.add_argument("--target", default="zh-CN", help="目标语言代码")
    parser.add_argument("--suffix", default="_translated", help="输出文件后缀")
    args = parser.parse_args()

    # 初始化翻译器
    translator = POTranslator(
        api_provider=args.api,
        api_key=args.key,
        target_lang=args.target
    )

    # 执行处理
    translator.process_files(
        input_path=args.input,
        suffix=args.suffix
    )

    """
    # 处理单个文件
    python po_translator.py -i input.po --api google --key YOUR_KEY
    
    # 处理整个目录
    python po_translator.py -i ./locales/ --api deepl --key YOUR_KEY
    """