from typing import List
from pydantic import BaseModel, Field
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.workflow import Workflow, START, Edge, node
from google.adk.events.event import Event
from google.adk.agents.context import Context

from google.adk.tools import google_search
from app.tools import scrape_article

# Define the structured output schema for the Manufactured Consent Index (MCI)
class ScoreDetail(BaseModel):
    score: int = Field(description="A sub-score between 0 and 100 representing risk.")
    justification: str = Field(description="A 2-3 sentence justification explaining the score based on evidence.")

class ManufacturedConsentIndex(BaseModel):
    overall_score: int = Field(description="The overall Manufactured Consent Index (MCI) score from 0 to 100 (the average of the 4 sub-scores).")
    sponsorship_transparency: ScoreDetail = Field(description="Pillar 1: Sponsorship & Funding Transparency (undisclosed links to state interests or foreign NGOs).")
    narrative_unanimity: ScoreDetail = Field(description="Pillar 2: Narrative Unanimity (exclusion or devaluing of dissenting perspectives).")
    loaded_framing: ScoreDetail = Field(description="Pillar 3: Loaded Framing & Rhetoric (propaganda language and emotional manipulation).")
    source_diversity: ScoreDetail = Field(description="Pillar 4: Source Diversity (reliance on a single official press release or state source).")
    detected_actors: List[str] = Field(description="List of organizations, foreign bodies, state departments, or NGOs suspected of backing or promoting this narrative.")
    propaganda_techniques: List[str] = Field(description="List of specific propaganda techniques detected in the text (e.g. appeal to authority, fear-mongering, loaded words, card stacking).")
    executive_summary: str = Field(description="A clear 1-2 paragraph executive summary explaining the overall findings and campaign attribution.")
    final_verdict: str = Field(description="A clear final statement on whether this article constitutes an attempt at manufactured consent.")

# Define the models
base_model = Gemini(
    model="gemini-2.5-flash",
    retry_options=types.HttpRetryOptions(attempts=3),
)

# 1. Scraper Agent: Grabs URL text or raw input
scraper_agent = Agent(
    name="scraper_agent",
    model=base_model,
    instruction="""You are a data ingestion specialist.
If the input is a URL, call the scrape_article tool to retrieve the title and text content.
If the input is raw text, output it as-is.
Return the clean text content.""",
    tools=[scrape_article],
    output_key="scraped_content"
)

# 2. Translation Agent: Translates non-English texts
translation_agent = Agent(
    name="translation_agent",
    model=base_model,
    instruction="""Translate the following text to English, preserving the original rhetorical framing, emotional tone, metaphors, and key political terms:
{scraped_content}

If the text is already in English, output it exactly as-is.""",
    output_key="translated_content"
)

# 3. Research Agent: Dynamic Google search on entities
research_agent = Agent(
    name="research_agent",
    model=base_model,
    instruction="""Identify key organizations, political figures, think tanks, or corporate interests mentioned in the following text:
{translated_content}

For each entity, use the google_search tool to search for their funding sources, NGO/government affiliations, state backing, and associated controversies (especially in relation to Sri Lanka).
Compile your findings into a comprehensive research brief detailing the potential backers and sponsors.""",
    tools=[google_search],
    output_key="research_brief"
)

# 4. Context Router (Function Node): Resolves target geopolitical/country context
@node(name="context_router")
async def context_router(ctx: Context, research_brief: str, translated_content: str):
    prompt = f"""Analyze the following text and research brief:
Text: {translated_content}
Research Brief: {research_brief}

Determine if this content is related to:
1. Sri Lanka (politics, history, actors, organizations) -> route to "sri_lanka"
2. Russia (politics, history, actors, organizations, Ukraine conflict) -> route to "russia"
3. Other -> route to "generic"

Return a single word matching the route ("sri_lanka", "russia", or "generic") in lowercase. Do not include any other text."""

    response = await base_model.api_client.aio.models.generate_content(
        model=base_model.model,
        contents=prompt,
    )
    result = response.text.strip().lower()
    
    if "sri_lanka" in result or "sri lanka" in result:
        route = "sri_lanka"
    elif "russia" in result:
        route = "russia"
    else:
        route = "generic"
        
    return Event(output=translated_content, route=route)

