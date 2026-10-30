"""
Modern Flask Backend for Research Pipeline
With streaming SSE (Server-Sent Events) support
"""

from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import asyncio
import json
import os
from datetime import datetime
from pipeline import ResearchPipeline
import logging
import threading

# ============================================
# Flask App Setup
# ============================================

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)

CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global pipeline instance
current_pipeline = None


# ============================================
# Helper Functions
# ============================================

def run_async_in_thread(coro):
    """Run async code in a separate thread's event loop"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ============================================
# Routes
# ============================================

@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')


@app.route('/api/research', methods=['POST'])
def start_research():
    """
    Start research pipeline with streaming.
    Uses Server-Sent Events for real-time updates.
    """
    data = request.json
    topic = data.get('topic', '').strip()
    
    if not topic or len(topic) < 3:
        return jsonify({
            "error": "Topic must be at least 3 characters long"
        }), 400
    
    def generate_events():
        """Generator for SSE events"""
        global current_pipeline
        
        try:
            pipeline = ResearchPipeline()
            current_pipeline = pipeline
            
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def consume_pipeline():
                """Consume the async generator"""
                async for update in pipeline.run_research_pipeline(topic):
                    yield update
            
            try:
                # Run the async generator
                gen = consume_pipeline()
                
                async def get_all_events():
                    events = []
                    async for update in gen:
                        events.append(f"data: {json.dumps(update)}\n\n")
                    return events
                
                events = loop.run_until_complete(get_all_events())
                for event in events:
                    yield event
                    
            finally:
                loop.close()
            
        except Exception as e:
            logger.error(f"Pipeline error: {str(e)}", exc_info=True)
            error_event = {
                "step": -1,
                "status": "error",
                "title": "❌ Pipeline Error",
                "message": f"Error: {str(e)}"
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return Response(
        generate_events(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Access-Control-Allow-Origin': '*'
        }
    )


@app.route('/api/report', methods=['GET'])
def get_report():
    """Get the current report data"""
    global current_pipeline
    
    if not current_pipeline:
        return jsonify({
            "error": "No pipeline running. Start a research first."
        }), 400
    
    try:
        report = current_pipeline.get_full_report()
        return jsonify(report)
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get pipeline status"""
    global current_pipeline
    
    if not current_pipeline:
        return jsonify({
            "status": "idle",
            "message": "No research in progress"
        })
    
    logs = current_pipeline.logs
    return jsonify({
        "status": "running" if len(logs) > 0 else "idle",
        "completed_steps": len([l for l in logs if l.get('status') == 'completed']),
        "total_logs": len(logs)
    })


@app.route('/api/download-report', methods=['GET'])
def download_report():
    """Download report as markdown"""
    global current_pipeline
    
    if not current_pipeline or not current_pipeline.state.get('refined_report'):
        return jsonify({
            "error": "No report available"
        }), 400
    
    try:
        report = current_pipeline.state.get('refined_report', '')
        topic = current_pipeline.logs[0].get('title', 'research') if current_pipeline.logs else 'research'
        
        # Create markdown content
        markdown_content = f"""# Research Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{report}

---

## About This Report
This report was generated using AI Research Pipeline with LangChain and LangGraph.
"""
        
        return jsonify({
            "content": markdown_content,
            "filename": f"research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        })
    
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app.route('/api/export-json', methods=['GET'])
def export_json():
    """Export all data as JSON"""
    global current_pipeline
    
    if not current_pipeline:
        return jsonify({
            "error": "No data to export"
        }), 400
    
    try:
        data = current_pipeline.get_full_report()
        data['generated_at'] = datetime.now().isoformat()
        return jsonify(data)
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@app.route('/api/clear', methods=['POST'])
def clear_pipeline():
    """Clear current pipeline"""
    global current_pipeline
    
    current_pipeline = None
    return jsonify({
        "status": "cleared",
        "message": "Pipeline cleared successfully"
    })


# ============================================
# Error Handlers
# ============================================

@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return jsonify({
        "error": "Endpoint not found",
        "status": 404
    }), 404


@app.errorhandler(500)
def server_error(error):
    """500 error handler"""
    logger.error(f"Server error: {str(error)}", exc_info=True)
    return jsonify({
        "error": "Internal server error",
        "status": 500
    }), 500


# ============================================
# Application Entry Point
# ============================================

if __name__ == "__main__":
    # Create required directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║       🚀 AI Research Pipeline - Modern LangChain           ║
    ║                                                            ║
    ║       Server running at: http://localhost:5000             ║
    ║                                                            ║
    ║       Features:                                            ║
    ║       ✓ Real-time streaming updates                        ║
    ║       ✓ Beautiful animated UI                              ║
    ║       ✓ Download reports as markdown                       ║
    ║       ✓ Export data as JSON                                ║
    ║                                                            ║
    ║       Press CTRL+C to stop                                 ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Run development server
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False  # Set to False to avoid event loop issues
    )