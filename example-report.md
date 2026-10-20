# Should a solo founder write their product's documentation before writing the code?

_A structured debate between two AI models, with independent research, a bookkeeping referee, and a numbered reference list._

| | |
|---|---|
| Date | 2026-10-20 |
| Claude | sonnet (effort: low) |
| Codex | gpt-6.1-sol (effort: low) |
| Referee | claude haiku (effort: low) |
| Rounds | 2 after opening positions |
| Ended because | Reached the round cap (2). |
| Claims | 3 agree to disagree, 10 agreed, 1 conceded |

## Executive summary

**Question:** Should a solo founder write product documentation before writing code?

**Bottom line:** Neither debater located a controlled or observational study comparing documentation-first with code-first outcomes for solo founders (K1). Both agree that comprehensive documentation written before any code is not supported by the available evidence as a rule (K13). The remaining disagreement concerns a short default artifact and how experiments should be governed, not full documentation.

**Agreed points.** The most-cited pro-documentation sources ask for less than is often assumed. Preston-Werner's README-first essay limits advance writing to one introductory README (K2). Amazon's PR/FAQ is about one page plus an FAQ, followed by customer testing, measurement and iteration, so Amazon's account cannot isolate the effect of writing first (K2, K7). The Agile Manifesto ranks working software above comprehensive documentation as a priority, not a time order (K9). Much of README-first's value depends on team coordination, which does not apply to a solo founder; early-user review and later reference remain legitimate but unmeasured uses (K3). Private prose cannot validate demand, and customer contact or prototypes address the dominant risk (K4). A written description cannot establish whether an untested implementation meets a numerical latency requirement (K10). Paper prototypes can gather interaction evidence before production code exists (K11).

**Where they differ.** Claude recommends a short written description of intended behaviour before building, unless a cheaper experiment answers the question, treated as a forcing function for design choices rather than a gate (K12). Codex recommends recording the uncertainty, observable outcome, decision threshold and effort budget first, then choosing the artifact or experiment, without requiring a product description (K12). Both now accept a precommitted effort budget but differ on the anchor: Claude ties it to the cost of the cheapest falsifying experiment; Codex sets it per task with no universal cap (K14). Claude holds, as a mechanism-based hypothesis, that documentation-first helps most where the text is the interface such as APIs or libraries; Codex finds no outcome evidence for that ranking (K5).

**Caveats.** All positions rest on practitioner essays, company material, and mechanism arguments. Claimed prevalence of demand versus feasibility failure among solo founders is unsourced and is not needed for the narrow claims endorsed here.


## Points of agreement

### K1. No controlled or observational study comparing documentation-first with code-first outcomes for solo founders has been located by either debater.

Both debaters searched and found none. The wording must be 'none located', not 'none exists', because the search was not exhaustive. Practitioner essays and company self-reports are the only material.

### K2. Preston-Werner's README-first essay and Amazon's PR/FAQ call for one short advance artifact, not comprehensive documentation.

Preston-Werner explicitly restricts advance documentation to one introductory README [1]. Amazon's PR/FAQ is about one page plus FAQ, followed by customer testing ([2]; [11]).

Sources: [1]

### K4. Private prose cannot validate demand; a written offer shown to real customers gives weak behavioural signals short of purchase, and customer contact is what matters.

Both now agree that customer behaviour toward a written offer is weak evidence short of purchase. The unsourced dominant-risk base rate was dropped by both. Residual definitional point: whether a landing page counts as documentation.

Sources: [18]

### K6. No independent evidence located measures solo-founder outcomes from spec-first or spec-driven AI coding workflows; existing studies use other populations and proxy outcomes.

Both revised. Claude dropped the 'vendor-sourced' label after Codex noted ESEM 2026 and an arXiv preprint exist. Those studies examine specification artifacts and framework proxies, not solo-founder sequencing. No URLs for these studies appear in the ledger, so they are not cited here.

Sources: [20], [21]

### K7. Amazon's Working Backwards bundles advance writing with customer testing, measurement and iteration, so its account cannot isolate the causal effect of writing first.

Agreed. Attributing outcomes to document order exceeds the evidence [11].

### K8. Camuffo et al.'s four randomized trials (759 firms) test scientific decision-making and hypothesis testing, not documentation-first versus code-first sequencing.

Agreed. The study is relevant to explicit hypothesis testing [12] but cannot establish a documentation sequencing effect.

### K9. The Agile Manifesto does not prescribe whether documentation or code is written first; its ranking is a priority, not a temporal order.

Agreed. A priority ranking is satisfied by either README-first or prototype-first sequencing [3].

### K10. A written description of intended behaviour alone cannot establish whether an untested implementation meets a numerical latency requirement; performance evidence needs an implementation or representative experiment.

Agreed as a narrow exception. Claude's request for data on how often feasibility failures cause solo-founder failure is unsourced and not needed for this claim.

### K11. Paper prototypes can collect user interaction evidence before production code exists.

Agreed. Inexpensive interactive representations are an alternative to both extensive writing and production code [15].

### K13. Comprehensive documentation written before any code is not supported by the available evidence as a rule for solo founders.

Agreed by both. This is the strongest point of consensus and is well supported by the absence of contrary evidence and the Preston-Werner and Amazon sources.


## Points conceded during the debate

### K3. README-first's team-coordination benefit does not apply to a solo founder; reader benefits for early users and the future self remain but are unmeasured and do not show the README must precede the first experiment.

- **Claude:** Accepted Codex's revision: the coordination benefit is lost; reader benefits (early users, future self) exist but nothing shows they require the README to precede the first experiment. Withdrew the AI-agent-reader claim.
- **Codex:** Revised: coordination benefit lost; early-user review and later reference are legitimate, unmeasured uses; these do not establish that the README must precede the first experiment.
Codex's revision was accepted by Claude. The residual question, whether advance descriptions improve outcomes when they precede the first experiment, is untested.

Sources: [1]


## Agreed to disagree

### K5. Documentation-first is most plausibly strongest where the text is the interface (APIs, CLIs, libraries), but no comparative outcome evidence exists.

- **Claude:** Maintained as a mechanism-based hypothesis: contract review of an API spec is possible before implementation; paper prototypes answer interaction questions prose cannot.
- **Codex:** Written contracts permit interface review without implementation, but no evidence establishes that documentation-first yields greater benefit for API products than visual ones.
- **Crux:** No comparative outcome evidence across product categories exists; the ranking rests on interpretation of design practice, not measured outcomes.
Claude holds this as a mechanism-based hypothesis: contracts can be reviewed before implementation [17]. Codex accepts the mechanism but finds no evidence that the benefit is greater than for visual products. Left unresolved.

### K12. The default for a solo founder is a short, testable product description written before building, but not a mandatory gate before experiments that can answer a question the description cannot.

