# Proposal: Redevelopment of Iterativ-Agent as a KNOWLEDGE II Agent

**Document Version:** 1.0  
**Date:** May 21, 2026  
**Author:** Linda Futwa  
**Status:** Draft for Review

---

## Executive Summary

This proposal outlines the strategic redevelopment of **iterativ-agent** into a **KNOWLEDGE II agent**—a next-generation agentic system that transcends traditional tool-calling architectures to become a **knowledge-centric intelligence platform**. By integrating the Iterativ Knowledge System (IKS) theoretical framework, this transformation will position iterativ-agent as the first production-ready agent capable of:

- **Domain-aware reasoning** through structured knowledge genealogy and traceability
- **Knowledge-optimized LLM performance** via domain-specific context compression
- **Autonomous knowledge synthesis** across multi-domain problem spaces
- **Misinformation resistance** through provenance tracking and epistemological validation
- **Self-improving knowledge graphs** that evolve with usage patterns

This redevelopment represents not merely a feature enhancement but a **fundamental paradigm shift** from agentic tool orchestration to **knowledge-mediated intelligence**.

---

## Strategic Rationale

### Current State Assessment (Hermes / Iterativ Agent)

Iterativ-agent today is functionally equivalent to the open-source **Hermes Agent** from Nous Research, sharing architecture and philosophy: a self-improving AI agent with five core pillars — Memory, Skills, Soul (user model), Crons (automations), and Self (learning loop) [cite:2][web:5][web:8]. It already delivers:

- Curated long-term memory with FTS5-backed search across sessions.
- Auto-generated skills produced from successful task trajectories.
- Honcho-based dialectic user modeling ("Soul").
- Scheduled automations and subagent delegation for parallel work.
- Multi-backend execution across local, Docker, SSH, Modal, Daytona, and more.

These are **KNOWLEDGE I** strengths: powerful behavior, strong ergonomics, and practical self-improvement — but with largely **implicit knowledge structures**.

### Knowledge II as an Extension, Not a Replacement

The Knowledge II redevelopment is deliberately framed as a **layered extension of Hermes/Iterativ**, not a greenfield rewrite. The goal is to keep the proven Hermes pillars and user experience while introducing a **formal knowledge substrate** underneath:

- Preserve: Memory, Skills, Soul, Crons, Self as the outer behavioral shell.
- Add: A knowledge graph, domain modules, epistemic validation, and synthesis as the inner knowledge engine.

In effect, **Hermes remains the way the agent behaves; Knowledge II becomes how it knows and trusts what it knows.**

### Combined Opportunity (Best of Both)

By fusing Hermes and Knowledge II, Iterativ can offer:

1. **Agentic UX + Epistemic Rigor**  
   Hermes already feels like a practical, everyday agent. Knowledge II adds explicit provenance, contradiction detection, and domain-aware reasoning without breaking that UX.

2. **Skills as Knowledge Transforms**  
   Existing auto-skills continue to be created and used, but now declare the knowledge they require and produce, integrating directly into the knowledge graph.

3. **Knowledge-Aware Automations**  
   Crons can be triggered not only by time but by knowledge change ("run this when new claims land in domain X"), enabling highly targeted, event-driven workflows.

4. **Metric-Driven Self-Improvement**  
   The Self loop gains epistemic metrics (claim stability, source diversity, impact on downstream skills), turning vague "learning" into measurable knowledge improvement.

This combined approach allows Iterativ to differentiate as **the Hermes-class agent with Knowledge II-grade epistemology**, rather than choosing between ergonomics and rigor.
---

## Technical Architecture

### Design Principle: Hermes Pillars + Knowledge II Substrate

The architecture preserves all five Hermes pillars as the **outer behavioral shell** and introduces Knowledge II as a **formal knowledge substrate** underneath each. No pillar is removed — each is extended by a corresponding Knowledge II component.

