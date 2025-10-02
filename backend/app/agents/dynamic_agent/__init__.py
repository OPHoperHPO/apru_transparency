from app.agents.dynamic_agent.agent import root_agent
__all__ = ["root_agent", "analyze_website"]
def analyze_website(url: str, goal: str = "Analyze website for dark patterns and transparency issues"):
    from app.agents.dynamic_agent.agents.
    from google.adk.agents import SequentialAgent
    pipeline = SequentialAgent(
        name="website_analysis_pipeline",
        description="Analyze website for dark patterns",
        sub_agents=[
            ingest_agent,
            browser_loop,
        ],
    )
    initial_state = {
        "url": url,
        "goal": goal,
        "success_criteria": [
            "Identify any dark patterns on the website",
            "Analyze transparency of terms and conditions",
            "Check for manipulative UI elements",
            "Evaluate user consent mechanisms"
        ]
    }
    try:
        result = pipeline.run(state=initial_state)
        final_data = result.state.get("final_data", {})
        final_summary = result.state.get("final_summary", "Analysis completed")
        parsed_data = result.state.get("parsed", {})
        dark_patterns = final_data.get("dark_patterns", []) if isinstance(final_data, dict) else []
        if isinstance(dark_patterns, str):
            dark_patterns = []
        transparency_score = max(0, 100 - (len(dark_patterns) * 10))
        return {
            'url': url,
            'transparency_score': transparency_score,
            'dark_patterns': dark_patterns,
            'summary': final_summary,
            'detailed_findings': parsed_data,
            'status': 'completed'
        }
    except Exception as e:
        return {
            'url': url,
            'transparency_score': 0,
            'dark_patterns': [],
            'summary': f'Analysis failed: {str(e)}',
            'error': str(e),
            'status': 'failed'
        }