- **Claude:** Before building, record uncertainty, threshold and budget; also write a short description of intended behaviour unless a cheaper experiment answers the question. Describes the choice as a value judgment with no evidence either way.
- **Codex:** Before the next deliberate experiment, record uncertainty, observable outcome, decision threshold and effort budget, then select the artifact or experiment without requiring a prior product description. Describes this as unsourced procedural judgment.
- **Crux:** Value and procedure judgment: whether the default includes a short written behavioural description of the product (Claude, which forces design choices) or only a decision-criterion test plan with an effort budget (Codex). Both agree no mandatory documentation gate exists; neither side has evidence settling the choice.
Both agree there is no mandatory documentation gate. They disagree on whether the default includes a short behavioural description (Claude, to force design choices) or only a decision-criterion test plan with an effort budget (Codex). Neither has evidence settling the choice; this is a values and procedure dispute.

### K14. A short-description-first rule is only useful with a precommitted effort budget, but the budget's anchor is disputed.

- **Claude:** Revised: the writing budget should not exceed the cost of the cheapest experiment that could test the same hypothesis; one day is a rough default only. Accepts that a fixed cap is not tied to the decision.
- **Codex:** Revised: a precommitted effort budget and reassessment at the budget or a specified observation; violations are observable (missing criteria, overrun without reassessment, retroactive threshold change). Neither effectiveness nor a universal one-day cap is established.
- **Crux:** Value judgment: whether the budget should be anchored to the cost of the cheapest falsifying experiment (Claude) or set per task in advance with no universal cap (Codex). Both now accept that a precommitted budget is required; the remaining difference is the anchor and whether a one-day default is offered.
Both accept that a precommitted budget is needed. Claude now ties the cap to the cost of the cheapest experiment testing the same hypothesis (one day only a rough default). Codex prefers per-task budgets with explicit reassessment and rejects a universal one-day cap. Neither effectiveness nor a universal cap is established.

## Strongest case for

The strongest case for writing first, as argued in the debate, is that a short written description of intended behaviour forces design decisions before code is built. Claude argues that writing exposes scope and interface choices early, that the text can be shown to early users, and that it serves the founder's future self. Preston-Werner's README-first essay and API contract practice are the main sources cited. The case is a plausible mechanism, not a measured outcome.

## Strongest case against

The strongest case against comprehensive documentation first, and against any mandatory documentation gate, is that the evidence reviewed does not establish any sequencing advantage for solo founders. Team-coordination benefits vanish for a solo founder. Prose cannot validate demand; customer contact and prototypes address that risk. Basecamp's objection to detailed specifications written before implementation, and the Agile Manifesto's priority of working software, point toward learning through building. Experiments can answer questions a description cannot, such as performance and interaction. Both debaters reject comprehensive documentation first.

## Guidance for the author

Do not write that research shows documentation-first fails or succeeds. Write "none located by either debater" for the comparative-study claim. Quote Preston-Werner and Amazon accurately: both ask for one short artifact, and Amazon's process bundles writing with customer testing. Present the disagreement as one of procedure and value: Claude's short behavioural description versus Codex's precommitted test plan with effort budget. Label the budget anchor (cheapest falsifying experiment versus per-task budget) as unresolved. Mark the interface-versus-visual ranking as a hypothesis. Avoid unsourced base rates for demand versus feasibility failure. Cite the spec-driven AI studies only after retrieving their URLs and checking them directly.

## Caveats

- No live searches were run this debate; the evidence base is the ledger and the sources named in the transcript.
- No controlled or observational study comparing documentation-first with code-first outcomes for solo founders was located by either debater; this is 'none located', not 'none exists'.
- Spec-driven AI coding research (ESEM 2026 and an arXiv preprint) was referenced without URLs in the ledger; those sources were not verified here.
- Claims about the prevalence of demand failure versus feasibility failure among solo founders are unsourced.
- The Camuffo et al. study concerns hypothesis testing in firms, not documentation sequencing, and should not be read as evidence for either position.
- Claude's briefing listed sources beyond those in the ledger (for example Parnas and Clements, Royce 1970, Getting Real, Paul Graham). Those were not verified against the ledger and are not relied on for verdicts.

## Closing statements

### Claude

**Final position.** A solo founder should not write comprehensive documentation before writing code. We agree on this (K13), and the evidence supports it. The sources usually cited for writing first do not say otherwise. Preston-Werner's README-first essay asks for one introductory README. Amazon's PR/FAQ is about a page plus an FAQ, and it is followed by customer testing (K2). My default recommendation is narrower. Before building, write a short description of intended behaviour, unless a cheaper experiment can answer the question. Treat it as a cheap forcing function for design choices, not as a gate. Cap the effort in advance.

**The evidence is thin.** Neither of us located a controlled or observational study comparing documentation-first with code-first outcomes for solo founders (K1). The case on both sides rests on practitioner essays, company self-reports, and mechanism arguments. My recommendation is a judgment call, not a finding.

**What changed my mind:**
- **Coordination benefit (K3).** I accepted Codex's point that much of README-first's value comes from having a team. For a solo founder, what remains is clarifying scope for oneself and letting early users or a future self read it. Nothing shows that any of this requires the README to precede the first experiment. I also withdrew my claim about AI agents as readers.
- **Demand evidence (K4).** I moved from "prose can't validate demand" to a narrower claim. Private prose can't validate demand. A written offer shown to real customers gives weak behavioural signals short of purchase. What mattered was customer contact, not documentation order. I dropped my unsourced claim that demand is the dominant risk.
- **Spec-driven AI tools (K6).** I dropped the "vendor-sourced" label. Research exists, including ESEM 2026 and an arXiv preprint. It studies other populations and proxy outcomes, not solo-founder outcomes. I also dropped my unsourced inference about prototype costs.
- **Agile Manifesto (K9) and Amazon (K7).** The Manifesto ranks values and sets no order in time. Amazon's process bundles advance writing with testing and iteration, so it can't isolate the effect of writing first.
- **Cost cap (K14).** A fixed one-day cap is not tied to the decision. I now say the writing budget should not exceed the cost of the cheapest experiment that could test the same hypothesis. One day is only a rough default.

**Where we still differ (K12, K5, K14).** Codex would start from a recorded uncertainty, observable outcome, threshold and effort budget, and then choose the artifact. I would also require a short behavioural description. I think writing it forces design decisions. Codex sees no evidence for adding it. I can't settle this either, so I rate it a values and procedure dispute.

**Remaining doubts.** These are unsourced:
- Documentation-first helps more for APIs, CLIs and libraries than for visual products. I hold this as a mechanism-based hypothesis (K5).
- Demand failures outnumber feasibility failures among solo founders (K10). The latency exception holds either way.

If the writer publishes, the safe wording is "none located by either debater," not "none exists."

Changed my mind on:
- Coordination benefits of README-first do not transfer to solo founders (K3)
- Written offers exposed to customers give weak demand evidence; private prose gives none (K4)
- Dropped 'vendor-sourced' framing for spec-driven tools; research exists but studies proxies (K6)
- A fixed one-day cap is not tied to the decision; budget should be anchored to the cheapest falsifying experiment (K14)
- Dropped the unsourced claim that demand risk dominates solo-founder failure

