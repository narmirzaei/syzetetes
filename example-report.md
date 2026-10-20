# D0006 — Tabs or spaces for Python?

_A structured debate between two AI models, with independent research, a bookkeeping referee, and a numbered reference list._

| | |
|---|---|
| Date | 2026-10-21 |
| Claude | haiku (effort: low) |
| Codex | gpt-6.1-sol (effort: low) |
| Referee | claude sonnet (effort: medium) |
| Judge | Jev (jev-latest): independent ruling on every claim; 2 final status(es) contested |
| Rounds | 1 after opening positions |
| Ended because | Reached the round cap (1). |
| Claims | 5 agreed, 1 disputed, 1 open |

**Derived from** D0005 (kept research and rounds 0-1).

## Executive summary

**Result.** The debate ended on a practical rule, not a claim that one choice is better. For new code, use 4 spaces. For existing code, keep the project's convention unless there is a concrete reason to change. Both debaters endorsed this (K7).

**Established facts**
- Python 3 accepts consistent tab indentation. Tabs expand to the next multiple of 8 columns. Only mixtures whose meaning depends on tab width raise TabError (K1). Source: [1]
- PEP 8 recommends 4 spaces, prefers spaces, and allows tabs for consistency with existing tab-indented code (K2). Source: [2]
- Black emits four spaces per level and has no tab mode. Google's style guide requires four spaces and prohibits tabs (K3). Sources: [15] and [6]
- The two CPython files checked, Lib/textwrap.py and Lib/test/test_tabnanny.py, use spaces for implementation code. No tree-wide census was done (K5).

**What changed during the debate**
- Claude withdrew the claim that spaces are inherently more robust (K4). Codex's expandtabs checks showed that an identical tab prefix followed by spaces keeps alignment at widths 2, 4 and 8. Only differing tab prefixes break it.
- Claude also withdrew the claim that no controlled study exists (K6), because no exhaustive search had been run.

**Still contested or open**
- K4: Claude still believes mixed-prefix alignment failures are common in practice, but it has no measured frequency for this. Codex argues the hazard is avoidable and that PEP 8 permits hanging indents, so alignment is optional. Whether predictable columns outweigh adjustable width is a value judgement.
- K6: Nobody searched for controlled performance studies. The only study cited was qualitative: Pandey, Oney and Begel (CHI 2024), with 16 blind or visually impaired developers who favoured tabs for navigation. Claude never answered that paper directly, but its closing statement said the paper is evidence it had not weighed.
- K7 nuance: Codex added that documented accessibility needs can justify reconsidering a convention. Claude accepted this in its closing statement.

## Points of agreement

### K1. Python 3 accepts consistent tab indentation and rejects only width-dependent mixtures of tabs and spaces with TabError.

Both sides agreed. Tabs expand to the next multiple of 8 columns, and spaces are not a syntactic requirement. The source is the Python lexical analysis reference: [1]

*Judge agrees: agreed with confidence 0.98; cases even (0.56); crux kind none.*

### K2. PEP 8 recommends four spaces per level, prefers spaces, and permits tabs to stay consistent with existing tab-indented code.

Both sides agreed this is a convention, not a language rule. Codex added that project consistency outranks mechanical compliance. Source: [2]

*Judge agrees: agreed with confidence 0.99; cases even (0.92); crux kind none.*

Sources: [2]

### K3. Black emits four spaces per level with no tab mode, and Google's Python style guide requires four spaces and prohibits tabs.

Claude had verified Black's no-option policy and the Google guide, but not the four-space width. Codex closed that gap with Black's source, where Line.__str__ multiplies a four-space string by depth. This describes tools and institutional preference, not human performance. Sources: [15] and [6]

*Judge agrees: agreed with confidence 0.94; Codex's case stronger (0.91); crux kind none.*

Sources: [9], [7], [6]

### K5. The CPython files checked, textwrap.py and test_tabnanny.py, use spaces for implementation indentation; a tree-wide claim is unverified.

Claude narrowed its claim to textwrap.py. Codex added test_tabnanny.py, where tab characters appear only in test fixtures. Both accepted that this is a sample-level observation and that no tree-wide census was done.

*Judge agrees: agreed with confidence 0.33; Codex's case stronger (0.58); crux kind scope or definition.*

