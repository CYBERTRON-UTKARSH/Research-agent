"""
Modern Research Pipeline with Streaming and Flask Integration
Uses new LangChain agent patterns
"""

import json
import asyncio
from typing import AsyncGenerator, Dict, Any
from datetime import datetime
from agents import (
    build_search_agent,
    build_reader_agent,
    writer_chain,
    critic_chain,
    refine_chain
)


class ResearchPipeline:
    """Modern research pipeline orchestrator"""
    
    def __init__(self):
        self.state = {}
        self.logs = []
    
    def add_log(self, step: int, title: str, status: str, content: str = "", duration: float = 0):
        """Add a log entry"""
        log_entry = {
            "step": step,
            "title": title,
            "status": status,
            "content": content[:500] if content else "",  # Limit content size
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.logs.append(log_entry)
        return log_entry
    
    def extract_content(self, response: Any) -> str:
        """Extract text content from agent response"""
        try:
            # Handle direct string responses
            if isinstance(response, str):
                return response
            
            # Handle dict responses (LangGraph output)
            if isinstance(response, dict):
                # Check for messages field
                if "messages" in response:
                    messages = response["messages"]
                    if isinstance(messages, list) and len(messages) > 0:
                        last_msg = messages[-1]
                        # Handle message objects with content attribute
                        if hasattr(last_msg, 'content'):
                            return str(last_msg.content)
                        # Handle tuples (role, content)
                        if isinstance(last_msg, tuple) and len(last_msg) > 1:
                            return str(last_msg[1])
                        # Handle dicts
                        if isinstance(last_msg, dict):
                            return str(last_msg.get('content', last_msg))
                        return str(last_msg)
                
                # Check for output field
                if "output" in response:
                    return str(response["output"])
                
                # Check for text field
                if "text" in response:
                    return str(response["text"])
                
                # Check for content field
                if "content" in response:
                    return str(response["content"])
            
            # Handle objects with content attribute
            if not isinstance(response, dict) and hasattr(response, 'content'):
                return str(response.content)
            
            # Default: convert to string
            return str(response)
            
        except Exception as e:
            return f"Error extracting content: {str(e)}"
    
    async def run_research_pipeline(self, topic: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Run the research pipeline with streaming updates.
        Yields progress updates to frontend.
        """
        import time
        
        try:
            # Step 1: Search Agent
            yield {
                "step": 1,
                "status": "running",
                "title": "🔍 Search Agent - Finding Information",
                "message": f"Searching for information about: {topic}"
            }
            
            start_time = time.time()
            try:
                search_agent = build_search_agent()
                
                search_result = search_agent.invoke({
                    "messages": [
                        {
                            "role": "user",
                            "content": f"Find recent, reliable and detailed information about: {topic}"
                        }
                    ]
                })
                
                self.state["search_results"] = self.extract_content(search_result)
            except Exception as e:
                self.state["search_results"] = f"Search failed: {str(e)}"
            
            search_duration = time.time() - start_time
            self.add_log(1, "Search Agent", "completed", self.state["search_results"], search_duration)
            
            yield {
                "step": 1,
                "status": "completed",
                "title": "🔍 Search Agent - Complete",
                "message": "Successfully gathered search results",
                "content": self.state["search_results"][:1000],
                "duration": f"{search_duration:.2f}s"
            }
            
            # Small delay for UI animation
            await asyncio.sleep(0.5)
            
            # Step 2: Reader Agent
            yield {
                "step": 2,
                "status": "running",
                "title": "📖 Reader Agent - Scraping Resources",
                "message": "Analyzing and scraping top resources..."
            }
            
            start_time = time.time()
            try:
                reader_agent = build_reader_agent()
                
                reader_result = reader_agent.invoke({
                    "messages": [
                        {
                            "role": "user",
                            "content": (
                                f"Based on this search about '{topic}', pick the most relevant "
                                f"URL and scrape it for deeper content.\n\n"
                                f"Search Results:\n{self.state['search_results'][:800]}"
                            )
                        }
                    ]
                })
                
                self.state["scraped_content"] = self.extract_content(reader_result)
            except Exception as e:
                self.state["scraped_content"] = f"Reader failed: {str(e)}"
            
            reader_duration = time.time() - start_time
            self.add_log(2, "Reader Agent", "completed", self.state["scraped_content"], reader_duration)
            
            yield {
                "step": 2,
                "status": "completed",
                "title": "📖 Reader Agent - Complete",
                "message": "Successfully scraped and analyzed content",
                "content": self.state["scraped_content"][:1000],
                "duration": f"{reader_duration:.2f}s"
            }
            
            await asyncio.sleep(0.5)
            
            # Step 3: Writer Chain
            yield {
                "step": 3,
                "status": "running",
                "title": "✍️ Writer - Drafting Report",
                "message": "Composing detailed research report..."
            }
            
            start_time = time.time()
            try:
                research_combined = (
                    f"## SEARCH RESULTS:\n{self.state['search_results']}\n\n"
                    f"## DETAILED SCRAPED CONTENT:\n{self.state['scraped_content']}"
                )
                
                self.state["report"] = writer_chain.invoke({
                    "topic": topic,
                    "research": research_combined
                })
                
                # Extract content if it's not already a string
                if not isinstance(self.state["report"], str):
                    self.state["report"] = self.extract_content(self.state["report"])
                    
            except Exception as e:
                self.state["report"] = f"Writer failed: {str(e)}"
            
            writer_duration = time.time() - start_time
            self.add_log(3, "Writer", "completed", self.state["report"], writer_duration)
            
            yield {
                "step": 3,
                "status": "completed",
                "title": "✍️ Writer - Report Complete",
                "message": "Research report drafted successfully",
                "content": self.state["report"][:1500],
                "duration": f"{writer_duration:.2f}s"
            }
            
            await asyncio.sleep(0.5)
            
            # Step 4: Critic Review
            yield {
                "step": 4,
                "status": "running",
                "title": "🔍 Critic - Reviewing Report",
                "message": "Evaluating report quality and completeness..."
            }
            
            start_time = time.time()
            try:
                self.state["feedback"] = critic_chain.invoke({
                    "report": self.state["report"]
                })
                
                if not isinstance(self.state["feedback"], str):
                    self.state["feedback"] = self.extract_content(self.state["feedback"])
                    
            except Exception as e:
                self.state["feedback"] = f"Critic failed: {str(e)}"
            
            critic_duration = time.time() - start_time
            self.add_log(4, "Critic", "completed", self.state["feedback"], critic_duration)
            
            yield {
                "step": 4,
                "status": "completed",
                "title": "🔍 Critic - Review Complete",
                "message": "Evaluation complete",
                "content": self.state["feedback"][:1500],
                "duration": f"{critic_duration:.2f}s"
            }
            
            await asyncio.sleep(0.5)
            
            # Step 5: Optional Refinement
            yield {
                "step": 5,
                "status": "running",
                "title": "🔧 Refiner - Improving Report",
                "message": "Applying critic feedback to improve report..."
            }
            
            start_time = time.time()
            try:
                self.state["refined_report"] = refine_chain.invoke({
                    "report": self.state["report"],
                    "feedback": self.state["feedback"]
                })
                
                if not isinstance(self.state["refined_report"], str):
                    self.state["refined_report"] = self.extract_content(self.state["refined_report"])
                    
            except Exception as e:
                self.state["refined_report"] = self.state.get("report", f"Refiner failed: {str(e)}")
            
            refine_duration = time.time() - start_time
            self.add_log(5, "Refiner", "completed", self.state["refined_report"], refine_duration)
            
            yield {
                "step": 5,
                "status": "completed",
                "title": "🔧 Refiner - Complete",
                "message": "Report refined based on feedback",
                "content": self.state["refined_report"][:1500],
                "duration": f"{refine_duration:.2f}s"
            }
            
            # Final Summary
            yield {
                "step": 6,
                "status": "completed",
                "title": "✅ Pipeline Complete",
                "message": "Research pipeline executed successfully!",
                "summary": {
                    "topic": topic,
                    "total_steps": 5,
                    "search_results_length": len(self.state.get("search_results", "")),
                    "report_length": len(self.state.get("refined_report", "")),
                    "total_logs": len(self.logs)
                }
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield {
                "step": -1,
                "status": "error",
                "title": "❌ Pipeline Error",
                "message": f"Error occurred: {str(e)}",
                "error": str(e)
            }
    
    def get_full_report(self) -> Dict[str, Any]:
        """Get complete pipeline results"""
        return {
            "search_results": self.state.get("search_results", ""),
            "scraped_content": self.state.get("scraped_content", ""),
            "initial_report": self.state.get("report", ""),
            "feedback": self.state.get("feedback", ""),
            "refined_report": self.state.get("refined_report", ""),
            "logs": self.logs
        }


# ============================================
# CLI Usage (if running directly)
# ============================================

async def main():
    """Run pipeline from command line"""
    topic = input("\n🔬 Enter a research topic: ").strip()
    
    if not topic:
        print("❌ Error: Please enter a valid topic!")
        return
    
    pipeline = ResearchPipeline()
    
    try:
        async for update in pipeline.run_research_pipeline(topic):
            if update["status"] == "running":
                print(f"\n⏳ {update['title']}")
                print(f"   {update['message']}")
            elif update["status"] == "completed":
                print(f"\n✅ {update['title']}")
                print(f"   {update['message']}")
                if "duration" in update:
                    print(f"   ⏱️  Duration: {update['duration']}")
            elif update["status"] == "error":
                print(f"\n❌ {update['title']}")
                print(f"   {update['message']}")
        
        # Print final report
        print("\n" + "="*60)
        print("📄 FINAL REFINED REPORT")
        print("="*60)
        print(pipeline.state.get("refined_report", ""))
        
    except KeyboardInterrupt:
        print("\n\n⛔ Pipeline interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())