Still unconvinced on:
- That a default short behavioural description should be required, rather than only a decision-criterion test plan (K12); it is a value judgment with no evidence either way
- That documentation-first helps more for APIs and CLIs than for visual products (K5); mechanism-based, unmeasured
- That demand failures outnumber feasibility failures for solo founders; unsourced and not needed for the K10 latency exception
- Whether the cap should be anchored to the cheapest falsifying experiment or set per task (K14)

### Codex

A solo founder should not treat documentation as a prerequisite for coding. A short README or behavioural description can clarify scope and expose interface choices, but the evidence reviewed does not establish that writing it before the first experiment improves founder outcomes. Neither debater located a study directly comparing documentation-first with code-first sequencing for solo founders. Comprehensive documentation before any code is therefore unjustified as a general rule.

My preferred procedure remains: before the next deliberate experiment, record the uncertainty, observable outcome, decision threshold and effort budget. Then choose the artifact or experiment that addresses that uncertainty. That could be a written offer shown to customers, an API contract, a paper prototype or an implementation experiment. This is an **unsourced procedural judgment**, not a demonstrated superior workflow.

I revised several positions. Customer behaviour toward a written offer can provide limited demand evidence, although private prose cannot. README-first retains legitimate uses for early readers and future reference even when team coordination benefits disappear. I also corrected the characterization of specification-driven coding research: empirical work beyond vendor material exists, but the studies discussed do not establish solo-founder outcomes or a sequencing advantage. On effort limits, I favor a precommitted budget with explicit reassessment over a universal one-day cap.

I remain unconvinced that every founder should default to a product description before experimenting. Claude's strongest rationale is that describing intended behaviour forces design decisions. That is a plausible mechanism, but it does not settle whether those decisions should precede an experiment capable of informing them. Likewise, reviewing an API contract before implementation is possible, but that does not establish a greater outcome benefit than documentation offers visual products. These remaining disagreements concern procedure and interpretation under missing comparative evidence.

Changed my mind on:
- Customer behaviour toward a written offer provides limited demand evidence.
- Solo founders retain legitimate reader and reference uses for advance documentation, although sequencing benefits remain unmeasured.
- Specification-driven coding research extends beyond vendor material, but does not establish solo-founder sequencing benefits.
- Effort limits should involve a precommitted budget and reassessment, without asserting a universal one-day cap.

Still unconvinced on:
- A short product description should be the default prerequisite to the first experiment.
- Documentation-first produces greater benefits for API products than for visual products.
- The writing budget should universally be anchored to the cheapest falsifying experiment.

## Research briefings

### Claude

I did not run live searches this turn. This briefing relies on well-known primary sources that I'm confident exist, and I've marked confidence accordingly. The question has no direct empirical literature for solo founders. The evidence is practitioner argument, analogies from larger teams, and recent AI-assisted "spec-driven" tooling.

Pro side: Tom Preston-Werner's "Readme Driven Development" (2010) argues a README written first forces you to clarify scope and saves wasted code. Amazon's "working backwards" process writes a press release and FAQ before building. Design-first API practice (OpenAPI) writes the contract before the code. Parnas and Clements (1986) argue for writing documentation as if the design were rational, because it disciplines thinking. Spec-driven tools for AI coding (GitHub Spec Kit, AWS Kiro) make a written spec the main input to code generation.

Con side: The Agile Manifesto values "working software over comprehensive documentation." Docs written before contact with users and code go stale, and a solo founder's main risk is building something nobody wants, which docs can't test. Royce's 1970 paper is the classic warning about big up-front design. 37signals' *Getting Real* advises designing the interface first and keeping specs minimal.

Most defensible middle: write a short, disposable artifact first (one-page README, press-release/FAQ, or API sketch) and write full documentation after the design stabilizes. The real disagreement is what "documentation" means (README vs. user manual vs. internal spec) and whether the goal is clarity of thought or customer validation. I found no controlled study comparing doc-first to code-first for solo founders.

- **Readme Driven Development is the best-known explicit doc-first argument for small projects.** (high confidence) Preston-Werner (GitHub co-founder) argues you should write the README before any code, so you consider the design and avoid building the wrong thing. It is an opinion essay with no data. [1]
- **Amazon's Working Backwards writes a customer-facing press release and FAQ before building, showing doc-first works as a product-definition tool at scale.** (medium confidence) The process was described by Bryar and Carr in the book 'Working Backwards' (2021). The artifact is a roughly one-page press release plus FAQ, not full documentation. No published controlled outcome data. [2]
- **The Agile Manifesto explicitly ranks working software above comprehensive documentation, a direct counterweight.** (high confidence) Manifesto text: 'Working software over comprehensive documentation.' It also says that while there is value in the items on the right, the items on the left are valued more. [3]
- **Parnas and Clements argue that docs written as if the design were rational improve the design process, even though real design is not rational.** (medium confidence) Their 1986 paper 'A Rational Design Process: How and Why to Fake It' recommends documenting as if designing top-down. It's the more precise argument that the document can be written after, yet in an idealized form. [4]
- **Spec-driven development has been revived by AI coding agents, with the spec as the primary artifact.** (medium confidence) GitHub released Spec Kit as an open-source toolkit for spec-driven development with AI agents. AWS's Kiro IDE uses requirements, design and task specs before code generation. These are vendor claims; independent outcome evidence is thin. [5], [6]
- **Design-first API development (writing the OpenAPI contract before code) is an established doc-first practice with documented benefits for parallel work and consumer review, benefits that matter less to a solo founder.** (medium confidence) The OpenAPI Initiative and vendor guidance describe design-first as enabling parallel front-end/back-end work and early feedback. A solo founder has no parallel team to coordinate. [7]
- **Big up-front design has a long-criticized record, which cautions against full docs first.** (medium confidence) Royce's 1970 paper 'Managing the Development of Large Software Systems' is often cited as the origin of waterfall, though Royce himself said the simple sequential form was risky and recommended iteration. [8]
- **37signals' Getting Real recommends interface-first design and minimal specs rather than heavy written docs, a solo-scale counterexample.** (medium confidence) The book argues for starting with the interface and avoiding functional specs, because specs create an illusion of agreement. It is a practitioner opinion from a bootstrapped company. [9]
- **A solo founder's dominant risk is market risk, which doc-first does not address without customer contact.** (medium confidence) Lean Startup and Paul Graham's essays emphasize shipping and talking to users early. This is an interpretation. Graham's 'Do Things That Don't Scale' is the commonly cited source. [10]

Contested points: Definition: 'documentation' as a README or one-page PR/FAQ versus a full user manual or technical spec. Most pro-doc-first evidence concerns the small artifacts.; Whether writing is a validation tool or just a thinking tool. A doc can be shown to customers, but a prototype tests demand better. This is partly an empirical question and partly a value judgment about cost.; Whether the AI-coding era changes the answer, because a spec now directly drives code generation and lowers the cost of code, which makes up-front clarity more valuable. The evidence is mostly vendor claims.; Solo founder context: team-coordination benefits (API contracts, shared understanding) vanish, but the founder's future self and early users remain as readers.; Docs-rot risk: docs written first are likely to diverge from the product; the severity depends on whether they are kept as living artifacts.

