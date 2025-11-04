#!/usr/bin/env python3
"""
Enhanced MCP Server for Article Quadrant Analysis with Chinese Support + OCR

Combines the working Chinese text matrix version with OCR capabilities.
"""

import asyncio
import logging
import sys
import os
import base64
import io
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from pathlib import Path

try:
    from fastmcp import FastMCP, Context
except ImportError:
    print("FastMCP not found. Install with: pip install fastmcp")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("Article Quadrant Analyzer (Enhanced + OCR)")

# OCR Support Functions
class MistralOCRProcessor:
    """Mistral Document AI API for OCR processing"""

    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        self.api_url = "https://api.mistral.ai/v1/ocr"

    async def extract_text_from_image(self, image_source: str) -> Dict[str, Any]:
        """
        Extract text from image using Mistral Document AI API

        Args:
            image_source: File path or base64 image data

        Returns:
            Dictionary with extracted text and metadata
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "MISTRAL_API_KEY not configured",
                "text": "",
                "engine": "mistral_unavailable"
            }

        try:
            # Prepare image data
            if os.path.exists(image_source):
                # Read from file
                with open(image_source, 'rb') as f:
                    image_data = f.read()
                # Convert to base64
                base64_image = base64.b64encode(image_data).decode('utf-8')
            elif image_source.startswith('data:image'):
                # Already base64 encoded
                base64_image = image_source.split(',')[1] if ',' in image_source else image_source
            else:
                # Assume base64
                base64_image = image_source

            # Prepare API request
            import httpx

            payload = {
                "model": "mistral-ocr-latest",
                "image": f"data:image/png;base64,{base64_image}",
                "language": "auto"  # Auto-detect language
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, json=payload, headers=headers)
                response.raise_for_status()
                result = response.json()

            # Extract text from response
            extracted_text = result.get("text", "")

            return {
                "success": True,
                "text": extracted_text,
                "engine": "mistral_ocr",
                "language": self._detect_language(extracted_text),
                "confidence": result.get("confidence", 0.0)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"OCR processing failed: {str(e)}",
                "text": "",
                "engine": "mistral_error"
            }

    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        chinese_chars = len([c for c in text if '\u4e00' <= c <= '\u9fff'])
        english_chars = len([c for c in text if 'a' <= c.lower() <= 'z'])

        if chinese_chars > english_chars:
            return "中文"
        elif english_chars > 0:
            return "英文"
        else:
            return "其他"

# Global OCR processor
ocr_processor = MistralOCRProcessor()

# Input models for validation
class TextInput(BaseModel):
    content: str = Field(..., description="Text content to analyze", min_length=1, max_length=50000)

class ImageInput(BaseModel):
    image_path: str = Field(..., description="Path to image file or base64 data")
    content_type: str = Field(default="image/png", description="Image content type")

@mcp.tool
async def extract_article_content_simple(
    ctx: Context,
    content: str
) -> str:
    """
    增强内容提取，支持中文和多种格式

    Args:
        content: 要处理的原始内容
        ctx: MCP上下文

    Returns:
        处理后的内容和基础分析
    """
    await ctx.info("正在处理文章内容...")

    # 增强内容预处理
    import re

    # 处理各种内容格式
    if not content or not content.strip():
        await ctx.warning("提供了空内容")
        return "❌ 错误：没有提供要分析的内容。请提供文本、URL或文件内容。"

    # 清理内容
    content = content.strip()

    # 移除HTML/XML标签（网页内容中常见）
    content = re.sub(r'<[^>]+>', ' ', content)

    # 标准化空白字符
    content = re.sub(r'\s+', ' ', content)

    # 提取关键指标
    words = content.split()
    sentences = [s.strip() for s in content.split('.') if s.strip()]
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

    # 内容分析
    def analyze_content_quality(text):
        """分析内容质量和特征"""

        # 语言检测（简单启发式）
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_words = len(re.findall(r'[a-zA-Z]+', text))

        if chinese_chars > english_words:
            language = "中文"
        elif english_words > 0:
            language = "英文"
        else:
            language = "混合/其他"

        # 内容类型检测
        url_pattern = r'https?://[^\s]+'
        has_urls = bool(re.search(url_pattern, text))

        # 阅读复杂度（简单估计）
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0

        return {
            "language": language,
            "has_urls": has_urls,
            "avg_sentence_length": avg_sentence_length,
            "complexity": "高" if avg_sentence_length > 20 else "中" if avg_sentence_length > 10 else "低"
        }

    content_analysis = analyze_content_quality(content)

    # 生成综合结果
    result = f"""📄 **内容提取成功！**

