# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import sys
import os

project = '逸夫科普讲解队'
copyright = '2024, 13th-SunJianhao'
author = '13th-SunJianhao'
release = 'v1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration
# 此处为项目文件地址
project_path = r"C:\Users\Jin\Desktop\yifu_document"
sys.path.insert(0, os.path.abspath("../.."))

# 此处为导入的 md 文件需要的配置
extensions = ['sphinx_markdown_tables', 'm2r']
source_suffix = [".rst", ".md"]

# html_theme = 'sphinx_rtd_theme'

html_theme = "furo"
templates_path = ['_templates']
exclude_patterns = []
html_theme_options = {
    "top_of_page_button": "edit",
    "sidebar_hide_name": True,
    "navigation_with_keys": True,
    "announcement": "<em>欢迎加入逸夫科普讲解队</em>",
    "light_css_variables": {
        "color-brand-primary": "green",
        # "color-brand-content": "green",
        "color-admonition-background": "orange",
        "font-stack": "Times New Roman, Times, serif",
    },
}

language = 'zh_CN'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_static_path = ['_static']

html_logo = 'https://github.com/Jin-sjh/Shaw_Science_Explainer_Team_Website/assets/97781484/999884c1-c6bd-4cc5-b898-a2e4861c3cbf'