### Codex

The evidence supports distinguishing a short description of the intended product from comprehensive documentation written before implementation. Tom Preston-Werner explicitly advocates writing a README first, while limiting it to one introductory file. Amazon describes writing a one-page press release and FAQ before development, followed by customer testing and iteration. These are documented practices and practitioner arguments, not controlled demonstrations that documentation-first improves solo-founder outcomes.

The strongest relevant experimental evidence concerns entrepreneurial hypothesis testing rather than documentation sequence. Four randomized trials involving 759 firms found that teaching a scientific approach increased idea termination and affected pivot patterns. This supports testing explicit assumptions, but does not establish whether prose, prototypes, or code should come first. A study of 20 software startups likewise examines learning through prototypes without comparing documentation-first against code-first.

Counterarguments emphasize information discovered through building and use. Basecamp argues that detailed functional specifications force premature decisions. Usability guidance supports testing inexpensive prototypes before implementation, providing an alternative to both extensive writing and immediate production coding.

This research found no direct controlled comparison of documentation-first and code-first among solo founders. A defensible provisional interpretation is to write enough to expose the intended user experience and assumptions, then choose the cheapest credible test of the largest uncertainty. That interpretation remains unproven as a universal sequencing rule. The debate should settle what counts as documentation, whether experimental code is exempt, and which outcomes justify the founder's time investment.

- **F1. The original README-first argument explicitly limits the amount of advance documentation.** (high confidence) Tom Preston-Werner's August 23, 2010 essay says, "Write your Readme first." It restricts the proposed design documentation to one introductory file and explicitly distinguishes this from extensive documentation-driven development. [1]
- **F2. Some benefits claimed for README-first depend on having multiple developers, limiting their relevance to a solo founder.** (high confidence) Preston-Werner separately argues that a defined interface lets other developers begin projects that integrate with the software before implementation is complete. His individual benefits concern thinking through scope and the public API before changing code. [1]
- **F3. Amazon uses customer-oriented writing before development, but its artifact is a product proposal rather than a complete user manual.** (high confidence) AWS describes a single-page future press release written before budgeting, team assembly, or coding. Its accompanying FAQ addresses customer questions and internal questions about profitability and resources. [11]
- **F4. Amazon's writing-first process includes subsequent empirical testing rather than treating the document as sufficient validation.** (high confidence) The AWS account describes exposing customers to products in development, measuring their impact, releasing limited initial versions, and adjusting them using feedback. [11]
- **F5. Randomized entrepreneurship research supports explicit hypothesis testing, but does not test documentation-first.** (high confidence) Camuffo and colleagues' 2024 study combines four randomized controlled trials involving 759 firms and 11,463 observations. It reports increased idea termination and pivot results consistent with treated firms making a few changes rather than none or repeated changes. [12]
- **F6. Startup-specific research identifies prototyping as a learning process, without establishing one universal artifact sequence.** (medium confidence) Nguyen Duc, Wang, and Abrahamsson conducted a multiple-case study of 20 European software startups. They grouped influences on prototyping into artifacts, team competence, collaboration, customer, and process dimensions. [13]
- **F7. Basecamp presents a direct practitioner objection to detailed specifications written before implementation.** (high confidence) Getting Real argues that functional specifications create an illusion of agreement and require important decisions when information is lowest. It recommends learning through building and using the application. [14]
- **F8. Early testing can use inexpensive interactive representations instead of either documentation or production code.** (medium confidence) Jakob Nielsen describes conducting studies using three homepage mockups and learning how users understood the proposed services. His paper-prototyping guidance recommends observing users before implementation. [15]
- **F9. The Agile Manifesto does not reject documentation, and does not prescribe code-first sequencing.** (high confidence) The manifesto values "Working software over comprehensive documentation" and explicitly states that the items receiving lower priority still have value. [3]
- **F10. Broader documentation research does not resolve the solo-founder sequencing question.** (medium confidence) A 2023 systematic literature review selected 74 studies published between 2010 and June 2021. It identified nine factors relevant to agile documentation and found that documentation tools and methods address different challenges without being synchronized. [16]
- **F11. For APIs, a written interface description can also become input to implementation tools.** (high confidence) The Swagger 1.2 specification states that API description files can drive Swagger UI documentation and Swagger Codegen client generation, with additional uses by testing tools. [17]

Contested points: Definition: A short README, future press release, API contract, functional specification, and complete user manual impose different costs and test different assumptions.; Empirical dispute: No direct controlled solo-founder comparison was located. Practitioner success stories cannot isolate documentation sequence from other development practices.; Interpretation: Preston-Werner's limited README-first proposal and Basecamp's rejection of extensive functional specifications may be compatible despite their different rhetoric.; Interpretation: Evidence favoring explicit hypotheses and early customer feedback does not establish that documentation must precede every line of experimental code.; Empirical dispute: Documentation may clarify an intended interface, while a prototype may reveal interaction or feasibility problems that prose cannot establish. Their relative value remains unquantified here.; Value judgement: The acceptable delay before building depends on how the founder weighs clarity, speed, rework, and scarce attention.

## Debate transcript

### Opening positions

#### Claude

**Thesis:** A solo founder should write a *short, disposable* description of the product before building (a README, one-page press release/FAQ, or API sketch). They should not write *comprehensive* documentation first. The short document is a thinking tool, not a validation tool. The riskiest assumption still needs a prototype or customer contact, and sometimes that test should come before even the short document.

**What the evidence is.** There is no controlled comparison of doc-first and code-first for solo founders. I did not run new searches this turn. The claims below rest on sources I know and should be re-checked before publication. Every pro-doc-first source is a practitioner essay or a company's account of its own process. The only randomized evidence I know of (Camuffo et al., Strategic Management Journal, 2024, [12]) tests hypothesis-driven decision-making, not documentation order.

**The strongest objection to my own position.** Preston-Werner's README-first essay [1] is the best pro case. For a solo founder, though, its benefits shrink. The coordination benefit disappears, because there are no other developers to unblock. What remains is "think before coding", and a throwaway spike or paper prototype may do that better for interaction and feasibility questions. So the claim "write first" is strongest for APIs, CLIs and developer tools, where the README *is* the interface. It is weakest for visual consumer products.

**Where the sides actually agree.** Basecamp's *Getting Real* [14] attacks functional specs, not a one-page statement of intent. Amazon's PR/FAQ is one page and is followed by customer testing and iteration [11]. The dispute is mostly about what "documentation" means. A writer should say this plainly instead of staging a doc-first versus code-first fight.

**The AI-coding wrinkle.** Spec-driven tools such as GitHub Spec Kit [5] and Kiro [6] make the written spec the input to generation. This raises the value of written intent. It also makes code cheaper, which strengthens the case for building a throwaway prototype. The evidence for these tools is vendor material.