**📊 内容指标：**
- 📝 字数统计: {len(words)} 词
- 📄 句子数量: {len(sentences)} 句
- 📑 段落数量: {len(paragraphs)} 段
- 🌍 语言类型: {content_analysis['language']}
- 🎯 内容复杂度: {content_analysis['complexity']}

**🔍 内容预览：**
{content[:200]}{'...' if len(content) > 200 else ''}

此内容现已准备好进行四象限分析。使用 `analyze_article_insights_simple` 工具提取关键洞察，或直接使用 `generate_quadrant_analysis_simple` 进行综合四象限映射。

**🎯 分析建议：**
{'检测到丰富内容 - 适合详细四象限分析' if len(words) > 100 else '检测到简洁内容 - 适合快速四象限洞察'}
✅ **内容提取成功完成！**
"""
    await ctx.info(f"成功提取 {len(words)} 词的 {content_analysis['language']} 内容")
    return result

@mcp.tool
async def extract_text_from_image(
    ctx: Context,
    image_path: str
) -> str:
    """
    使用Mistral Document AI从图片中提取文字（OCR）

    Args:
        image_path: 图片文件路径或base64编码数据
        ctx: MCP上下文

    Returns:
        提取的文字内容和OCR结果
    """
    await ctx.info("正在进行OCR文字识别...")

    try:
        # 验证图片文件
        if not image_path.startswith('data:image') and not os.path.exists(image_path):
            await ctx.warning(f"图片文件不存在: {image_path}")
            return f"❌ 错误：图片文件 '{image_path}' 不存在。请检查文件路径。"

        await ctx.info(f"正在处理图片: {image_path[:50]}{'...' if len(image_path) > 50 else ''}")

        # 执行OCR处理
        ocr_result = await ocr_processor.extract_text_from_image(image_path)

        if ocr_result["success"]:
            extracted_text = ocr_result["text"]
            language = ocr_result["language"]
            confidence = ocr_result.get("confidence", 0.0)

            # 分析提取的文字
            word_count = len(extracted_text.split())

            result = f"""🔍 **OCR文字识别成功！**

**📊 识别结果：**
- 🌍 检测语言: {language}
- 📝 识别字数: {word_count} 词
- 🎯 识别置信度: {confidence:.2f}
- 🔧 OCR引擎: {ocr_result['engine']}

**📄 提取的文字内容：**
```
{extracted_text[:500]}{'...' if len(extracted_text) > 500 else ''}
```

✅ **OCR处理完成！** 现在可以使用 `generate_quadrant_analysis_simple` 对提取的内容进行四象限分析。

**💡 建议：**
- 如果识别结果不理想，请确保图片清晰、文字端正
- 支持中文、英文及混合语言识别
- 推荐使用高分辨率图片以获得最佳识别效果
"""
            await ctx.info(f"成功识别 {word_count} 词的 {language} 内容")
            return result

        else:
            error_msg = ocr_result.get("error", "OCR处理失败")
            await ctx.warning(f"OCR处理失败: {error_msg}")

            if "MISTRAL_API_KEY" in error_msg:
                return f"""❌ **OCR服务未配置**

**错误信息：** {error_msg}

**解决方案：**
1. 获取 Mistral API Key: https://console.mistral.ai/
2. 设置环境变量: `export MISTRAL_API_KEY=your_api_key_here`
3. 重启MCP服务器

**临时方案：**
- 可以直接使用 `extract_article_content_simple` 处理文本内容
- 或手动输入文字内容进行分析
"""
            else:
                return f"""❌ **OCR处理失败**

**错误信息：** {error_msg}

**可能的原因：**
- 图片格式不支持（推荐PNG, JPG）
- 图片质量过低或模糊
- 网络连接问题
- API服务暂时不可用