Sources: [8], [12]

### K7. Use four spaces for new Python code; in an existing project, follow its established convention unless there is a concrete reason to migrate.

Both sides held this core rule. Codex added that Black compatibility supports spaces for new code and that documented accessibility needs can be a concrete reason to migrate. In its closing statement Claude accepted this qualification.

*Judge agrees: agreed with confidence 0.78; Codex's case stronger (0.38); crux kind none.*

Sources: [2]


## Points of disagreement

### K4. Whether spaces are more robust than tabs across editors and views is contested; all-tab block structure is width-independent, and the continuation-alignment hazard is layout-dependent.

- **Claude:** Withdrew the original wording. Revised: all-tab block structure is width-independent, but spaces used for continuation alignment after tabs render differently by tab width; the weighting is a value judgement.
- **Codex:** Rejects the original wording. Argues the alignment hazard is layout-dependent: an identical tab prefix followed by spaces keeps alignment at widths 2, 4 and 8 (checked with expandtabs); only differing tab prefixes break it. PEP 8 permits hanging indents, so alignment is optional.
- **Crux:** Both reject the original wording, so the judge's non-agreed reading is accepted. The remaining factual split is whether the continuation-alignment hazard is general or avoidable by encoding. Whether predictable columns outweigh adjustable width is a value judgement.
Both sides rejected the original claim that spaces are more robust. Codex's expandtabs checks showed that an identical tab prefix followed by spaces keeps alignment at widths 2, 4 and 8, and that only differing prefixes break it. Claude still thinks mixed prefixes are a common failure in practice, but it has no measured frequency. Whether predictable columns outweigh per-reader width control is a value judgement.

*Judge disagrees: rules **agree to disagree** with confidence 0.52 (referee: disputed); Codex's case stronger (0.93); crux kind value judgement.*

Sources: [1], [11], [4]


## Open points

### K6. No controlled study of tab versus space indentation was located, but this is unverified, and qualitative accessibility evidence supports tabs for some users.

- **Claude:** Withdrew the absence claim; no exhaustive search was run, so it is unverified.
- **Codex:** Rejects the absence claim as established. Cites Pandey, Oney and Begel (CHI 2024), a qualitative study of 16 blind or visually impaired developers recommending tabs for navigation. It is not a controlled performance study.
- **Crux:** The judge's open ruling is adopted. The earlier 'agreed' status is withdrawn because both sides revised the claim. It stays open: Claude has not responded to the CHI 2024 paper, and no one has searched for controlled performance studies.
Claude withdrew its absence claim because it had not run an exhaustive search. Codex cited Pandey, Oney and Begel (CHI 2024), a qualitative study of 16 blind or visually impaired developers who recommended tabs for navigation. That study is not a controlled performance comparison. Nobody searched for controlled studies, so the question stays open.

*Judge disagrees: rules **disputed** with confidence 0.46 (referee: open); Codex's case stronger (0.69); crux kind missing evidence.*

Sources: [13]

## Strongest case for

The case for spaces rests on convention and tooling. PEP 8 prefers four spaces. Black emits only four spaces per level and has no tab mode. Google's guide requires four spaces and prohibits tabs. The CPython files checked use spaces. Spaces give predictable columns, so Python sources look the same in every editor and review view. Following the dominant convention also avoids friction with formatters and style guides. Codex framed this as a recommendation about convention and tooling, not a demonstrated human-performance advantage.

## Strongest case against

The case for tabs is that Python 3 accepts consistent tabs, and an all-tab block structure does not depend on display width. Each reader can set the width they want. Codex's checks showed the alignment problem is narrow: an identical tab prefix followed by spaces keeps alignment at widths 2, 4 and 8. PEP 8 permits hanging indents, so alignment is optional, and it also permits tabs in existing tab-indented code. Pandey, Oney and Begel (CHI 2024) is a qualitative study of 16 blind or visually impaired developers who recommended tabs for navigation. The debaters agreed that documented accessibility needs can justify reconsidering a convention. No controlled study showed spaces to be better.

## Guidance for the author