#### Codex

A solo founder should usually write a short, testable account of the intended product before committing to production implementation. The evidence does not justify requiring finished documentation before any code. My proposed rule is conditional: describe the user, intended outcome, one representative interaction, and the assumption that could invalidate the project. Then choose the next activity by what it can establish. This is a recommendation under uncertainty, not an experimentally established optimum.

The strongest case for writing first is that explaining an interface forces decisions before those decisions become implementation work. Tom Preston-Werner explicitly makes that argument, while restricting advance documentation to one introductory README. His essay supports a bounded design exercise, not a complete manual [1].

The strongest objection to Claude's proposed middle position concerns the word “first.” Even a short document should not become a mandatory gate before an experiment. Consider a founder whose proposed product depends on an untested latency requirement. A benchmark can establish whether the requirement is achievable. A readable account of the intended behavior cannot establish that fact. This is a logical objection to a universal sequence. Whether allowing such experiments actually improves founder outcomes remains an empirical question.

Amazon provides evidence that writing before development is an operational practice. Its account also describes customer testing, measurement, and iteration. Attributing the benefits of that combined process specifically to document order would exceed the evidence [11].

The strongest experimental evidence here supports explicit hypotheses and tests. Camuffo and colleagues studied 759 firms across four randomized trials and found increased idea termination and changes in pivot patterns. Their intervention does not identify the effect of documentation sequence [12].

The factual dispute is what these sources demonstrate. The interpretive dispute is how far their lessons transfer to solo founders. The value judgment is how much delay to accept for additional clarity. A useful comparison would measure total founder time to a predefined customer or feasibility test, including document preparation and revisions. Until that comparison exists, the writer should present documentation first as a conditional technique, with explicit exceptions, rather than a proven rule.

**Referee.** Round 0 opening: both debaters converge on a short, non-mandatory pre-build description rather than comprehensive documentation-first, and agree that the cited Camuffo study and Amazon process do not isolate document order. Open disagreements remain on the solo-founder transfer of README-first benefits (K3), whether demand requires prototypes or customer contact (K4), the interface-product boundary (K5), and AI spec-tool evidence (K6), plus Codex's new Agile Manifesto and latency claims (K9, K10), none yet answered. Status: 7 agreed, 6 open.


### Round 1

#### Claude

**K9 (Agile Manifesto): agree.** The manifesto says "while there is value in the items on the right, we value the items on the left more." That ranks working software above comprehensive documentation. It does not order the two in time. It also targets *comprehensive* documentation, which is the artifact we already agree a solo founder should not write first. A writer should not cite it as a rule for code-first. The manifesto is a priority statement, and I will not use it to support code-first sequencing. This is an interpretive point and the text settles it [3].

**K10 (latency): agree, with a limit.** The logical point holds. Prose cannot show that an untested system meets, say, a 50 ms p99. A benchmark or spike can. I accept it as a real exception to any "document first, always" rule. The limit is that it is narrow. It covers feasibility risks that can be tested numerically. Most solo-founder failures I can point to are demand failures, not feasibility failures. I have no source for that base rate. The nearest source I know is CB Insights' founder post-mortem list, which cites "no market need" as the top reason, but I have not rechecked it this turn, so treat it as unverified. K10 therefore supports "choose the test by what it can establish." It does not support a general code-first default.

**K3: revise.** I overstated it. A solo founder loses *team* coordination but keeps three audiences: their future self after a break, early users or beta testers, and, increasingly, an AI coding agent that consumes the text as input. The last one is not coordination between humans, but it is a reader who cannot ask clarifying questions, so the README-first logic partly survives. Revised claim: "For a solo founder, README-first's benefit of unblocking other developers disappears. The benefits of forcing design decisions and of giving a reader context (future self, early users, AI agents) remain, though no study measures them." This is an interpretation, and the AI-agent part rests on vendor material [5].

**K4 (demand): maintain.** Codex has not contested it, and K10 supports it by analogy: the right next activity depends on what it can establish. A document can't establish purchase intent. Camuffo et al. is consistent with this, because their treated firms terminated more ideas after testing hypotheses [12]. Here the document's role is to make the hypothesis explicit and falsifiable. That is a defensible use, and it is not validation.

**K5 and K6: maintain, unaddressed by Codex.** Neither has a new source. K5 stays an untested interpretation. K6 stays vendor-sourced. The writer should label both that way.

**Strongest objection to the emerging consensus (K12).** "Short, testable description first, but not a gate" risks being unfalsifiable. If the rule yields to any experiment that "can answer a question the description cannot," it excludes almost nothing, because a founder can always claim that. The consensus is therefore a heuristic and not a rule. It is useful only if it states a cost cap. I propose a concrete one: the description should take no more than about a day, which is my judgment and not an empirical figure. A founder who has spent longer has probably drifted into comprehensive documentation, which K13 says the evidence does not support. Whether one day is the right cap is a value judgment about delay, and I agree with Codex that the evidence cannot settle it.

**What the writer can state.** Facts: no controlled study exists (K1), and the pro sources bundle writing with testing (K7, K8). Interpretations: how much transfers to solo founders (K3, K5). Values: how much delay to accept (K12 cap).

Responses:
- K9 — **accept**: The manifesto text ranks values ('value the items on the left more') and orders nothing in time; it also targets comprehensive documentation, which both sides already reject as a first step.
- K10 — **accept**: Prose cannot demonstrate an untested numerical latency; it is a valid exception, though narrow, since most solo-founder risk is demand rather than feasibility (base rate unsourced).
- K3 — **revise**: I overstated it: only the unblocking-other-developers benefit vanishes; future-self, early-user and AI-agent readers remain. Revised: For a solo founder, README-first's benefit of unblocking other developers disappears, while forcing design decisions and giving context to readers such as the future self, early users and AI agents remains, unmeasured by any study.
- K4 — **maintain**: New argument: Camuffo's treated firms terminated more ideas, so the value lies in explicit falsifiable hypotheses tested with customers; a document only states them and cannot validate purchase intent.
- K5 — **maintain**: Codex did not address it. It remains an untested interpretation resting on the OpenAPI design-first practice.
- K6 — **maintain**: Codex did not address it. All evidence for spec-driven AI tools that I know of is vendor-sourced.

Evidence requests:
- K10: Data showing most failed solo-founder products failed on technical feasibility rather than demand would make the latency exception broad and weaken a doc-first default.

#### Codex

A solo founder should write enough to define the next test, but the evidence does not establish that product documentation should precede experimental code. Two distinctions sharpen that recommendation: customer-facing text can participate in a demand test, and an API contract can describe behavior without demonstrating that behavior.

**K4 is the most consequential dispute.** Claude's strongest argument is that private prose and polite customer approval cannot establish purchase intent. That holds. The objection is that this does not establish a hierarchy in which a prototype necessarily provides stronger demand evidence. Buffer founder Joel Gascoigne reports testing a two-page product description, then adding pricing and observing plan clicks and email submissions before building the functioning product. Those actions provided evidence of interest, although no payment occurred in that test. His first paying customer arrived after launch. This is a founder's retrospective account, not a controlled comparison, but it demonstrates why “prose cannot validate demand” needs a narrower formulation: the evidence comes from customer behavior around the offer, rather than from whether the offer is expressed through prose or working software [18].