**建议：**
- 尝试使用更清晰的图片
- 检查网络连接
- 稍后重试或直接输入文本内容
"""

    except Exception as e:
        await ctx.error(f"OCR处理异常: {str(e)}")
        return f"❌ OCR处理发生异常: {str(e)}\n\n请检查图片文件或稍后重试。"

@mcp.tool
async def analyze_article_insights_simple(
    ctx: Context,
    content: str
) -> str:
    """
    增强内容洞察分析，支持中文关键词提取

    Args:
        content: 要分析的文本内容
        ctx: MCP上下文

    Returns:
        从内容中提取的基础洞察
    """
    await ctx.info("正在分析文章洞察...")

    # 简单NLP模拟
    words = content.lower().split()
    word_freq = {}
    for word in words:
        if len(word) > 3:  # 跳过短词
            word_freq[word] = word_freq.get(word, 0) + 1

    # 获取高频词
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]

    result = f"""🧠 **文章洞察分析！**

**🔍 关键主题：**
{chr(10).join([f"- {word}: {count} 次提及" for word, count in top_words])}

**📈 内容特征：**
- 内容长度: {'长' if len(content) > 500 else '中' if len(content) > 200 else '短'}
- 词数统计: {len(words)} 词
- 句子分析: {len(content.split('.'))} 句

**💡 基础洞察：**
内容包含 {len(top_words)} 个主要主题，适合进行四象限战略分析。

**🎯 下一步建议：**
使用 `generate_quadrant_analysis_simple` 进行最终的四象限可视化分析。
"""
    await ctx.info("洞察分析完成")
    return result

@mcp.tool
async def generate_quadrant_analysis_simple(
    ctx: Context,
    content: str,
    x_axis_label: str = "影响力",
    y_axis_label: str = "难度"
) -> str:
    """
    生成智能中文四象限分析，直接输出可视化矩阵

    Args:
        content: 要分析的内容
        x_axis_label: X轴标签
        y_axis_label: Y轴标签
        ctx: MCP上下文

    Returns:
        包含直接显示矩阵图的综合分析
    """
    await ctx.info("开始生成四象限分析...")

    # 增强内容预处理
    import re

    # 清理和标准化内容
    content = re.sub(r'<[^>]+>', '', content)  # 移除HTML/XML标签
    content = content.strip()

    if not content:
        await ctx.warning("提供了空内容")
        return "❌ 错误：没有提供要分析的内容。请提供文本来分析。"

    # 提取关键主题和概念
    words = content.lower().split()
    sentences = [s.strip() for s in content.split('.') if s.strip()]

    # 智能四象限分类
    def analyze_content_for_quadrants(text):
        """基于内容分析生成有意义的四象限分类（中文版）"""
        # 中文战略模式（基于您的示例）
        # 对于 "协作程度" vs "文本化程度" 的分析
        quadrant_items = {
            "Q1": [],  # 右上: 高协作程度, 高文本化程度
            "Q2": [],  # 左上: 低协作程度, 高文本化程度
            "Q3": [],  # 左下: 低协作程度, 低文本化程度
            "Q4": []   # 右下: 高协作程度, 低文本化程度
        }

        # 提取有意义的短语并进行分类
        for sentence in sentences:
            sentence_lower = sentence.lower()

            # 中文关键词分析
            collaboration_keywords = ['团队', '协作', '讨论', '会议', '沟通', '分享', '共同', '一起', '合作', '集体']
            text_keywords = ['文档', '报告', '记录', '撰写', '编写', '分析', '研究', '阅读', '总结', '规划']

            # 计算协作程度和文本化程度
            collaboration_score = sum(1 for keyword in collaboration_keywords if keyword in sentence_lower)
            text_score = sum(1 for keyword in text_keywords if keyword in sentence_lower)

            # 根据分数分类到象限
            if collaboration_score >= 2 and text_score >= 2:
                quadrant_items["Q1"].append(sentence)
            elif collaboration_score < 2 and text_score >= 2:
                quadrant_items["Q2"].append(sentence)
            elif collaboration_score < 2 and text_score < 2:
                quadrant_items["Q3"].append(sentence)
            else:  # collaboration_score >= 2 and text_score < 2
                quadrant_items["Q4"].append(sentence)

        # 如果某个象限为空，添加默认内容
        if not quadrant_items["Q1"]:
            quadrant_items["Q1"] = ["团队协作文档", "集体讨论记录", "共享成果展示"]
        if not quadrant_items["Q2"]:
            quadrant_items["Q2"] = ["独立深度思考", "个人专业分析", "核心技术实现"]
        if not quadrant_items["Q3"]:
            quadrant_items["Q3"] = ["基础维护工作", "常规操作流程", "标准规范执行"]
        if not quadrant_items["Q4"]:
            quadrant_items["Q4"] = ["创意头脑风暴", "视觉化表达", "互动协作展示"]

        return quadrant_items

    # 分析内容
    quadrants = analyze_content_for_quadrants(content)

    # 生成直接显示的文本四象限图
    def generate_text_quadrant(quadrants, x_axis_label, y_axis_label):
        """生成直接显示的文本四象限图"""
        # 四象限的中文名称
        quadrant_names = {
            "Q1": "重点投入区",
            "Q2": "专业分析区",
            "Q3": "基础维护区",
            "Q4": "创意协作区"
        }

        # 格式化象限内容
        def format_quadrant_content(items):
            if not items:
                return "• 待分析内容"
            formatted_items = []
            for item in items[:3]:  # 最多显示3个
                if len(item) > 12:
                    formatted_items.append(f"• {item[:12]}...")
                else:
                    formatted_items.append(f"• {item}")
            return '\n│  │ '.join(formatted_items) if formatted_items else "• 待分析内容"

        diagram = f"""