# 5a. Sri Lankan Context Specialist Agent
sri_lankan_context_specialist_agent = Agent(
    name="sri_lankan_context_specialist",
    model=base_model,
    instruction="""You are a senior geopolitical analyst specializing in Sri Lankan politics, history, media networks, and NGO networks.
Review the following text:
{translated_content}

Alongside the research brief:
{research_brief}

Provide a detailed local context report:
1. Explain how these entities fit into the historical and current political landscape of Sri Lanka.
2. Identify if any of the entities are state-controlled (e.g. state-owned media), partisan campaign groups, or foreign-funded organizations with specific agendas.
3. Call out any subtle language or local narratives that indicate coordinated campaigning or manufactured consent.""",
    output_key="context_analysis"
)

# 5b. Russian Context Specialist Agent
russian_context_specialist_agent = Agent(
    name="russian_context_specialist",
    model=base_model,
    instruction="""You are a senior geopolitical analyst specializing in Russian media networks, state-backed campaigns (such as RT, Sputnik), and Kremlin foreign policy.
Review the following text:
{translated_content}

Alongside the research brief:
{research_brief}

Provide a detailed local context report:
1. Explain how these entities or narratives fit into Russian foreign policy, state-media operations, or information warfare.
2. Identify if any of the entities are Russian state-controlled channels, organizations with Kremlin ties, or proxy networks.
3. Call out any specific rhetorical techniques, framing, or narratives characteristic of Russian active measures or disinformation.""",
    output_key="context_analysis"
)

# 5c. Generic/Global Context Specialist Agent
generic_context_specialist_agent = Agent(
    name="generic_context_specialist",
    model=base_model,
    instruction="""You are a senior media analyst and geopolitical specialist.
Review the following text:
{translated_content}

Alongside the research brief:
{research_brief}

Provide a general context report:
1. Explain how the mentioned entities or narratives fit into their relevant national or international political landscape.
2. Identify if any of the entities are state-controlled, partisan campaign groups, or special interest groups.
3. Call out any subtle language or narratives that indicate coordinated campaigning or manufactured consent in this region or topic.""",
    output_key="context_analysis"
)

# 6. Analysis Agent: Calculates the MCI scorecard and outputs structured JSON
analysis_agent = Agent(
    name="analysis_agent",
    model=base_model,
    instruction="""Perform the final Manufactured Consent Index (MCI) analysis.
You must review:
1. The text content: {translated_content}
2. The research brief: {research_brief}
3. The local context report: {context_analysis}

Compute the overall score and the four sub-scores (each worth 25%):
- Sponsorship & Funding Transparency (25%)
- Narrative Unanimity (25%)
- Loaded Framing & Rhetoric (25%)
- Source Diversity (25%)

Provide detailed justifications for each score, list detected actors, list the propaganda techniques, and generate an executive summary and final verdict. Your final output must strictly follow the output schema.""",
    output_schema=ManufacturedConsentIndex,
    output_key="mci_report"
)

# Multi-Agent Workflow Engine Graph Pipeline
pipeline = Workflow(
    name="ambient_consent_pipeline",
    edges=[
        (START, scraper_agent),
        (scraper_agent, translation_agent),
        (translation_agent, research_agent),
        (research_agent, context_router),
        
        # Geopolitical Context Specialist Routing
        Edge(from_node=context_router, to_node=sri_lankan_context_specialist_agent, route="sri_lanka"),
        Edge(from_node=context_router, to_node=russian_context_specialist_agent, route="russia"),
        Edge(from_node=context_router, to_node=generic_context_specialist_agent, route="generic"),
        
        # Merge back to final analysis
        (sri_lankan_context_specialist_agent, analysis_agent),
        (russian_context_specialist_agent, analysis_agent),
        (generic_context_specialist_agent, analysis_agent),
    ]
)

root_agent = pipeline

# The ADK App wrapper
app = App(
    root_agent=root_agent,
    name="app"
)
