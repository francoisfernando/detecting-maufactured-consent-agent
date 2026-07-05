# 0003-manufactured-consent-index-scoring-rubric

## Context
Evaluating manufactured consent in media requires a transparent, standardized, and quantifiable metric to judge the degree of influence and coordination in media artifacts. This scorecard needs to be human-readable and displayable in the Streamlit dashboard.

## Decision
We will define the **Manufactured Consent Index (MCI)**, a score from 0 to 100 calculated as the average of four weighted sub-scores (each worth 25%):
1. **Sponsorship & Funding Transparency (25%)**: Extent of undisclosed links to well-funded governmental entities or NGOs.
2. **Narrative Unanimity (25%)**: The exclusion or devaluing of dissenting perspectives.
3. **Loaded Framing & Rhetoric (25%)**: Use of manipulative language, propaganda, or logical fallacies.
4. **Source Diversity (25%)**: Reliance on a single state/NGO press release or official source.

The Streamlit UI will display this index prominently using metric cards, progress bars, or radar charts, alongside a detailed justification block explaining the score for each sub-metric to maintain transparency.

## Consequences
- **Pros**: Clear, visual, and granular feedback. Users and competition judges can easily verify *why* an article received a specific rating.
- **Cons**: Sub-scores are calculated via LLM reasoning which, although guided by strict criteria, carries some subjective variability.