```
┌─────────────────────────────────────────────────────────────┐
│                  HERMES BEHAVIORAL SHELL                     │
│   Memory │ Skills │ Soul (User Model) │ Crons │ Self (Loop)  │
└────────────────────────┬────────────────────────────────────┘
                         │ extends via
┌────────────────────────▼────────────────────────────────────┐
│               KNOWLEDGE II SUBSTRATE                         │
│  Knowledge   │  Domain    │  Epistemic  │  Synthesis  │      │
│  Graph       │  Modules   │  Validator  │  Engine     │ API  │
└─────────────────────────────────────────────────────────────┘
                         │ persists to
┌────────────────────────▼────────────────────────────────────┐
│                  STORAGE LAYER                               │
│   SQLite/FTS5 (session logs) │ Graph DB (knowledge nodes)    │
│   MEMORY.md (human summary)  │ skills/ (knowledge-anchored)  │
└─────────────────────────────────────────────────────────────┘
```

---

### Core Components

#### 1. Knowledge Graph Engine
**Extends Hermes Pillar: Memory**

Hermes' current memory writes to SQLite/FTS5 and maintains MEMORY.md as a human-readable summary. Knowledge II adds a **parallel knowledge graph store** — every memory write now dual-writes:
- **To MEMORY.md** (unchanged UX, unchanged FTS5 search)
- **To the graph** as structured `Claim`, `Concept`, `Source`, and `Domain` nodes with provenance edges

**Graph Schema:**
```
Node types:  Claim | Concept | Domain | Source | Skill | User
Edge types:  derives_from | supports | contradicts | synthesizes
             domain_of | used_in | about_user | produced_by
```

**Storage backend options (by deployment scale):**

| Scale | Backend | Notes |
|-------|---------|-------|
| Local / single user | SQLite (graph extension) | Zero additional infra, file-based |
| Team / cloud | ArangoDB | Multi-model: graph + document in one |
| Enterprise | Neo4j | Best graph query performance at scale |

**New capabilities unlocked:**
- Cross-session knowledge lineage queries ("When did my understanding of X change, and why?")
- Temporal versioning of claims — old beliefs preserved, never silently overwritten
- Graph traversal augmenting FTS5 search for richer context retrieval

---

#### 2. Domain Knowledge Modules
**Extends Hermes Pillar: Skills**

Hermes skills are procedural documents auto-generated from task trajectories. Domain Modules are the **knowledge complement** to skills — pre-structured ontologies that tell the agent *what it already knows* about a domain before a task begins, compressing LLM context and improving reasoning accuracy.

**Module structure:**
```
domain_modules/
├── core/             # mathematics, logic, language, computation
├── applied/          # finance, law, medicine, software-architecture
├── iterativ/         # IKS theory, succession planning, financial architecture
└── user/             # LG-specific knowledge spaces (auto-populated from graph)
```

**Each module is a JSON-LD file declaring:**
- Canonical concepts and their definitions
- Known relationships between concepts
- Trusted sources for this domain
- Linked skills that operate in this domain

**Integration with Skills:**
- Skills gain a `knowledge_signature` block:
```yaml
# skill: weekly-architecture-review.md
knowledge_signature:
  requires_domains: [iterativ.iks, software.architecture]
  requires_claims:  ["current repo structure", "recent design decisions"]
  produces_claims:  ["architecture health assessment", "refactoring candidates"]
```
- At runtime, the agent checks the graph for claim sufficiency before the skill executes — if insufficient, it runs an **acquire-context** sub-routine first.

---

#### 3. Epistemological Validation Layer
**Extends Hermes Pillar: Soul (User Model)**

Hermes' Soul tracks user preferences, goals, and personality via Honcho. The Epistemic Validator extends this to the **truth dimension** of the user model: not just *who LG is*, but *what we know and how well we know it*.

**Validation pipeline (runs on every knowledge write):**

```
New knowledge claim
       │
       ▼
[1] Source credibility score   — is the source reliable?
       │
       ▼
[2] Consistency check          — does this contradict existing graph nodes?
       │
       ▼
[3] Temporal validity          — is this claim time-sensitive / expiring?
       │
       ▼
[4] Corroboration check        — do ≥2 independent sources agree?
       │
       ▼
[5] User-model alignment       — is this consistent with Soul/Honcho context?
       │
  ┌────┴────┐
  │ PASS    │  → Integrate into graph with confidence score
  │ WARN    │  → Integrate with warning flag; surface in next report
  │ BLOCK   │  → Reject; log contradiction; prompt user to resolve
  └─────────┘
```

**Two operating modes:**
- **Soft mode** (default): All writes succeed; warnings surfaced in daily/weekly reports
- **Hard mode** (opt-in per domain): Blocked writes on critical domains (finance, legal, infra automation); requires explicit user confirmation to override

