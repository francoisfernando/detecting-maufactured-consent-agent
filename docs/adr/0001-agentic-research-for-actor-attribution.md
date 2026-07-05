# 0001-agentic-research-for-actor-attribution

## Context
Detecting manufactured consent campaigns from well-funded government or non-governmental organizations (NGOs) requires attributing narratives to behind-the-scenes sponsors. Static databases of organizations quickly go out of date, and relying purely on the LLM's pre-trained knowledge limits performance on niche or current local events in Sri Lanka.

## Decision
We will implement an **Agentic Research** pattern for actor attribution. The agent will:
1. Extract organizations, think tanks, and prominent entities from the media artifact.
2. Dynamically use search tools to query the web for funding sources, affiliations, and controversies related to these entities.
3. Feed these search results back into the LLM context to determine if a specific, well-funded Actor is backing the narrative.

## Consequences
- **Pros**: The agent is highly dynamic, works on recent/current events, and bases its decisions on verifiable web evidence rather than LLM hallucinations. This also showcases active tool usage for the Capstone evaluation.
- **Cons**: Increased latency due to search engine queries, and dependency on external search APIs during analysis.
