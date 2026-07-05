# 0002-multi-agent-orchestration-and-specialization

## Context
Analyzing local media artifacts in Sri Lanka for manufactured consent requires handling multiple languages (English, Sinhala, Tamil) and possessing deep domain knowledge of the local political, historical, and organizational landscape. Packing all of these tasks into a single LLM prompt creates high cognitive load, increases hallucinations, and dilutes focus.

## Decision
We will construct a multi-agent system utilizing the **Google Agent Development Kit (ADK)**. The system will consist of five specialized agents:
1. **Coordinator Agent (Root)**: Manages the workflow, routes inputs, and aggregates the final evaluation report.
2. **Translation Agent**: Detects language and translates Sinhala/Tamil text into English while preserving the original rhetorical framing and emotional tone.
3. **Research Agent**: Scrapes the input text/URLs and queries the web dynamically to research the funding and affiliations of extracted entities.
4. **Sri Lankan Context Specialist**: Validates the extracted actors and narratives against historical Sri Lankan political history, known state/NGO funding patterns, and local interests.
5. **Analysis Agent**: Performs the final narrative analysis, maps propaganda techniques, and computes the Manufactured Consent Index (MCI) score.

## Consequences
- **Pros**: Clean separation of concerns. The translation and local context analysis are handled by specialized roles, increasing accuracy and preventing context clutter.
- **Cons**: Multiple LLM invocations, increasing latency and API cost.
