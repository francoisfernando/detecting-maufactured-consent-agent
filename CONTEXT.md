# Ambient manufactured consent detector

An agentic system designed to detect attempts at manufactured consent in media, focusing on coordinated campaigns propagated by well-funded governmental or non-governmental organizations (NGOs), particularly in regional contexts like Sri Lanka.

## Language

**Manufactured Consent**:
The systematic manipulation of public opinion to align with the interests of powerful sponsors, achieved through coordinated media narratives.
_Avoid_: Simple bias, accidental misreporting

**Campaign**:
A coordinated effort across multiple Media Artifacts, channels, or timeframes to push a specific, non-neutral narrative.
_Avoid_: Individual editorial opinion, isolated articles

**Actor**:
A well-funded organization (governmental department, state-owned enterprise, NGO, or foreign interest group) that initiates or funds a narrative campaign.
_Avoid_: Independent journalists, individual citizens

**Media Artifact**:
A single unit of content analyzed by the system, such as a news article, blog post, social media post, or video transcript.
_Avoid_: Raw metadata, generic web pages

**Translation Agent**:
An ADK sub-agent responsible for translating non-English Media Artifacts (primarily Sinhala and Tamil) into English, preserving rhetorical tone and framing.
_Avoid_: Machine translation without contextual preservation

**Sri Lankan Context Specialist**:
An ADK sub-agent equipped with knowledge of Sri Lankan socio-political structures, local actors, funding patterns, and historical context to evaluate local narrative framing.
_Avoid_: Generic geopolitical agent

