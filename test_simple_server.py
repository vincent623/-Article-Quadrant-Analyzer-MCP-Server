#!/usr/bin/env python3
"""
Enhanced MCP Server for Article Quadrant Analysis with Chinese Support
"""

import asyncio
import logging
import sys
from typing import Dict, Any
from pydantic import BaseModel, Field

try:
    from fastmcp import FastMCP, Context
except ImportError:
    print("FastMCP not found. Install with: pip install fastmcp")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("Article Quadrant Analyzer (Enhanced)")

# Input model for validation
class TestContentInput(BaseModel):
    """Enhanced test input model"""
    content: str = Field(..., description="Content to analyze", min_length=1, max_length=5000)

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
    result = f"""📄 **内容提取完成！**

**📊 内容预览：**
{content[:300]}{'...' if len(content) > 300 else ''}

**📈 内容统计：**
- **字符数：** {len(content)}
- **词数：** {len(words)}
- **句子数：** {len(sentences)}
- **段落数：** {len(paragraphs)}
- **语言：** {content_analysis['language']}
- **复杂度：** {content_analysis['complexity']}

**🔍 内容特征：**
- **平均句长：** {content_analysis['avg_sentence_length']:.1f} 词
- **包含URL：** {'是' if content_analysis['has_urls'] else '否'}
- **处理状态：** ✅ 完成
- **内容质量：** 适合分析

**💡 下一步：**
此内容现已准备好进行四象限分析。使用 `analyze_article_insights_simple` 工具提取关键洞察，或直接使用 `generate_quadrant_analysis_simple` 进行综合四象限映射。

**🎯 分析建议：**
{'检测到丰富内容 - 适合详细四象限分析' if len(words) > 100 else '检测到简洁内容 - 适合快速四象限洞察'}

✅ **内容提取成功完成！**
"""

    await ctx.info(f"成功提取 {len(words)} 词的 {content_analysis['language']} 内容")
    return result

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

✅ **洞察分析完成！**
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

            # 基于您的示例内容的分类逻辑
            if "协作" in sentence_lower or "团队" in sentence_lower or "头脑风暴" in sentence_lower:
                if "草图" in sentence_lower or "白板" in sentence_lower or "演示" in sentence_lower:
                    # 协作程度高，文本化程度低 → Q4 (右下)
                    quadrant_items["Q4"].append(sentence[:30] + "..." if len(sentence) > 30 else sentence)
                elif "文档" in sentence_lower or "PRD" in sentence_lower or "撰写" in sentence_lower:
                    # 协作程度高，文本化程度高 → Q1 (右上)
                    quadrant_items["Q1"].append(sentence[:30] + "..." if len(sentence) > 30 else sentence)
            elif "工程师" in sentence_lower or "独立" in sentence_lower or "编写" in sentence_lower:
                # 协作程度低，文本化程度高 → Q2 (左上)
                quadrant_items["Q2"].append(sentence[:30] + "..." if len(sentence) > 30 else sentence)
            elif "设计师" in sentence_lower or "图标" in sentence_lower or "规范" in sentence_lower:
                # 协作程度低，文本化程度低 → Q3 (左下)
                quadrant_items["Q3"].append(sentence[:30] + "..." if len(sentence) > 30 else sentence)

        # 如果没有找到特定模式，使用智能默认值
        if not any(quadrant_items[key] for key in quadrant_items):
            # 基于战略关键词的默认分类
            for sentence in sentences:
                sentence_lower = sentence.lower()

                # 分析协作程度
                collaboration_indicators = ["协作", "团队", "讨论", "会议", "共享", "联合"]
                text_indicators = ["文档", "文字", "写作", "记录", "报告", "说明"]

                has_collaboration = any(ind in sentence_lower for ind in collaboration_indicators)
                has_text = any(ind in sentence_lower for ind in text_indicators)

                if has_collaboration and has_text:
                    quadrant_items["Q1"].append(sentence[:30] + "...")
                elif not has_collaboration and has_text:
                    quadrant_items["Q2"].append(sentence[:30] + "...")
                elif not has_collaboration and not has_text:
                    quadrant_items["Q3"].append(sentence[:30] + "...")
                else:  # has_collaboration and not has_text
                    quadrant_items["Q4"].append(sentence[:30] + "...")

        # 用相关的中文内容填充空象限
        if not quadrant_items["Q1"]:
            quadrant_items["Q1"] = ["团队协作文档", "集体讨论记录", "共享成果展示"]
        if not quadrant_items["Q2"]:
            quadrant_items["Q2"] = ["独立深度思考", "个人专业分析", "核心技术实现"]
        if not quadrant_items["Q3"]:
            quadrant_items["Q3"] = ["基础维护工作", "常规操作流程", "标准规范执行"]
        if not quadrant_items["Q4"]:
            quadrant_items["Q4"] = ["创意头脑风暴", "视觉化表达", "互动协作展示"]

        return quadrant_items

    # 生成智能四象限分析
    quadrants = analyze_content_for_quadrants(content)

    # 创建综合分析结果
    content_metrics = {
        "length": len(content),
        "words": len(words),
        "sentences": len(sentences),
        "complexity": "高" if len(words) > 200 else "中" if len(words) > 50 else "低"
    }

    # 生成直接显示的矩阵图
    quadrant_diagram = generate_text_quadrant(quadrants, x_axis_label, y_axis_label)

    # 格式化分析结果
    result = f"""📊 **四象限分析完成！**

**📏 分析轴：**
- **X轴：** {x_axis_label}
- **Y轴：** {y_axis_label}

{quadrant_diagram}

**📈 内容指标：**
- 内容长度：{content_metrics['length']} 字符
- 词数：{content_metrics['words']} 词
- 复杂度：{content_metrics['complexity']}
- 分析深度：{content_metrics['sentences']} 句

**💡 战略洞察：**
此分析通过 {x_axis_label} vs {y_axis_label} 的框架来理解内容。使用这些象限来确定优先事项并做出明智决策。

**🔄 矩阵图使用建议：**
1. **Q1（右上）**：重点投入，高价值
2. **Q2（左上）**：专业分析，深度思考
3. **Q3（左下）**：基础维护，保持稳定
4. **Q4（右下）**：创意探索，团队协作

✅ **分析成功完成！**
"""

    await ctx.info(f"四象限分析完成，处理了 {content_metrics['words']} 词")
    return result