**Anti-misinformation outputs:**
- Provenance chain view per claim (which tools, sources, and runs produced it)
- Contradiction digest in synthesis reports
- Confidence intervals on synthesized knowledge

---

#### 4. Knowledge-Mediated Tool & Skill Execution
**Extends Hermes Pillar: Crons (Automations)**

Hermes crons are time-scheduled automations. Knowledge II adds a **second trigger class**: knowledge-change events. Crons can now also be declared as:

```yaml
# cron: succession-plan-review.yaml
trigger:
  type: knowledge_change
  domains: [iterativ.succession, finance.estate]
  min_new_claims: 5
delivery: telegram
skill: succession-plan-review
```

**Tool execution gains three Knowledge II hooks:**

```python
# KNOWLEDGE II tool execution lifecycle

# 1. PRE-EXECUTION: knowledge sufficiency check
context = graph.get_relevant_knowledge(task, domains=skill.requires_domains)
if context.sufficiency_score < threshold:
    context = await acquire_missing_knowledge(skill.requires_claims)

# 2. EXECUTION: tool runs with enriched context
result = tool.execute(params, knowledge_context=context)

# 3. POST-EXECUTION: extract and integrate new knowledge
new_claims = extract_claims(result, provenance={
    "tool": tool.id, "skill": skill.id,
    "run_id": run.id, "timestamp": now()
})
graph.integrate(new_claims, validator=epistemic_validator)
```

**For existing Hermes crons:** no change required unless opted into Hard mode.

---

#### 5. Autonomous Knowledge Synthesis Engine
**Extends Hermes Pillar: Self (Learning Loop)**

Hermes' Self loop evaluates completed tasks and decides whether to create/update skills or memory. The Synthesis Engine extends this with **epistemic introspection** — the agent now also asks "what do I know, how well do I know it, and what can I derive from it?"

**Three synthesis jobs run on a configurable schedule:**

| Job | Frequency | Output |
|-----|-----------|--------|
| Contradiction Scan | Daily | List of conflicting claims + resolution prompts |
| Cross-Domain Pattern Mining | Weekly | Analogies, gaps, and novel hypothesis candidates |
| Skill Impact Audit | Weekly | Which skills are expanding the graph vs. adding noise |

