"""
Modern LangChain Agents using LangGraph create_agent
Updated from deprecated create_react_agent
"""

from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from tools import web_search, scrape_url
from dotenv import load_dotenv

load_dotenv()

# ============================================
# Modern LLM Setup
# ============================================

from langchain_groq import ChatGroq

llm = ChatGroq(model="qwen/qwen3.8-27b", temperature=0)

# ============================================
# 1st Agent - Search Agent (Modern)
# ============================================

def build_search_agent():
    """
    Build search agent using modern create_agent.
    This replaces the old create_react_agent pattern.
    """
    return create_agent(
        model=llm,
        tools=[web_search],
        system_prompt="You are an expert research assistant. Find recent, reliable and detailed information. "
               "Always search thoroughly and return complete information with all URLs."
    )


# ============================================
# 2nd Agent - Reader Agent (Modern)
# ============================================

def build_reader_agent():
    """
    Build reader agent using modern create_agent.
    Scrapes and extracts content from URLs.
    """
    return create_agent(
        model=llm,
        tools=[scrape_url],
        system_prompt="You are an expert web content analyzer. Scrape URLs and extract the most relevant "
               "and detailed information. Focus on main content, not ads or sidebars."
    )


# ============================================
# Writer Chain (LLM-based)
# ============================================

writer_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are an expert research writer specializing in creating clear, structured, and insightful reports. "
     "Write in professional academic style with proper citations."),
    ("human", """Write a detailed research report on the following topic.

Topic: {topic}

Research Gathered:
{research}

Please structure the report as follows:

## Introduction
Brief overview of the topic and its relevance.

## Key Findings
- Present at least 3 well-researched and explained points
- Each point should be substantive and based on the research data
- Include specific examples and statistics where available

## Analysis
Deep dive into the implications and significance of the findings.

## Conclusion
Summarize key points and suggest areas for further research.

## Sources
List all URLs found in the research material.

Requirements:
- Be detailed, factual, and professional
- Use proper markdown formatting
- Aim for 1500-2000 words
- Include data-driven insights"""),
])

writer_chain = writer_prompt | llm | StrOutputParser()


# ============================================
# Critic Chain (LLM-based)
# ============================================

critic_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are a sharp and constructive research critic with expertise in evaluating academic and "
     "professional reports. Be honest, specific, and fair in your assessment."),
    ("human", """Review and evaluate the following research report with critical analysis.

Report:
{report}

Please provide your evaluation in this exact format:

**Score: X/10**

**Strengths:**
- [List 3-5 key strengths of the report]
- Include what was done well in research and presentation

**Areas to Improve:**
- [List 3-5 specific areas for improvement]
- Be constructive and suggest how to improve

**Missing Elements:**
- Any important information that should have been included

**Verdict:**
[One concise sentence summarizing your overall assessment]

**Recommendations:**
[2-3 actionable recommendations for improvement]"""),
])

critic_chain = critic_prompt | llm | StrOutputParser()


# ============================================
# Optional: Multi-step Refinement Chain
# ============================================

refine_prompt = ChatPromptTemplate.from_messages([
    ("system", 
     "You are an expert editor and researcher. Your job is to refine and improve reports based on feedback."),
    ("human", """Refine the following report based on the critic's feedback.

Original Report:
{report}

Critic's Feedback:
{feedback}

Please:
1. Maintain the good parts identified as strengths
2. Address the specific areas for improvement
3. Add any missing elements mentioned
4. Improve overall clarity and flow
5. Keep the professional tone

Return the improved report in markdown format."""),
])

refine_chain = refine_prompt | llm | StrOutputParser()


# ============================================
# Export all chains and agents
# ============================================

__all__ = [
    'build_search_agent',
    'build_reader_agent',
    'writer_chain',
    'critic_chain',
    'refine_chain',
    'llm'
]