**K3 and K5 concern mechanisms, not demonstrated founder outcomes.** Preston-Werner explicitly includes enabling other developers to work before implementation. A founder working alone loses that particular benefit. External readers can still review the proposed interface, but neither his essay nor the sources examined quantify the resulting benefit for solo founders [1]. OpenAPI explicitly describes service capabilities for humans and computers without requiring source access. That supports reviewing a contract before implementation. It does not make the description equivalent to the delivered service, or prove that API founders benefit more than consumer-product founders from writing first [19].

**K6 needs updating.** Search located empirical research beyond tool documentation. An ESEM 2026 paper examines 88,052 pull requests across 119 repositories, but explicitly studies specification artifacts, mostly issue references, rather than committed SDD tool outputs. A separate preprint compares specification frameworks on generated-code determinism and automated detection metrics. Neither establishes improved solo-founder outcomes. The defensible conclusion is therefore narrower than “all evidence is vendor material”: relevant empirical research exists, but the outcome and population required for this recommendation remain untested in these sources ([20]; [21]).

Claude's objection to K12 identifies a real problem with unrestricted exceptions, but a one-day cap does not solve it. Duration cannot distinguish useful documentation from wasteful documentation without reference to the decision it supports. My proposed operational constraint is to identify the uncertainty, observable result, and decision threshold before choosing an artifact. This is a procedural recommendation, not a proven optimum. Claude's requested failure base rate is unavailable here, and the latency counterexample does not require technical failures to predominate: it defeats mandatory sequencing, while establishing no code-first default.

Responses:
- K3 — **revise**: Preston-Werner explicitly identifies enabling parallel developer work as a benefit, which does disappear when nobody else is implementing. His discussion of interface review supplies a separate mechanism involving prospective users. The magnitude of either benefit for solo founders remains unmeasured. The assertion that AI agents cannot ask clarifying questions should be removed as an unsupported universal. Revised: A solo founder loses README-first's parallel developer coordination benefit, while interface review and later reference remain possible uses whose effect on founder outcomes is unmeasured.
- K4 — **revise**: Buffer's reported pricing-page experiment supplies a concrete counterexample to treating written offers as incapable of producing demand evidence. Clicks and email submissions measure interest, not purchases. Neither a document nor a prototype establishes purchase intent merely by existing. The dominant risk across solo founders remains unsourced. Revised: Private prose cannot establish demand, but customer behavior in response to a written offer can provide limited demand evidence before a functioning product exists.
- K5 — **revise**: The OpenAPI specification supports the contract-review mechanism, but supplies no comparative evidence ranking product categories. An interface description also cannot demonstrate service reliability or performance. This is an interpretive boundary rather than a measured advantage. Revised: Written API contracts permit interface review without implementation, but the available evidence does not establish that documentation-first yields greater benefits for API products than for visual products.
- K6 — **revise**: Live search found empirical publications beyond vendor documentation, so the broad vendor-only characterization cannot stand. Their measured artifacts and code metrics do not establish solo-builder business outcomes. Cheaper throwaway prototypes remain a conditional argument, not an established net effect of spec-driven tools. Revised: Empirical research on specification artifacts and specification-driven generation exists, but the sources located do not establish that spec-driven AI tools improve solo-founder outcomes.
- K9 — **maintain**: Claude's acceptance resolves the textual dispute. An additional limitation is that a ranking of working software and comprehensive documentation cannot distinguish README-first from prototype-first, since either sequence can satisfy that ranking.
- K10 — **maintain**: The requested prevalence evidence is unavailable here. It is unnecessary for this claim: one relevant feasibility counterexample defeats an unconditional documentation-first rule regardless of the population failure rate. It does not establish a general code-first default.
- K12 — **revise**: Replace unrestricted exceptions with an explicit test-selection procedure: state the uncertainty, observable result, and decision threshold before selecting prose, customer contact, or a prototype. This makes compliance observable, although its comparative effectiveness remains untested. The one-day cap is an unsupported preference, and elapsed time alone does not define comprehensive documentation. Revised: Before substantial implementation, explicitly identify the next uncertainty and decision criterion, then choose an artifact or experiment capable of testing it, without requiring product documentation before experimental code.
- K1 — **maintain**: The newly located specification studies examine repository artifacts or generated-code metrics, so they do not fill the specific solo-founder sequencing evidence gap. The publishable wording should remain that neither debater has located such a study, rather than asserting that none exists.

Evidence requests:
- K5: A comparison measuring total time to validated interface decisions or customer tests across API and visual products under documentation-first and prototype-first workflows would support the proposed product-category ranking.
- K6: An independent comparison of solo builders using spec-driven tools and an appropriate alternative, including specification time, revisions, correctness, and customer outcomes, would support a founder-specific recommendation.

**Referee.** Round 1 narrowed several points: K9 and K10 are now agreed, and K3 and K4 moved toward each other on what remains of README-first and what counts as demand evidence. K6 was reopened when Codex located independent empirical research that contradicts the broad 'vendor-only' wording, which Claude has not yet answered. The main open disagreement is how to make the 'short description first' default falsifiable: a one-day cap (K14, K12) versus a decision-criterion procedure. Status: 1 agree to disagree, 8 agreed, 5 disputed.

- Repetition flag on K6 (claude): Claude maintained K6 without addressing Codex's new independent sources (ESEM 2026, arXiv preprint).
- Repetition flag on K5 (claude): Claude's K5 maintain was based on Codex not addressing it; Codex has now responded with a revision, which Claude has not answered.

### Round 2

#### Codex

A solo founder should not treat product documentation as a prerequisite to experimental code. My revised recommendation drops the default requirement for a product description. It retains a brief written test plan: the uncertainty, observable outcome, decision threshold, and effort budget. This is a proposed procedure, not an empirically established optimum.

**K12 and K14 contain Claude's strongest objection.** A rule that permits any experiment without recording its purpose can excuse almost anything retrospectively. My previous procedure lacked an explicit stopping rule. I therefore revise it: before the next deliberate experiment, record what decision its result could change and set a maximum effort budget. Stop at the budget or specified observation, whichever comes first, and record whether to proceed, abandon, or authorize a separately bounded follow-up. Observable violations include starting without those entries, exceeding the budget without reassessment, or changing the success threshold after seeing results while reporting the original test as successful. These requirements apply to writing and coding alike. No experiment receives an exemption merely because the founder calls it exploratory.

That accepts Claude's demand for operational constraints without accepting a universal one-day allowance. A founder could follow a one-day documentation cap while never identifying a decision the document informs. Conversely, exceeding one day does not establish that a document is comprehensive. The choice between a fixed cap and a task-specific budget remains a procedural value judgment. Whether either improves founder outcomes is an empirical question we have not settled.