**Skill Impact Metrics (replaces binary skill-exists/doesn't-exist):**
- **Claim stability:** How often do this skill's outputs get contradicted or revised?
- **Source diversity:** Average number of independent sources backing each produced claim
- **Downstream impact:** How many other skills depend on knowledge this skill produces

**Synthesis report output (natural language + structured):**
```
Weekly Knowledge Synthesis — May 26, 2026

📊 Graph Health
   Total claims: 14,821  |  Flagged: 47  |  Contradictions: 3 (unresolved)

🔗 Cross-Domain Insights
   Pattern: IKS genealogy model ↔ succession planning transfer structures
   Hypothesis: "Knowledge inheritance" may formalize estate knowledge transfer
   Confidence: Medium — 2 supporting sources, 0 contradictions

⚙️  Skill Recommendations
   Create: "iks-succession-knowledge-mapper" (pattern seen 4× in last 2 weeks)
   Review: "legal-template-generator" (low source diversity, 3 contradictions)
```

---

### Revised Directory Structure

Minimal additions to the existing iterativ-agent repo:

```
iterative-agent/
├── knowledge/                  ← NEW Knowledge II substrate
│   ├── graph/                  # Graph DB adapter (SQLite / ArangoDB / Neo4j)
│   ├── domain_modules/         # JSON-LD domain ontologies
│   │   ├── core/
│   │   ├── applied/
│   │   ├── iterativ/           # IKS-specific domains
│   │   └── user/               # Auto-populated from graph
│   ├── validator.py            # Epistemological validation pipeline
│   ├── synthesis.py            # Synthesis engine and scheduled jobs
│   └── schema.py               # Node/edge type definitions
├── skills/                     ← EXTENDED with knowledge_signature blocks
├── agent/                      ← EXTENDED with knowledge hooks in tool lifecycle
├── cron/                       ← EXTENDED with knowledge_change trigger type
└── iterativ_state.py           ← EXTENDED with graph state management
```

**What is NOT changed:** CLI, TUI, gateway (Telegram/Discord/Slack), providers, MCP server, Docker/Modal/Daytona backends, ACP adapter, web UI, or any existing skill files. Knowledge II is purely additive until Hard mode is opted into.

---

## Migration Roadmap

### Phase 1: Foundation (Months 1-3)

**Objectives:**
- Deploy knowledge graph infrastructure alongside existing SQLite storage
- Implement basic knowledge node types and relationships
- Develop domain module specification and core domain library

**Deliverables:**
- Neo4j/ArangoDB integration with read/write APIs
- Core domain modules: mathematics, logic, programming, general_knowledge
- Knowledge graph visualization dashboard
- Migration of existing session memory to knowledge nodes

**Success Metrics:**
- 100% of historical conversations mapped to knowledge graph
- <50ms query latency for knowledge retrieval
- Domain module coverage for 80% of typical user queries

### Phase 2: Intelligence Enhancement (Months 4-6)

**Objectives:**
- Implement epistemological validation layer
- Enhance tool execution with knowledge-mediated workflows
- Deploy autonomous knowledge synthesis engine

**Deliverables:**
- Provenance tracking for all knowledge claims
- Source credibility scoring system
- Knowledge-aware tool selection algorithm
- Weekly synthesis report generation

**Success Metrics:**
- 95% accuracy in misinformation flagging (validated against benchmark datasets)
- 30% reduction in tool execution failures due to context insufficiency
- Generation of ≥3 actionable synthesis insights per week for active users

### Phase 3: Advanced Capabilities (Months 7-9)

**Objectives:**
- Cross-domain analogy and hypothesis generation
- User-customizable domain ontologies
- Knowledge graph sharing and collaboration features

**Deliverables:**
- Analogy engine for cross-domain pattern matching
- Domain ontology editor UI
- Knowledge graph export/import (JSON-LD format)
- Multi-user knowledge graph collaboration (for teams)

**Success Metrics:**
- User-reported usefulness of cross-domain analogies (>70% positive feedback)
- ≥100 community-contributed domain modules
- <5 minutes to export/import complete knowledge graph

### Phase 4: Ecosystem Integration (Months 10-12)

**Objectives:**
- Public Knowledge II API for third-party integrations
- Integration with agentskills.io standard for knowledge-aware skills
- Multi-agent knowledge graph federation

**Deliverables:**
- RESTful/GraphQL API for knowledge graph operations
- SDK for Python, JavaScript, TypeScript
- Federation protocol for multi-agent knowledge sharing
- Documentation and developer onboarding resources

**Success Metrics:**
- ≥10 third-party integrations within 3 months of API launch
- 1,000+ API calls per day from external systems
- Federation protocol adopted by ≥3 independent agent projects

---

## Competitive Differentiation

### Market Position

**Current Landscape:**
- **LangChain/AutoGPT:** Tool orchestration without epistemological grounding
- **Semantic Scholar/Connected Papers:** Static knowledge graphs, no agentic intelligence
- **Notion AI/Obsidian:** Document-centric, lacks formal knowledge structures

**Knowledge II Advantage:**
- Only agent architecture with **native epistemological reasoning**
- First system enabling **provenance-tracked knowledge synthesis**
- Unique capability for **domain-aware LLM optimization**

### Patent and IP Strategy

**Potential Patentable Components:**
1. Knowledge-mediated tool execution framework
2. Cross-domain analogy generation via graph topology analysis
3. Epistemological validation scoring algorithm
4. Multi-agent knowledge graph federation protocol

**Open Source Strategy:**
- Core graph engine: Open source (Apache 2.0)
- Advanced synthesis algorithms: Dual-license (AGPL/Commercial)
- Domain modules: Community-contributed (Creative Commons)
- Enterprise features: Proprietary (collaboration, federation, advanced security)

---

## Business Model Implications

### Revenue Streams

1. **Freemium SaaS**  
   - Free tier: Personal use, basic knowledge graph (10K nodes)
   - Pro tier ($29/month): Unlimited nodes, advanced synthesis, custom domains
   - Team tier ($99/user/month): Collaboration, federation, API access
   - Enterprise tier (Custom): On-premise deployment, SLA, dedicated support

2. **API Monetization**  
   - Knowledge graph queries: $0.001 per query
   - Domain module access: $0.01 per module load
   - Synthesis operations: $0.10 per synthesis run

3. **Domain Module Marketplace**  
   - Community creators sell specialized domain ontologies
   - Iterativ takes 30% platform fee
   - Certified premium domains (legal, medical, financial) at higher price points

4. **Consulting and Custom Development**  
   - Enterprise domain ontology development: $50K-$500K projects
   - Integration services for existing knowledge management systems
   - Training and certification programs for Knowledge II practitioners

### Market Opportunity

**Total Addressable Market (TAM):**
- Knowledge management software: $12.5B (2026)
- AI agent platforms: $8.2B (2026)
- **Knowledge II segment:** ~$2B (estimated 10% of combined markets seeking epistemological rigor)

**Serviceable Addressable Market (SAM):**
- Technical professionals requiring provenance-tracked knowledge: ~500K users
- Organizations with misinformation risk (media, research, finance): ~25K enterprises
- **SAM revenue potential:** $1.5B annually

**Serviceable Obtainable Market (SOM - Year 3):**
- Conservative capture: 2% of SAM
- **Projected revenue:** $30M annually by Year 3

---

## Risk Analysis and Mitigation

### Technical Risks

**Risk 1: Knowledge Graph Performance Degradation**  
- **Probability:** Medium  
- **Impact:** High  
- **Mitigation:** Implement graph partitioning, caching layers, and query optimization from Phase 1; benchmark against 100M+ node graphs

**Risk 2: Domain Ontology Quality Variability**  
- **Probability:** High  
- **Impact:** Medium  
- **Mitigation:** Establish certification process for premium domains; community voting on module quality; automated consistency validation

**Risk 3: LLM Hallucination in Knowledge Extraction**  
- **Probability:** High  
- **Impact:** High  
- **Mitigation:** Multi-pass extraction with consistency checking; human-in-the-loop validation for critical domains; confidence scoring on all extracted knowledge

### Market Risks

**Risk 4: Slow User Adoption of Knowledge II Paradigm**  
- **Probability:** Medium  
- **Impact:** High  
- **Mitigation:** Maintain backward compatibility with KNOWLEDGE I workflows; gradual opt-in rollout; extensive educational content and onboarding

**Risk 5: Competitive Response from Incumbents**  
- **Probability:** Medium  
- **Impact:** Medium  
- **Mitigation:** Accelerate patent filings; build community moat via open domain module ecosystem; focus on enterprise niches (legal, medical) with high switching costs

### Strategic Risks

**Risk 6: Resource Constraints for 12-Month Development**  
- **Probability:** High  
- **Impact:** High  
- **Mitigation:** Phased rollout allows revenue generation by Phase 2; seek strategic partnerships for domain ontology development; leverage community contributions

**Risk 7: Epistemological Framework Validation**  
- **Probability:** Low  
- **Impact:** Critical  
- **Mitigation:** Engage academic advisors in knowledge representation and epistemology; publish research papers validating approach; establish advisory board with domain experts

---

## Success Criteria

### Quantitative Metrics (12 Months Post-Launch)

- **User Growth:** 10,000 active users (50% on paid tiers)
- **Knowledge Graph Scale:** 100M+ nodes across all users
- **Domain Module Ecosystem:** 500+ community-contributed modules
- **Revenue:** $500K ARR by end of Phase 3
- **API Adoption:** 25+ third-party integrations
- **Synthesis Accuracy:** >80% user-reported relevance on generated insights

### Qualitative Metrics

- **Market Recognition:** Featured in ≥3 major AI/tech publications
- **Academic Validation:** ≥2 peer-reviewed papers citing IKS framework
- **Community Health:** Active Discord community with >1,000 members
- **Enterprise Interest:** ≥10 enterprise pilot programs initiated
- **Developer Ecosystem:** ≥50 community code contributors

---

## Resource Requirements

### Team Composition

**Phase 1-2 (Months 1-6):**
- 1 Lead Architect (full-time) - Knowledge graph systems
- 2 Backend Engineers (full-time) - Graph DB, API development
- 1 Domain Ontology Specialist (full-time) - Core domain module creation
- 1 ML/NLP Engineer (part-time) - Knowledge extraction and synthesis
- 1 Technical Writer (part-time) - Documentation and educational content

**Phase 3-4 (Months 7-12):**
- Add 1 Frontend Engineer (full-time) - Knowledge graph visualization, UI
- Add 1 DevOps Engineer (full-time) - Federation infrastructure, scaling
- Add 1 Product Manager (full-time) - Ecosystem development, partnerships
- Existing team continues

**Total Team by Month 12:** 8 full-time, 2 part-time

### Budget Estimate

**Development Costs (12 months):**
- Salaries and contractors: $1.8M
- Infrastructure (graph DB hosting, compute): $150K
- Software licenses and tools: $50K
- **Total Development:** $2M

**Go-to-Market Costs:**
- Marketing and content creation: $200K
- Conference sponsorships and speaking: $50K
- Community building (events, swag): $30K
- **Total GTM:** $280K

**Contingency (15%):** $342K

**Total Budget:** $2.622M

### Funding Strategy

**Option 1: Bootstrap with Phased Revenue**
- Launch freemium by Phase 2 (Month 6)
- Reinvest early revenue into Phase 3-4 development
- Slower growth, full equity retention

**Option 2: Seed Round ($2.5M)**
- Accelerated hiring and development
- Aggressive marketing and ecosystem building
- Dilution: ~15-20% equity

**Option 3: Strategic Partnership**
- Co-development with enterprise partner (e.g., legal tech, research institution)
- Partner provides domain expertise and initial customer base
- Revenue sharing or equity stake

**Recommendation:** Pursue **Option 3** for Phase 1, transition to **Option 2** for Phase 2-4 based on validated traction.

---

## Next Steps

### Immediate Actions (Weeks 1-4)

1. **Stakeholder Review**  
   - Present proposal to key stakeholders and advisors
   - Gather feedback on technical approach and business model
   - Refine roadmap based on input

2. **Technical Proof of Concept**  
   - Build minimal knowledge graph integration with existing iterativ-agent
   - Demonstrate single-domain knowledge-mediated tool execution
   - Validate performance assumptions with 10K+ node graph

3. **Partnership Exploration**  
   - Identify 5-10 potential strategic partners (research institutions, legal tech, medical informatics)
   - Initiate conversations with domain ontology experts
   - Explore co-development opportunities

4. **Team Planning**  
   - Draft job descriptions for Phase 1 roles
   - Identify potential candidates or contractors
   - Establish hiring timeline

### Decision Point (Week 5)

**Go/No-Go Criteria:**
- PoC demonstrates <100ms knowledge graph query latency
- ≥2 potential strategic partners express serious interest
- Team recruitment pipeline shows feasibility of Phase 1 hiring
- Stakeholder consensus on strategic direction

**If GO:** Initiate Phase 1 development, finalize partnership negotiations, begin hiring

**If NO-GO:** Revisit technical approach, explore alternative business models, consider staged/experimental rollout

---

## Conclusion

The redevelopment of iterativ-agent as a **KNOWLEDGE II agent** represents a transformative opportunity to pioneer the next generation of epistemologically-grounded AI systems. By moving beyond reactive tool orchestration to knowledge-mediated intelligence, we position Iterativ at the forefront of trustworthy AI, misinformation resistance, and cross-domain synthesis.

This proposal outlines a pragmatic 12-month roadmap with clear milestones, measurable success criteria, and realistic resource requirements. The phased approach allows for course correction, revenue validation, and community building while maintaining technical rigor.

**The core question is not whether Knowledge II represents the future—it does—but whether Iterativ will lead that future or follow others into it.**

I recommend proceeding with the immediate next steps outlined above, targeting a decision point in 4 weeks to formally commit to Phase 1 development.

---

**Appendices**

**Appendix A:** Detailed technical specifications for knowledge graph schema  
**Appendix B:** Sample domain module structure (JSON-LD)  
**Appendix C:** Competitive analysis matrix  
**Appendix D:** Financial projections (3-year detailed model)  
**Appendix E:** Academic references for IKS theoretical framework  

**Document Status:** Draft for stakeholder review  
**Next Review Date:** May 28, 2026  
**Approval Required From:** Founding Team, Technical Advisory Board, Potential Strategic Partners

---

*This proposal is confidential and intended solely for stakeholders of Iterativ (Pty) Ltd. Unauthorized distribution is prohibited.*