- Present the 4-space default as convention and tooling, not as a language requirement or a measured productivity result.
- State accurately that Python 3 accepts consistent tabs and raises TabError only for width-dependent mixtures.
- Cite PEP 8 [2], Black's style documentation [15] and the Google guide [6] for the tooling claims.
- Treat spaces being more robust than tabs as a value judgement. Do not repeat it as established fact.
- Describe the CHI 2024 study as qualitative, with 16 participants, not as controlled evidence.
- Include the rule for existing projects and the accessibility exception.
- If you need a claim about controlled studies or about CPython as a whole, do the search or census yourself first.

## Caveats

- No research briefings were produced, and no exhaustive literature search was run by either side. The absence of controlled studies is unverified, not established.
- The CPython evidence covers two files only. It says nothing about the whole tree or about Python projects generally.
- The only empirical human-factors source is a small qualitative study (16 participants) of blind or visually impaired developers. It does not measure defects, readability or productivity.
- Claude's belief that mixed-prefix alignment failures are common has no measured frequency. Codex's expandtabs checks were done on specific layouts and may not generalise.
- Claude did not directly respond to the CHI 2024 paper in the ledger, though its closing statement acknowledges it.
- The judge's confidence on K4 and K6 was low (about 0.5 for each), and K5 was agreed at only 0.325 confidence, so treat those rulings as provisional.

## Closing statements

### Claude

## Closing statement: tabs or spaces for Python

**Final position.** Python accepts consistent tab indentation. Mixing tabs and spaces is rejected only when the meaning depends on tab width, which the interpreter reports as TabError. For new code, use 4 spaces. For existing code, follow the project's established convention unless there is a concrete reason to migrate. PEP 8 [2] states this preference directly. Black [14] emits four spaces per level and offers no tab mode. Google's Python style guide [6] requires four spaces and prohibits tabs. The 4-space default is a convention about tooling and institutional preference, not a language requirement.