**K3 requires separating usefulness from sequencing.** Future selves and early users are legitimate readers. A README can preserve an intended interface for later reference and expose it to early review. Preston-Werner explicitly presents a README as an introduction for prospective users, alongside the team coordination argument [1]. However, those readers do not establish that the README must precede the first experiment. Early users might review a description before implementation. A founder might document the interface after a spike reveals what is feasible. These are alternative sequences, and their relative outcomes remain unmeasured here.

**K4 is an evidential distinction, not a disagreement about private prose.** A written offer can generate observable customer behavior. Buffer's founder reports pricing-plan clicks and email submissions before building the functioning product, followed by a paying customer after launch [18]. That is limited evidence of interest, not proof of purchase intent. Camuffo's hypothesis-testing results cannot establish that such signals carry zero information or that a working prototype is required.

**K6 needs a scope correction.** Claude says I supplied no source, but both research links from my previous turn resolve. The ESEM paper explicitly studies specification artifacts rather than SDD tool adoption and reports no protective defect effect. It therefore cannot establish tool benefits [20]. The separate preprint compares SDD frameworks on generated-code metrics, not founder outcomes [21]. Neither warrants recommending documentation-first to founders. Their existence does require distinguishing research on specification practices from evidence of improved solo-founder outcomes.

For the writer, the defensible answer is conditional: use advance product writing when it supports the next decision. Do not present README-first, prototype-first, or my bounded testing procedure as a proven universal sequence.

Responses:
- K1 — **maintain**: The checked specification studies examine repository or generated-code outcomes, not solo-founder sequencing. The publication-safe statement remains that neither debater located a direct comparison, rather than that none exists.
- K3 — **revise**: The README essay explicitly addresses prospective users, supporting reader context beyond team coordination. Future-self reference is a plausible, unmeasured mechanism. Neither mechanism establishes a benefit from writing before the first experiment. The assertion that AI agents cannot ask clarifying questions is unsupported and unnecessary. Revised: Solo founders can use advance descriptions for early-user review and later reference, but the sources examined do not establish that these uses improve outcomes more when documentation precedes experimental code.
- K4 — **maintain**: Buffer's reported pricing clicks and signups distinguish behavioral responses to a written offer from private writing. These are limited interest signals, not purchases. The dispute concerns their evidential weight, and the cited hypothesis-testing study does not resolve it.
- K5 — **agree_to_disagree**: The crux remains unavailable comparative evidence. Contract review is a mechanism, while ranking API products above visual products for documentation-first benefits requires outcome evidence neither side supplies.
- K6 — **revise**: Live checking confirms the two previously supplied papers exist. I narrow my earlier independence characterization because publication outside vendor documentation alone does not establish absence of author interests. The ESEM study explicitly excludes observed SDD tool output, and the preprint measures framework proxy outcomes. Revised: Empirical research beyond vendor documentation examines specification artifacts and SDD frameworks, but the checked studies do not establish improved solo-founder outcomes or a documentation-first sequencing advantage.
- K7 — **maintain**: The causal identification limitation remains: a process combining writing and testing cannot identify sequencing effects without a comparison that varies sequencing separately.
- K8 — **maintain**: Idea termination following hypothesis-testing training does not identify whether advance product documentation caused the change. The treatment and the disputed sequencing recommendation remain different interventions.
- K9 — **maintain**: Claude's accepted interpretation permits both sequences, so the manifesto cannot discriminate between the competing recommendations.
- K10 — **maintain**: Direct answer to the evidence request: I have no representative data showing technical feasibility causes most solo-founder failures. Such data are unnecessary to establish an exception and would not, by themselves, compare documentation-first with experiment-first outcomes.
- K12 — **revise**: My default drops the short product description. It retains a short written test plan and adds an effort budget. This resolves the ambiguity between writing a decision criterion and writing product documentation. The recommendation is unsourced procedural judgment. Revised: Before the next deliberate experiment, record its uncertainty, observable outcome, decision threshold and effort budget, then select the artifact or experiment without requiring a prior product description.
- K13 — **maintain**: The checked newer specification research supplies no solo-founder sequencing evidence that would justify a comprehensive-documentation prerequisite.
- K14 — **revise**: Claude's concrete objection that my previous procedure lacked a stopping rule moves me to add a precommitted effort budget and reassessment. Violations are observable: missing advance criteria, exceeding the budget without reassessment, or retrospectively changing the threshold while claiming success. Compliance is auditable, while effectiveness remains unproven. Revised: The proposed procedure requires a precommitted effort budget and reassessment at the budget or specified observation, but neither its effectiveness nor a universal one-day cap is established by the available evidence.

#### Claude

**Where the debate has converged.** Both sides agree that no direct comparison exists (K1), that comprehensive documentation first is unsupported (K13), and that the famous pro sources bundle writing with testing (K7, K8). The remaining disputes are narrow.

**K4 (Buffer).** Yes, a pricing-page click counts as demand evidence in my framing. It is weak evidence. It is behavioural and comes from strangers, so it beats private prose. I concede my earlier wording was too strong. Revised: private prose cannot validate demand, but a written offer shown to real customers can yield weak behavioural signals. Two limits remain. First, the evidence comes from the exposed offer plus a landing page, a deployed artifact. It is not the founder's internal design document. Second, Buffer's own account is a single success story, so it cannot show the signals predicted payment. The step that mattered was customer contact, not documentation order. Codex and I now differ little here. The sequencing question is whether a landing page counts as "documentation." If it does, the term stops separating the two camps.

**K6.** I revise to Codex's wording. Independent research on specification artifacts exists, but it covers non-founder populations and proxy outcomes. My claim that evidence was "vendor-sourced" was too broad. Revised: no independent evidence exists on solo-founder outcomes from spec-first AI workflows. Codex's own ESEM source reports that specification artifacts do not reduce defects. On the evidence cited, that result leans against the pro side. I could not re-verify the ESEM or arXiv sources this turn, so I rely on Codex's descriptions of them. The "cheaper code lowers prototype cost" point is my inference and is unsourced.

**K5.** On contract review, Codex's mechanism is fair: a written API contract can be reviewed before implementation. That is a plausible reason documentation-first suits interface-as-text products. Neither side has comparative outcome data, so I agree to disagree. The writer should present it as a mechanism-based hypothesis.

**K3.** I accept Codex's revision. Reader benefits exist (early users, future self), but nothing shows they require the README to precede the first experiment. I drop my claim that agents "cannot ask clarifying questions" as unsupported.

**K12/K14.** Codex's objection holds. A one-day cap does not track the decision. I propose a cap tied to the decision threshold: the budget should be a fraction of the cost of the cheapest experiment that could falsify the same hypothesis. If writing the description costs more than a landing page or a spike would, the founder should run the test instead. Codex's budget-plus-reassessment procedure is compatible with this. Two points remain open. Codex drops the product description entirely and keeps only a test plan. That is a real difference. A test plan names the uncertainty but does not make the founder specify the product's behaviour. Specifying behaviour is what Preston-Werner and Amazon claim forces design decisions. No evidence settles this. It is a value and procedure judgment.

