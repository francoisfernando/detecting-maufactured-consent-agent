import asyncio
import streamlit as st
import json
from dotenv import load_dotenv

# Load environment variables (such as GEMINI_API_KEY)
load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.genai import types

# Page config
st.set_page_config(
    page_title="Ambient Manufactured Consent Detector",
    page_icon="🕵️‍♂️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main {
        background-color: #0e1117;
    }
    .stAlert {
        border-radius: 8px;
    }
    .mci-header {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        color: #ff4b4b;
    }
    .metric-container {
        background-color: #1e293b;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #334155;
        text-align: center;
        margin-bottom: 20px;
    }
    .pillar-card {
        background-color: #0f172a;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #1e293b;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to run the async runner pipeline
async def run_pipeline(prompt, session_id):
    from app.agent import app as adk_app
    from app.agent import root_agent

    # Initialize Runner
    runner = Runner(
        app=adk_app,
        session_service=InMemorySessionService(),
        artifact_service=InMemoryArtifactService(),
        auto_create_session=True,
    )
    
    user_message = types.Content(
        parts=[types.Part.from_text(text=prompt)]
    )
    
    # We yield events as they come
    async for event in runner.run_async(
        user_id="streamlit_user",
        session_id=session_id,
        new_message=user_message
    ):
        yield event, runner

def render_agents_list(active_agent_name=None, completed=False):
    agents = [
        ("scraper_agent", "📥 Scraper Agent", "Text extraction"),
        ("translation_agent", "🗣️ Translation Agent", "Language translation"),
        ("research_agent", "🔍 Research Agent", "Dynamic web research"),
        ("timeline_agent", "⏳ Timeline Agent", "Media & campaign timeline"),
        ("context_router", "🧭 Context Router", "Deciding regional routing"),
        ("context_specialist", "🌍 Context Specialist", "Sri Lankan, Russian, or Generic context"),
        ("analysis_agent", "📊 Analysis Agent", "MCI Score & Report")
    ]
    
    html_lines = []
    for key, name, desc in agents:
        is_active = False
        if active_agent_name:
            if key == active_agent_name:
                is_active = True
            elif key == "context_specialist" and active_agent_name in [
                "sri_lankan_context_specialist",
                "russian_context_specialist",
                "generic_context_specialist"
            ]:
                is_active = True

        if completed:
            html_lines.append(f"<div style='background-color: #2e7d3222; border-left: 4px solid #2e7d32; padding: 10px; border-radius: 4px; margin-bottom: 8px; font-family: sans-serif;'>✅ <b>{name}</b><br><small style='opacity: 0.8;'>{desc}</small></div>")
        elif is_active:
            html_lines.append(f"<div style='background-color: #ff4b4b22; border-left: 4px solid #ff4b4b; padding: 10px; border-radius: 4px; margin-bottom: 8px; font-family: sans-serif;'>⚡ <b>{name} (Active)</b><br><small style='opacity: 0.9;'>{desc}</small></div>")
        else:
            html_lines.append(f"<div style='padding: 10px; border-left: 4px solid transparent; margin-bottom: 8px; opacity: 0.5; font-family: sans-serif;'><b>{name}</b><br><small>{desc}</small></div>")
            
    return "\n".join(html_lines)

# Streamlit App UI
st.title("🕵️‍♂️ Ambient Manufactured Consent Detector")
st.markdown("""
This system uses a **Google ADK Multi-Agent Pipeline** to analyze media articles, blog posts, or YouTube transcripts. 
It extracts key organizations, performs live web research to identify funding/government backing, assesses local geopolitical contexts (with a focus on Sri Lanka), and calculates a **Manufactured Consent Index (MCI)**.
""")

st.sidebar.header("Configuration & Settings")
st.sidebar.markdown("### Agentic Pipeline Status:")
agent_list_placeholder = st.sidebar.empty()
agent_list_placeholder.markdown(render_agents_list(), unsafe_allow_html=True)

st.sidebar.markdown("---")
session_id = st.sidebar.text_input("Session ID", value="demo-session-1")

# Input Section
st.subheader("1. Ingest Media Artifact")
input_type = st.radio("Select Input Type:", ["Web URL", "Raw Text"])

user_input = ""
if input_type == "Web URL":
    user_input = st.text_input("Enter article or video transcript URL:", placeholder="https://example.com/sri-lanka-news-article")
else:
    user_input = st.text_area("Paste raw text or transcript here:", height=200, placeholder="Paste text here...")

analyze_button = st.button("🚀 Analyze Media Artifact", use_container_width=True)

if analyze_button:
    if not user_input.strip():
        st.error("Please provide a valid URL or text to analyze.")
    else:
        # Create an event log area
        st.subheader("2. Multi-Agent Reasoning Trace")
        status_box = st.status("Initializing multi-agent pipeline...", expanded=True)
        log_area = st.empty()
        
        events_log = []
        
        # Define execution wrapper to run in Streamlit's event loop
        async def execute():
            runner_instance = None
            async for event, runner in run_pipeline(user_input, session_id):
                runner_instance = runner
                
                # Update sidebar highlighting
                if event.author in [
                    "scraper_agent",
                    "translation_agent",
                    "research_agent",
                    "timeline_agent",
                    "context_router",
                    "sri_lankan_context_specialist",
                    "russian_context_specialist",
                    "generic_context_specialist",
                    "analysis_agent"
                ]:
                    agent_list_placeholder.markdown(render_agents_list(event.author), unsafe_allow_html=True)
                
                # Determine nice formatting for the event
                author_display = f"🤖 **{event.author}**"
                if event.author == "scraper_agent":
                    status_box.update(label="📥 Scraper Agent: Extracting article text...")
                elif event.author == "translation_agent":
                    status_box.update(label="🗣️ Translation Agent: Translating text...")
                elif event.author == "research_agent":
                    status_box.update(label="🔍 Research Agent: Dynamic web search...")
                elif event.author == "timeline_agent":
                    status_box.update(label="⏳ Timeline Agent: Investigating media timeline...")
                elif event.author == "context_router":
                    status_box.update(label="🧭 Context Router: Resolving regional context routing...")
                elif event.author == "sri_lankan_context_specialist":
                    status_box.update(label="🇱🇰 Sri Lankan Context Specialist: Checking local history...")
                elif event.author == "russian_context_specialist":
                    status_box.update(label="🇷🇺 Russian Context Specialist: Checking Kremlin backing...")
                elif event.author == "generic_context_specialist":
                    status_box.update(label="🌍 Generic Context Specialist: Analyzing generic context...")
                elif event.author == "analysis_agent":
                    status_box.update(label="📊 Analysis Agent: Computing MCI scorecard...")
                elif event.author == "google_search":
                    author_display = "🌐 **Google Search Tool**"
                elif event.author == "scrape_article":
                    author_display = "📄 **Article Scraper Tool**"
                
                if event.content:
                    events_log.append(f"{author_display}: {event.content}")
                    log_area.markdown("\n\n".join(events_log))
            
            # Update sidebar to show all completed
            agent_list_placeholder.markdown(render_agents_list(completed=True), unsafe_allow_html=True)
            status_box.update(label="✅ Analysis complete!", state="complete", expanded=False)
            return runner_instance

        # Run async event loop
        final_runner = asyncio.run(execute())
        
        # Display Results
        if final_runner:
            async def get_results():
                session = await final_runner.session_service.get_session(
                    app_name="app",
                    user_id="streamlit_user",
                    session_id=session_id
                )
                return session.state
                
            state = asyncio.run(get_results())
            
            scraped = state.get("scraped_content", "")
            translated = state.get("translated_content", "")
            research = state.get("research_brief", "")
            timeline = state.get("narrative_timeline", "")
            context = state.get("context_analysis", "")
            mci_report = state.get("mci_report")
            
            if mci_report:
                # Handle both Pydantic model and dict
                if not isinstance(mci_report, dict):
                    mci_data = mci_report
                else:
                    mci_data = json.loads(json.dumps(mci_report))
                
                # Get fields robustly
                def get_val(obj, key):
                    if hasattr(obj, key):
                        return getattr(obj, key)
                    return obj.get(key) if isinstance(obj, dict) else None
                
                overall_score = get_val(mci_data, "overall_score")
                sponsorship = get_val(mci_data, "sponsorship_transparency")
                narrative = get_val(mci_data, "narrative_unanimity")
                framing = get_val(mci_data, "loaded_framing")
                source_div = get_val(mci_data, "source_diversity")
                detected_actors = get_val(mci_data, "detected_actors") or []
                propaganda = get_val(mci_data, "propaganda_techniques") or []
                summary = get_val(mci_data, "executive_summary")
                verdict = get_val(mci_data, "final_verdict")
                
                st.subheader("3. Manufactured Consent Evaluation")
                
                # Score Layout
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
                    st.markdown("### Overall MCI Score")
                    
                    # Color based on risk level
                    if overall_score <= 30:
                        score_color = "#22c55e"
                        risk_level = "LOW RISK"
                    elif overall_score <= 70:
                        score_color = "#f97316"
                        risk_level = "MODERATE RISK"
                    else:
                        score_color = "#ef4444"
                        risk_level = "HIGH RISK"
                        
                    st.markdown(f"<h1 style='color: {score_color}; font-size: 64px; margin: 0;'>{overall_score}</h1>", unsafe_allow_html=True)
                    st.markdown(f"<strong style='color: {score_color};'>{risk_level}</strong>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Display Verdict
                    st.info(f"**Verdict:** {verdict}")
                    
                with col2:
                    st.markdown("### Scorecard Breakdown")
                    
                    def render_pillar(name, detail):
                        score = get_val(detail, "score") if detail else 0
                        just = get_val(detail, "justification") if detail else ""
                        st.markdown(f"<div class='pillar-card'>", unsafe_allow_html=True)
                        st.markdown(f"**{name}**: **{score}/100**")
                        st.progress(score / 100)
                        st.markdown(f"<small>{just}</small>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                    render_pillar("Pillar 1: Sponsorship & Funding Transparency", sponsorship)
                    render_pillar("Pillar 2: Narrative Unanimity", narrative)
                    render_pillar("Pillar 3: Loaded Framing & Rhetoric", framing)
                    render_pillar("Pillar 4: Source Diversity", source_div)
                
                # Actors and Techniques
                col_act, col_tech = st.columns(2)
                with col_act:
                    st.markdown("### 🏢 Detected Backing Actors")
                    if detected_actors:
                        for actor in detected_actors:
                            st.markdown(f"- **{actor}**")
                    else:
                        st.markdown("_No specific backing organizations identified._")
                with col_tech:
                    st.markdown("### 📢 Propaganda Techniques")
                    if propaganda:
                        for tech in propaganda:
                            st.markdown(f"- `{tech}`")
                    else:
                        st.markdown("_No specific propaganda techniques detected._")
                        
                # Executive Summary
                st.markdown("### 📝 Executive Summary")
                st.markdown(summary)
                
                # Collapsible Deep Dives
                st.markdown("### 🔍 Intermediate Analysis Details")
                with st.expander("Original & Translated Text Content"):
                    st.markdown(f"**Translated Content:**\n\n{translated}")
                    if scraped != translated:
                        st.markdown("---")
                        st.markdown(f"**Original Scraped Content:**\n\n{scraped}")
                        
                with st.expander("Web Research Brief (DuckDuckGo Search results)"):
                    st.markdown(research)
                    
                with st.expander("Preceding Media Timeline & Campaign Analysis"):
                    st.markdown(timeline)
                    
                with st.expander("Sri Lankan Context & Nuance Report"):
                    st.markdown(context)
                    
                # Download Report Button
                report_markdown = f"""# Manufactured Consent Analysis Report

* **Overall MCI Score**: {overall_score} / 100
* **Verdict**: {verdict}

## Scorecard Breakdown
* **Sponsorship & Funding Transparency**: {get_val(sponsorship, 'score') if sponsorship else 0}/100
  * *Justification*: {get_val(sponsorship, 'justification') if sponsorship else ''}
* **Narrative Unanimity**: {get_val(narrative, 'score') if narrative else 0}/100
  * *Justification*: {get_val(narrative, 'justification') if narrative else ''}
* **Loaded Framing & Rhetoric**: {get_val(framing, 'score') if framing else 0}/100
  * *Justification*: {get_val(framing, 'justification') if framing else ''}
* **Source Diversity**: {get_val(source_div, 'score') if source_div else 0}/100
  * *Justification*: {get_val(source_div, 'justification') if source_div else ''}

## Attributed Actors
{chr(10).join([f'* **{actor}**' for actor in detected_actors]) if detected_actors else '_None detected_'}

## Propaganda Techniques
{chr(10).join([f'* `{tech}`' for tech in propaganda]) if propaganda else '_None detected_'}

## Executive Summary
{summary}

## Dynamic Web Research Brief
{research}

## Preceding Media Timeline & Campaign Analysis
{timeline}

## Sri Lankan Context & Nuance Report
{context}
"""
                st.markdown("---")
                st.download_button(
                    label="📥 Download Full Report (Markdown)",
                    data=report_markdown,
                    file_name=f"MCI_Report_{session_id}.md",
                    mime="text/markdown"
                )
            else:
                st.error("Failed to retrieve the Manufactured Consent Index scorecard. Check the agent execution logs above.")