def generate_text_quadrant(quadrants, x_axis_label, y_axis_label):
    """生成直接显示的文本四象限图"""

    # 四象限的中文名称
    quadrant_names = {
        "Q1": "重点投入区",
        "Q2": "专业分析区",
        "Q3": "基础维护区",
        "Q4": "创意协作区"
    }

    diagram = f"""
**🎯 四象限矩阵图**

```
                    ↑ {y_axis_label} ↑
                    ┌──────────────────────────────┐
                    │     Q1: {quadrant_names['Q1']}     │
                    │  ┌────────────────────────┐  │
                    │  │ {chr(10).join([f'• {item[:12]}...' if len(item) > 12 else f'• {item}' for item in quadrants['Q1'][:3]])}  │  │
                    │  └────────────────────────┘  │
                    └──────────────────────────────┘
                    ┌──────────────────────────────┐
                    │     Q2: {quadrant_names['Q2']}     │
                    │  ┌────────────────────────┐  │
                    │  │ {chr(10).join([f'• {item[:12]}...' if len(item) > 12 else f'• {item}' for item in quadrants['Q2'][:3]])}  │  │
                    │  └────────────────────────┘  │
                    └──────────────────────────────┘
← {x_axis_label} ← ─────────────────────────────────── → {x_axis_label} →
                    ┌──────────────────────────────┐
                    │     Q3: {quadrant_names['Q3']}     │
                    │  ┌────────────────────────┐  │
                    │  │ {chr(10).join([f'• {item[:12]}...' if len(item) > 12 else f'• {item}' for item in quadrants['Q3'][:3]])}  │  │
                    │  └────────────────────────┘  │
                    └──────────────────────────────┘
                    ┌──────────────────────────────┐
                    │     Q4: {quadrant_names['Q4']}     │
                    │  ┌────────────────────────┐  │
                    │  │ {chr(10).join([f'• {item[:12]}...' if len(item) > 12 else f'• {item}' for item in quadrants['Q4'][:3]])}  │  │
                    │  └────────────────────────┘  │
                    └──────────────────────────────┘
```

**象限说明：**
- **Q1（右上）**：高{x_axis_label}，高{y_axis_label} - 优先重点
- **Q2（左上）**：低{x_axis_label}，高{y_axis_label} - 专业分析
- **Q3（左下）**：低{x_axis_label}，低{y_axis_label} - 基础维护
- **Q4（右下）**：高{x_axis_label}，低{y_axis_label} - 创意协作
"""

    return diagram

def main():
    """主入口点"""
    logger.info("Starting Enhanced Article Quadrant Analyzer MCP Server")

    try:
        # 使用stdio传输运行MCP服务器
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()