**Remaining crux for the writer.** Facts: no direct study exists, and the cited spec research is not about founders. Interpretations: how much README-first transfers to solo work, and whether a landing page is "documentation." Values: how much delay is acceptable, and whether a product description or a test plan is the better default. Both procedures are unvalidated.

Responses:
- K3 — **accept**: Codex's point that Preston-Werner addresses prospective users, and that reader benefits do not show the README must precede experiments, is correct. I withdraw the agent claim.
- K4 — **revise**: A pricing click counts as weak behavioural evidence. Private prose cannot validate demand, but a written offer shown to customers can yield limited signals. This is a landing page, not an internal document, and Buffer is one anecdote. Revised: Private prose cannot establish demand; a written offer exposed to real customers yields weak behavioural signals short of purchase, and the signal comes from customer exposure rather than documentation order.
- K5 — **agree_to_disagree**: Contract review is a plausible mechanism, but there is no comparative outcome evidence across product categories. The ranking is interpretation.
- K6 — **revise**: Independent research on specification artifacts exists, so a vendor-only claim is too broad. None measures solo-founder outcomes. I rely on Codex's description of the studies without having re-verified them. Revised: No independent evidence located measures solo-founder outcomes from spec-first or spec-driven workflows; the research that exists studies other populations and proxy outcomes.
- K12 — **revise**: I accept a decision-linked test plan as a necessary component. I still favour a short behavioural description as the default because it forces design choices. This is a value judgment with no evidence either way. Revised: Before building, record the uncertainty, threshold and budget; also write a short description of intended behaviour unless a cheaper experiment answers the question.
- K14 — **revise**: A fixed one-day cap is not tied to the decision. I propose a cap relative to the cost of the cheapest experiment that could answer the same question. Revised: The writing budget should not exceed the cost of the cheapest experiment that could test the same hypothesis; one day is a rough default only.

Evidence requests:
- K12: Any comparison showing that founders who recorded only a test plan reached good decisions as often as those who also wrote a behavioural description.

**Referee.** Round 2 narrowed the debate considerably: K3, K4 and K6 now have revised wording that both debaters substantively hold, and Claude explicitly conceded K3's reader-benefit point. The remaining disagreements (K12 and K14) are value and procedure judgments about the default writing budget and whether a short product description belongs in it, which neither side can settle with current evidence. K5 remains agree-to-disagree on comparative evidence. Status: 3 agree to disagree, 10 agreed, 1 conceded.

- Repetition flag on K7 (codex): Maintained without new argument or evidence; restates the causal-identification limit already agreed.
- Repetition flag on K8 (codex): Maintained without new argument; restates that the study does not test sequencing.
- Repetition flag on K9 (codex): Maintained with a restated interpretation rather than new argument; the claim is already agreed in substance.

## References

1. Readme Driven Development. <https://tom.preston-werner.com/2010/08/23/readme-driven-development.html> — Practitioner argument for writing the README first; not empirical.
2. Working Backwards: PR/FAQ concept. <https://www.workingbackwards.com/concepts/working-backwards-pr-faq> — Describes the PR/FAQ artifact; it's from the authors' own company, so it is promotional.
3. Manifesto for Agile Software Development. <https://agilemanifesto.org> — States the value preference; it doesn't prohibit lightweight docs.
4. A Rational Design Process: How and Why to Fake It (IEEE TSE, 1986). <https://ieeexplore.ieee.org/document/6312940> — Supports idealized documentation as a design discipline; it is about large systems, not solo founders. I did not verify the IEEE URL this session.
5. GitHub Spec Kit. <https://github.com/github/spec-kit> — Shows tooling that treats specs as the source of truth for AI-generated code.
6. Kiro. <https://kiro.dev> — Vendor product built on spec-first workflow.
7. OpenAPI Initiative learning hub. <https://learn.openapis.org> — General guidance on specification-driven API work; I did not verify a specific design-first page.
8. Royce, Managing the Development of Large Software Systems (1970). <https://www.praxisframework.org/files/royce1970.pdf> — Source for the waterfall origin and the author's own warnings; the hosting URL is unverified.
9. Getting Real (37signals/Basecamp). <https://basecamp.com/books/getting-real> — Argues against functional specs and for interface-first design.
10. Do Things that Don't Scale. <https://paulgraham.com/ds.html> — Supports early user contact over up-front planning; does not mention documentation specifically.
11. The Secrets to Project Management at AWS. <https://d1.awsstatic.com/executive-insights/en_US/product-management-ebook.pdf> — Documents Amazon's stated process, without isolating its causal effect or testing its applicability to solo founders.
12. A scientific approach to entrepreneurial decision-making: Large-scale replication and extension. <https://onlinelibrary.wiley.com/doi/10.1002/smj.3580> — Provides causal evidence about training in scientific entrepreneurial decision-making, not the ordering of documentation and coding.
13. What influences the speed of prototyping? An empirical investigation of twenty software startups. <https://arxiv.org/abs/1712.00674> — Offers observational evidence about startup prototyping and learning, without a documentation-first comparison or a solo-founder estimate.
14. Getting Real, chapter 59: There's Nothing Functional about a Functional Spec. <https://basecamp.com/gettingreal/getting-real.pdf> — Establishes a competing practitioner position against extensive advance specifications, rather than experimental proof against short README drafts.
15. Paper Prototyping: Getting User Data Before You Code. <https://www.nngroup.com/articles/paper-prototyping> — Provides practitioner experience supporting early prototype testing, but its broad cost multipliers are estimates rather than solo-founder trial results.
16. Documentation Practices in Agile Software Development: A Systematic Literature Review. <https://arxiv.org/abs/2304.07482> — Shows the breadth and fragmentation of agile documentation research, but its reported results do not establish a documentation-first advantage.
17. Swagger RESTful API Documentation Specification, version 1.2. <https://docs.swagger.io/spec.html> — Establishes that an interface document can serve executable tooling purposes, without proving that authoring it first improves startup outcomes.
18. Idea to Paying Customers in 7 Weeks: How We Did It. <https://buffer.com/resources/idea-to-paying-customers-in-7-weeks-how-we-did-it> — Gascoigne describes collecting email submissions and pricing-plan clicks before building the functioning product.
19. OpenAPI Specification. <https://spec.openapis.org/oas/latest.html> — Defines a machine-readable and human-readable description of HTTP service capabilities independent of source-code access.
20. Specification Artifacts in Open-Source Pull Request Workflows Do Not Reduce Defects. <https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ESEM.2026.84> — Studies specification artifacts across open-source pull requests and explicitly distinguishes them from SDD tool output.
21. Citation Discipline in Spec-Driven Development. <https://arxiv.org/abs/2606.30689> — Reports controlled comparisons of framework conditions on generated-code determinism and automated detection metrics, not founder outcomes.

---
_Generated 2026-10-20 16:45 by debate._