**What I changed my mind about.**
- **K3 (Black's indentation width).** I had verified Black's no-option policy but not the four-space width. Codex's citation of Black's source, where Line.__str__ multiplies a four-space string by depth, closed that gap.
- **K4 (robustness of spaces).** I withdrew the original wording. Codex's expandtabs check changed my view. An all-tab block prefix is width-independent. Continuation alignment breaks only when the tab prefixes of the two lines differ. An identical tab prefix followed by spaces keeps alignment at widths 2, 4 and 8. The hazard is real but narrower than I first claimed.
- **K6 (controlled studies).** I withdrew the claim that no such study exists. I had not run an exhaustive search. Codex's citation of Pandey, Oney and Begel (CHI 2024) is a qualitative study of 16 blind or visually impaired developers who favoured tabs for navigation. It is not a performance study, but it is evidence I had not weighed.
- **K7 (migration).** Codex's point that documented accessibility needs can justify migrating a project's convention is correct. I accept it as a qualification of the agreed rule.

**What I remain unconvinced of.**
- **K4, the factual part.** I still think alignment after mixed prefixes is a common failure mode in practice, because editors and reviewers do not all keep prefixes identical. I have no measured frequency for this, so the claim is unsourced and I hold it with low confidence.
- **K4, the value part.** Whether predictable columns outweigh per-reader width control is a value judgement. Neither side can settle it from the evidence.
- **K6, the open question.** No one has searched for controlled performance studies on defects, readability or productivity. The question stays open until someone does.

**Kind of disputes.** K3 was a factual gap, now closed. K4 is partly factual (how general the alignment hazard is) and partly a value judgement (predictability versus adjustability). K6 is an open evidence gap. K5 is a sample-level observation: the CPython files checked use space-based implementation indentation, and the tree-wide claim is unverified.

Changed my mind on:
- K3: Black's four-space width is now sourced via Black's Line.__str__ implementation.
- K4: the all-tab structure is width-independent; the alignment hazard applies only when tab prefixes differ, per the expandtabs check.
- K6: withdrew the claim that no controlled study exists; the CHI 2024 qualitative study on blind and visually impaired developers is relevant evidence.
- K7: documented accessibility needs can justify migrating an existing convention.

Still unconvinced on:
- K4 factual: alignment breakage after mixed tab prefixes is common in practice; I have no measured frequency, so this is unsourced and held with low confidence.
- K4 value: whether predictable columns outweigh per-reader tab width control is a value judgement that the evidence cannot settle.
- K6: no controlled performance study on defects, readability or productivity has been found, and no systematic search was run, so the question stays open.
- K5: the tree-wide claim about CPython indentation remains unverified; only textwrap.py and test_tabnanny.py were checked.

### Codex

My final recommendation is **four spaces for new Python code, and the established convention for an existing project unless there is a concrete reason to migrate** (K7). This follows PEP 8 and fits Black's formatting behavior. It is a recommendation about convention and tooling, not a demonstrated advantage in human performance [4] [15].

**K1 and K2: accept.** Consistent tabs are valid Python. Python expands tabs to the next multiple of eight columns and rejects indentation mixtures whose meaning depends on tab width. Spaces are preferred by PEP 8, not required by Python's grammar [1].

**K4: revise.** I reject the broad claim that tabs inherently make block structure less robust across display widths. The strongest objection concerns continuation alignment when tabs and spaces interact. Our checked examples narrowed that objection: identical tab prefixes followed by spaces preserve alignment, while differing prefixes can disrupt it. Hanging indents also make column alignment optional. Predictable columns versus adjustable indentation width remains a value judgement, not an established performance result.

**K5: accept the limited finding.** The two inspected CPython files use spaces for implementation indentation. That sample does not establish a repository-wide result.

**K6: revise.** The evidence changed my assessment of accessibility: the qualitative study of 16 blind or visually impaired developers supplies a concrete reason to consider tabs for some users. It does not establish a controlled productivity or readability advantage. Neither side conducted a search sufficient to establish that controlled comparisons do not exist.

I therefore retain spaces as the default while rejecting claims of universal superiority. Documented accessibility needs can justify reconsidering an existing convention.

Changed my mind on:
- K4: Narrowed the rendering objection to particular alignment layouts rather than tabs generally.
- K6: Accessibility evidence gives tabs a concrete user-specific justification.
- K6: An unsuccessful or incomplete search cannot establish the absence of controlled studies.

Still unconvinced on:
- K4: That predictable columns universally outweigh reader-adjustable indentation width.
- K6: That either indentation style has an established controlled advantage in defects, readability or productivity.
- K5: Any tree-wide CPython indentation claim based on the two inspected files.

## The referee's verdict

Use four spaces for new Python code. In an existing project, follow its established convention unless you have a concrete reason to migrate. Both debaters ended here (K7). This is a convention and tooling choice, not a language rule and not a demonstrated performance advantage. Python 3 accepts consistent tabs and rejects only mixtures whose meaning depends on tab width (K1). PEP 8 prefers spaces but permits tabs for consistency (K2). Black and Google's guide enforce four spaces (K3). The debaters did not agree on whether spaces are more robust than tabs across editors and diffs (K4). Claude thinks the alignment hazard is common in practice, but it has no measured frequency. Codex showed it is layout-dependent. Whether predictable columns outweigh per-reader width control is a value judgement. Whether controlled studies exist is unresolved (K6). Qualitative accessibility evidence favours tabs for some users, and both sides accepted that it can justify migration.

## Debate transcript

### Opening positions

#### Claude

**Thesis:** For Python, spaces are the correct default, and the question is settled more by convention and tooling than by any language rule. Tabs are legal and work, so the case for spaces rests on consistency and on the fact that the language's own guidance prefers them. The "tabs are more accessible" argument is real but does not outweigh that.

**Caveat on inputs:** The message said two research briefings were attached, but none came through. This position is drawn from my own knowledge and the sources below. I did not run a search, so every factual claim should be re-checked before publication.

**Claim 1 (fact, high).** Python 3 accepts either tabs or spaces but refuses ambiguous mixing. Indentation is measured with tab stops every 8 columns, and inconsistent mixing raises `TabError`. This is documented in the lexical analysis reference [1]. Practical consequence: a file can run correctly with tabs, so "tabs break Python" is false. The real hazard is mixing, which the interpreter catches.

**Claim 2 (fact, high).** PEP 8, the de facto style guide, says to use 4 spaces per indentation level and that spaces are preferred. It allows tabs only to stay consistent with code that already uses them [2]. This is the strongest single document in the dispute, and it is a convention, not a language requirement.

**Claim 3 (fact, medium-high).** Major Python tooling and guides standardise on spaces. Black normalises indentation to 4 spaces and has no tab mode [3]. Google's Python style guide also specifies spaces only [6]. I am less certain about the exact wording of the Google guide's indentation section, so check it before quoting it.

**Claim 4 (interpretation, medium).** Spaces give more predictable rendering across editors, diff tools, and web views because their width does not depend on a user's tab-width setting. Tabs give each reader control over display width, which is the main accessibility argument. For Python, the first property matters more because Python's semantics depend on indentation: a file that looks aligned in one editor can look misaligned in another, and continuation-line alignment is where that bites. This is a judgement about which failure mode matters more, so treat it as contestable.

**Claim 5 (fact, medium, unverified in this session).** The CPython standard library and its test suite use spaces. Check this against the CPython repository before publishing. I am reasonably confident but have not checked the current tree.

**Claim 6 (value, high confidence that it is a value dispute).** The remaining disagreement is largely about taste and team convention. I know of no controlled study comparing defect rates, readability, or productivity between tab- and space-indented Python. If a writer says "research shows spaces are better," that claim is unsupported as far as I know. Low confidence that such a study does not exist, because I have not searched for one.

**Strongest objection I expect from the tabs side.** Tabs let each developer set display width, which is an accessibility gain for people with low vision or unusual preferences. A fair steelman: PEP 8 is a recommendation, and a team that enforces tabs consistently with a formatter loses none of Python's correctness. My reply is that this is accepted, but it means the choice is one of local convention, not a correctness fact, and a writer should say so rather than present spaces as objectively required.

**What would change my view:** evidence that a major Python project of comparable size uses tabs and reports fewer indentation-related bugs, or a controlled study showing accessibility or comprehension gains that outweigh the alignment problems.

#### Codex

Use four spaces per indentation level for new Python code. In an existing project, follow its established convention unless there is a concrete reason to migrate. This recommendation rests on Python's published style guidance and indentation semantics. It does not require claiming that spaces improve programmer intelligence, productivity, or accessibility.

The strongest case for tabs is that an indentation character can represent structure while the reader chooses its displayed width. That is a real distinction between tabs and spaces. However, Python gives tabs a specific interpretation: during indentation processing, a tab advances to the next multiple of eight columns. A reader's preferred display width does not change that rule. The practical objection concerns files containing both tabs and spaces: the displayed alignment can differ from the indentation Python computes. The language reference documents both the expansion rule and the conditions under which inconsistent mixing raises `TabError` [1].

That objection has a limit. Consistent tab indentation is legal Python. It would be inaccurate to say that Python requires spaces or that every mixture of tabs and spaces is rejected. The narrower conclusion is that spaces avoid the discrepancy between configurable tab display and Python's fixed tab expansion rule.

The recommendation also has an explicit institutional basis. PEP 8 specifies four spaces per indentation level and prefers spaces, while allowing tabs to preserve consistency in code already using them. Its broader guidance places project consistency ahead of mechanical compliance with the document [4]. Thus, converting a coherent existing codebase solely to satisfy a slogan misrepresents the guidance being invoked.

These are disputes about different things. Whether tabs are legal and how they expand are factual questions. Whether following the documented default outweighs adjustable display width is a practical value judgement. Whether either convention improves productivity or accessibility requires evidence beyond a style guide. My thesis is consequently specific: spaces are Python's documented default and the better recommendation for new code. Tabs remain defensible where an existing project's convention supplies a concrete reason to retain them.

**Referee.** Both sides agree on the language facts (consistent tabs are legal, 8-column expansion, TabError on ambiguous mixing) and on what PEP 8 says. They also agree there is no evidence of productivity or accessibility effects. The one real disagreement is K4, the weight of rendering predictability against adjustable tab width. K3, K5 and K7 are still unverified or not yet answered by the other side. Status: 3 agreed, 1 disputed, 3 open.


### Round 1

#### Claude

**Verification pass on the open items**

**K3 (Black and Google).** Verified in part. Google's Python style guide, Indentation section, says "Indent your code blocks with 4 spaces" and then "Never use tabs" [6]. Black's FAQ says it provides no option to change indentation style, that requests for one will not be considered, and that PEP 8 is the basis [7]. The FAQ also concedes "we recognise that using tabs is an accessibility issue as well" and points users to expand/unexpand conversion hooks. I could not confirm from the fetched Black pages the literal phrase "normalises to 4 spaces". That is widely known behaviour, but I have not sourced the wording, so I downgrade it to a claim about policy ("no tab mode, by design") rather than a quoted width.

**K4 (rendering).** The claim as worded does not survive. "Spaces are more robust across editors, diffs and web views" is unsourced for diffs and web views, and it treats all tab use as one case. Split the cases:
- Block indentation in a file that is all tabs: Python's block structure does not depend on display width, because each tab is one indentation step under the 8-column rule and the interpreter never reads the display setting. The semantic hazard is gone. Display width only changes how deep blocks look, which is the accessibility benefit.
- Continuation-line alignment: PEP 8 asks for continuation lines to align with an opening delimiter. In a tab-indented file, aligning inside a line requires spaces after the leading tabs. Python's tokenizer ignores whitespace inside brackets, so this is legal, but it renders differently at each tab width. This is the residual rendering problem, and it is the one that still applies to consistent-tab files.

So the rendering problem survives only for alignment, not for block structure. That is a factual claim about the tokenizer plus an interpretation about which failure matters more. The weighting of that failure against adjustable display width is a value judgement.

**K5 (CPython).** Partially verified. I fetched `Lib/textwrap.py` from the main branch [8]. Its indentation is spaces only, with no tab characters in leading whitespace. That is one file, not the tree. The CPython developer guide style page returned a 404 when fetched, so I have no citation for the test suite. I withdraw the blanket claim and keep only the single-file fact.

**K6 (absence of studies).** I did not run a search for controlled studies, so I cannot support "no controlled study shows." The judge's open ruling is correct on wording. The defensible claim is that I have not located evidence either way, and the dispute is therefore unverified rather than settled.

**K7 (existing-project exception).** Accepted. PEP 8 states that "Tabs should be used solely to remain consistent with code that is already indented with tabs" and that "Consistency within a project is more important" [2]. That is the document's own text, not my inference. It moved me because it means the exception is institutional, not a concession I made up. Codex's position and mine now match on new code and on existing projects.

**Strongest objection, pressed.** The tabs side's best case is Black's own accessibility concession. Black chose not to offer tabs, and its FAQ acknowledges the accessibility cost and offers a workaround instead. That is a designed trade-off, not a fact that settles the matter. My remaining claim is narrower: for Python, the documented default and the tooling both point to spaces, and the one place where tabs fail (alignment) is real. Whether that alignment cost outweighs per-reader display width is a value judgement, and I do not claim to resolve it.

**Classification.** Facts: the tokenizer rule, PEP 8 wording, Google's "Never use tabs", Black's no-option policy, the CPython sample. Interpretation: that alignment is the main residual rendering issue. Values: whether accessibility outweighs alignment, and how much weight project convention gets.

Responses:
- K3 — **revise**: Google's guide is verified verbatim ('Never use tabs'). Black's FAQ is verified to say it offers no indentation-style option and cites PEP 8, and it concedes an accessibility issue. I could not verify the literal '4 spaces' wording for Black from its pages, so that part is downgraded. Revised: Google's Python style guide says to indent with 4 spaces and to never use tabs, and Black's FAQ states it provides no option to change indentation style (tabs are not supported by design).
- K4 — **revise**: The rendering problem does not apply to block indentation in files that use only tabs, because Python's block structure is independent of display width under the 8-column rule. It still applies to continuation-line alignment that uses spaces after leading tabs, which is legal but renders differently at each tab width. The weighting against adjustable display width remains a value judgement. Wording as previously stated was overbroad and unsourced for diffs and web views. Revised: In files indented only with tabs, display width does not change Python's block structure, but spaces used for continuation-line alignment after tab indentation render differently across tab-width settings; whether this outweighs reader-adjustable display width is a value judgement.
- K5 — **revise**: I fetched Lib/textwrap.py from the CPython main branch: spaces only, no tab characters in indentation. That is one file. The developer guide page returned 404, and I did not check the test suite or the whole tree. The claim is narrowed accordingly. Revised: A sampled CPython standard library module (Lib/textwrap.py on main) indents with spaces only; the rest of the tree and the test suite are unchecked.
- K6 — **revise**: I did not run a search for controlled studies, so I cannot support a claim that none exist. The honest statement is that no evidence was located in this round, and the dispute is unverified. Revised: I have not located a controlled study comparing tab and space indentation on defects, readability, productivity or accessibility; this is unverified because no exhaustive search was run.
- K7 — **accept**: PEP 8 states 'Tabs should be used solely to remain consistent with code that is already indented with tabs' and 'Consistency within a project is more important.' That is the document's own text and it supports the existing-project clause as institutional guidance, not my inference.

Evidence requests:
- K6: A controlled experiment (peer-reviewed or preprint) comparing tab and space indentation on comprehension, error rate or accessibility. Its existence would make the claim false; its absence after a proper search would support it.
- K5: Evidence that a significant part of the CPython tree (Lib/ or Lib/test) uses tab indentation would contradict the sampled file and require narrowing the claim further.

#### Codex

Four spaces remain my default recommendation for new Python projects, based on documented conventions and Black compatibility. Two corrections change the supporting argument: tab-based alignment need not break when tab width changes, and accessibility has empirical evidence favoring tabs for some users.

**K3:** The original tooling claim can be restored. Black's implementation constructs indentation with `indent = "    " * self.depth`, directly establishing four spaces per level [9]. Its FAQ excludes indentation-style configuration [7]. Google's guide explicitly requires four spaces and prohibits tabs [10]. These establish tool behavior and institutional preferences, not superior human performance.

**K4:** I reject the original claim as worded, including its assertion that rendering predictability outweighs adjustable width. Claude's strongest remaining argument is that delimiter alignment introduces a display hazard even when block indentation consistently uses tabs. That hazard exists for some layouts, but the proposed mechanism is overgeneralized. Equal tab prefixes followed by spaces preserve relative alignment across tab widths.

Here is a reproducible counterexample, with whitespace represented as escaped strings: `"\tresult = func(first,"` and `"\t              second)"`. Both argument names start at zero-based columns 16, 18 and 22 for tab widths 2, 4 and 8 respectively. I verified those positions using Python's `expandtabs`. Replacing the second prefix with two tabs and six spaces produces columns 10, 14 and 22, breaking alignment except at width 8. Thus the failure depends on how alignment is encoded, not merely on spaces following tabs. PEP 8 also permits hanging indentation, so delimiter alignment is optional [4].

Spaces do provide invariant indentation columns under changes to tab stops. Consistent tabs preserve block relationships while allowing those columns to change. Some mixed alignment layouts break, others do not. This is a factual distinction. Which property matters more is a value judgement, and neither establishes a general ranking across editors, diffs and web views.

**K6:** I reject the original absence claim as established knowledge. A targeted search found Pandey, Oney and Begel's CHI 2024 paper, *Towards Inclusive Source Code Readability Based on the Preferences of Programmers with Visual Impairments*. Its qualitative study involved 16 blind or visually impaired developers comparing differently formatted code snippets. The authors recommend tabs for character-level navigation [13]. This answers the accessibility evidence request with relevant empirical evidence, although it is not a controlled performance experiment establishing differences in defects or productivity. I therefore cannot remain neutral by implying there is no accessibility evidence. Its scope supports some users' navigation needs, not universal superiority.

**K5 and K7:** A checked test-suite module, `Lib/test/test_tabnanny.py`, uses spaces for its executable indentation and includes tab-containing test strings [12]. That extends Claude's sample but does not establish a tree-wide census. Tabs in fixtures must be distinguished from implementation indentation. The recommendation to preserve established project conventions remains supported by PEP 8, with demonstrated accessibility needs supplying a concrete reason to reconsider a project's default.

Responses:
- K3 — **revise**: Black's Line.__str__ implementation explicitly multiplies a four-space string by indentation depth. This supplies the missing direct evidence for width. Google's guide and Black's FAQ verify the remaining policies. Revised: Black generates four spaces per indentation level and offers no tab indentation mode, while Google's Python style guide requires four spaces and prohibits tabs.
- K4 — **revise**: I reject the original claim as worded. The executable counterexample in the argument shows that an identical tab prefix followed by spaces preserves delimiter alignment at widths 2, 4 and 8. Claude's revised claim still overstates the residual hazard. Revised: Spaces preserve indentation columns across tab-stop settings, while consistent tab prefixes preserve relative alignment and block relationships. Some alignment layouts with differing tab prefixes break across settings, but this is avoidable and does not establish that rendering predictability outweighs reader-adjustable width.
- K5 — **revise**: The checked test_tabnanny.py adds a test-suite example using spaces for executable indentation. This directly answers the request with an additional sample, not evidence about a significant fraction of the tree. Tab-containing test fixtures do not contradict spaces-based implementation indentation. Revised: Checked CPython examples include a standard-library module and a test-suite module with spaces-based implementation indentation, but the blanket tree-wide claim remains unverified.
- K6 — **revise**: I do not accept the original absence claim as established. Pandey, Oney and Begel's qualitative study of 16 blind or visually impaired developers supplies empirical accessibility evidence favoring tabs for character-level navigation. It does not establish a controlled performance advantage, and this targeted search cannot prove that no controlled comparison exists. Revised: Qualitative accessibility evidence supports tabs for some developers' navigation needs, while a controlled tab-versus-space performance comparison was not located in this targeted search.
- K7 — **maintain**: Verified Black behavior adds a concrete compatibility reason for spaces in new projects. The accessibility study also makes the migration exception substantive: a documented participant need can justify reconsidering an established convention. This remains a recommendation based on priorities, not a measured universal optimum.

**Referee.** Claude verified Google's and Black's policies and narrowed the K4, K5 and K6 wording. Codex supplied Black's source for four-space output, a counterexample showing that consistent tab prefixes preserve alignment, a second CPython sample, and a CHI 2024 accessibility study. K3, K5 and K7 now have common ground. K4 remains a mix of a narrowed factual question and a value weighting. K6 is open because Claude has not answered the new study and no performance-study search was run. Status: 5 agreed, 1 disputed, 1 open.


## References

1. Python Language Reference: Indentation. <https://docs.python.org/3/reference/lexical_analysis.html#indentation> — Defines tab-stop handling and states that inconsistent tab/space use is an error.
2. PEP 8 – Style Guide for Python Code. <https://peps.python.org/pep-0008> — Contains the spaces-preferred and 4-space recommendations.
3. Black documentation. <https://black.readthedocs.io/en/stable> — Official docs for the formatter; check current options before quoting.
4. PEP 8: Indentation. <https://peps.python.org/pep-0008/#indentation> — Specifies four spaces per level and prefers spaces over tabs.
5. PEP 8: Tabs or Spaces?. <https://peps.python.org/pep-0008/#tabs-or-spaces> — Allows tabs for consistency with code already indented using tabs.
6. Google Python Style Guide. <https://google.github.io/styleguide/pyguide.html> — Indentation section: 'Indent your code blocks with 4 spaces' and 'Never use tabs.'
7. Black FAQ: Why spaces? I prefer tabs. <https://black.readthedocs.io/en/stable/faq.html> — Black provides no indentation-style option, cites PEP 8, and acknowledges tabs as an accessibility issue.
8. CPython Lib/textwrap.py (main). <https://raw.githubusercontent.com/python/cpython/main/Lib/textwrap.py> — Leading indentation uses spaces only, with 4-space and 8-space levels.
9. Black indentation implementation. <https://raw.githubusercontent.com/psf/black/main/src/black/lines.py> — Line.__str__ constructs indentation from a four-space string multiplied by depth.
10. Google Python Style Guide: Indentation. <https://google.github.io/styleguide/pyguide.html#s3.4-indentation> — Google requires four spaces and prohibits tabs.
11. Python documentation: str.expandtabs. <https://docs.python.org/3/library/stdtypes.html#str.expandtabs> — Documents configurable tab-stop expansion used in the reproducible alignment check.
12. CPython test_tabnanny.py. <https://raw.githubusercontent.com/python/cpython/main/Lib/test/test_tabnanny.py> — Shows spaces-based executable indentation alongside tab-containing source-code fixtures.
13. Towards Inclusive Source Code Readability Based on the Preferences of Programmers with Visual Impairments. <https://from.so/static/cb9b08b836c39422e8a59f4736326f1c/chi24_617_TAPS_a20eff5b9d.pdf> — Reports a qualitative study with 16 developers and recommends tabs for character-level navigation.
14. https://black.readthedocs.io. <https://black.readthedocs.io>
15. https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html. <https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html>

---
_Generated 2026-10-21 00:15 by debate._
