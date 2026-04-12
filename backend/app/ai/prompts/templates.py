"""
提示词模板
RAG 问答和其他 AI 任务的提示词
"""
from typing import Optional


def get_rag_prompt(
    teacher_name: str,
    personality: str,
    catchphrase: str,
    context: str,
    question: str
) -> str:
    """
    构建 RAG 问答提示词

    Args:
        teacher_name: 教师分身名称
        personality: 性格特征
        catchphrase: 口头禅
        context: 检索到的上下文
        question: 学生问题

    Returns:
        完整的提示词
    """
    prompt = f"""
你是教师数字分身 **{teacher_name}**。

## 你的身份特征
- **性格:** {personality}
- **口头禅:** {catchphrase}

## 参考文档
{context if context else "暂无相关文档"}

## 学生问题
{question}

## 回答要求
1. 基于参考文档回答问题
2. 如果文档中没有相关信息,请礼貌地说明:"这个问题超出了我目前的知识范围"
3. 保持你的性格特征,适当使用口头禅
4. 回答要简洁明了,语气友好
5. 如果涉及专业知识,要准确且易于理解

请开始回答:
"""
    return prompt


def get_summary_prompt(text: str, max_length: int = 200) -> str:
    """
    构建文本总结提示词

    Args:
        text: 待总结的文本
        max_length: 最大长度

    Returns:
        提示词
    """
    prompt = f"""
请将以下文本总结为 {max_length} 字以内的摘要:

{text}

要求:
1. 保留核心信息
2. 语言简洁
3. 逻辑清晰

摘要:
"""
    return prompt


def get_xiaohongshu_prompt(title: str, content: str) -> str:
    """
    构建小红书文案生成提示词

    Args:
        title: 标题
        content: 内容

    Returns:
        提示词
    """
    prompt = f"""
基于以下内容,生成一篇小红书风格的文案:

**标题:** {title}
**内容:** {content}

要求:
1. 使用emoji表情
2. 标签化语言 (#学术 #干货)
3. 短段落,易于阅读
4. 语气轻松活泼
5. 突出亮点和实用价值

请生成文案:
"""
    return prompt


def get_poster_prompt(copy: str) -> str:
    """
    构建海报提示词生成提示词

    Args:
        copy: 小红书文案

    Returns:
        提示词
    """
    prompt = f"""
基于以下小红书文案,生成 DALL-E 3 图片提示词:

**文案:** {copy}

要求:
1. 描述画面主体、风格、色调
2. 突出学术感但不失活泼
3. 适合小红书分享的竖版海报
4. 英文提示词,100词以内

请生成 DALL-E 提示词:
"""
    return prompt


def get_broadcast_prompt(
    teacher_name: str,
    personality: str,
    content: str
) -> str:
    """
    构建广播消息提示词

    Args:
        teacher_name: 教师名称
        personality: 性格特征
        content: 广播内容

    Returns:
        提示词
    """
    prompt = f"""
你是教师 {teacher_name},性格特点是 {personality}。

请将以下内容改写为一条班级广播消息:

**原始内容:** {content}

要求:
1. 语气符合你的性格特点
2. 友好且具有号召力
3. 简洁明了,适合快速阅读
4. 可以适当添加emoji

请生成广播消息:
"""
    return prompt