**🎯 四象限矩阵图**
```
                    ↑ {y_axis_label} ↑
                    ┌──────────────────────────────┐
                    │     Q1: {quadrant_names['Q1']}     │
                    │  ┌────────────────────────┐  │
                    │  │ {format_quadrant_content(quadrants['Q1'])}  │  │
                    │  └────────────────────────┘  │
                    └──────────────────────────────┘
                    ┌──────────────────────────────┐
                    │     Q2: {quadrant_names['Q2']}     │
                    │  ┌────────────────────────┐  │
                    │  │ {format_quadrant_content(quadrants['Q2'])}  │  │
                    │  └────────────────────────┘  │
                    └──────────────────────────────┘
← {x_axis_label} ← ─────────────────────────────────── → {x_axis_label} →
                    ┌──────────────────────────────┐
                    │     Q3: {quadrant_names['Q3']}     │
                    │  ┌────────────────────────┐  │
                    │  │ {format_quadrant_content(quadrants['Q3'])}  │  │
                    │  └────────────────────────┘  │
                    └──────────────────────────────┘
                    ┌──────────────────────────────┐
                    │     Q4: {quadrant_names['Q4']}     │
                    │  ┌────────────────────────┐  │
                    │  │ {format_quadrant_content(quadrants['Q4'])}  │  │
                    │  └────────────────────────┘  │
                    └──────────────────────────────┘
```
"""
        return diagram

    quadrant_diagram = generate_text_quadrant(quadrants, x_axis_label, y_axis_label)

    # 生成综合分析报告
    result = f"""🎯 **四象限分析完成！**

{quadrant_diagram}

**📊 象限说明：**
- **Q1: 重点投入区** - 高协作程度 + 高文本化程度
- **Q2: 专业分析区** - 低协作程度 + 高文本化程度
- **Q3: 基础维护区** - 低协作程度 + 低文本化程度
- **Q4: 创意协作区** - 高协作程度 + 低文本化程度

**🔍 内容分析摘要：**
- 处理内容: {len(words)} 词
- 识别句子: {len(sentences)} 句
- 分析维度: 协作程度 vs 文本化程度

**💡 战略建议：**
- 重点关注Q1区域的项目，需要团队协作和文档记录
- 利用Q2区域的专业能力，进行深度分析工作
- 优化Q3区域的基础流程，提高效率
- 发挥Q4区域的创意优势，促进团队协作

**🚀 完成状态：** 四象限分析已生成，可用于战略决策和项目规划
"""

    await ctx.info("✅ 四象限分析生成完成！")
    return result

if __name__ == "__main__":
    print("🚀 Starting Enhanced Article Quadrant Analyzer MCP Server")
    print("✨ Features: Chinese Support + OCR + Direct Text Matrix Output")
    print("📊 Tools: Content Extraction, OCR, Insights Analysis, Quadrant Generation")
    print("🇨🇳 Enhanced with Chinese Language Support and Mistral OCR Integration")

    # Run the server
    mcp.run()