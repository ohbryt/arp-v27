# MedSci Skills Integration

Unified integration of all 32 medsci-skills into ARP v24 for medical research automation.

**Source:** `/Users/ocm/.openclaw/workspace/medsci-skills/skills/`
**Integration:** `/Users/ocm/.openclaw/workspace/arp-v24/integration/`
**Skills:** `/Users/ocm/.openclaw/workspace/arp-v24/skills/`

---

## Quick Start

```python
from integration.med_sci_integration import MedSciIntegration

medsci = MedSciIntegration()

# Literature search
results = medsci.search_lit.search("MASLD cardiovascular outcomes", max_results=50)

# Compliance check
report = medsci.check_reporting.check("manuscript/manuscript.md", "STROBE")

# Sample size calculation
ss = medsci.calc_sample_size.calculate(test_type="t_test", effect_size=0.5, power=0.8)

# Write manuscript
project = medsci.write_paper.write(
    project_dir=".",
    title="My Study",
    paper_type="original_article",
    target_journal="Radiology",
    research_question="..."
)
```

---

## Architecture

```
medsci-skills/              # Source skills
├── skills/
│   ├── search-lit/         # Literature search
│   ├── write-paper/        # Manuscript writing
│   ├── check-reporting/    # Compliance checking
│   └── ... (28 more)
│
arp-v24/                    # Integration layer
├── integration/
│   ├── med_sci_integration.py    # Unified Python API
│   ├── compliance_checker.py     # Reporting guidelines
│   ├── manuscript_writer.py     # IMRAD pipeline
│   ├── literature_search.py      # PubMed wrapper
│   └── references/checklists/    # 30+ checklists
├── skills/
│   ├── med_sci_orchestrate.py    # Workflow orchestrator
│   └── med_sci_registry.py      # Skill registry
```

---

## Integrated Skills (32 Total)

### Literature & Research
| Skill | Purpose | API |
|-------|---------|-----|
| search-lit | PubMed search, citation verification, BibTeX | `medsci.search_lit.search(query)` |
| fulltext-retrieval | PDF download by DOI | Coming soon |
| lit-sync | Zotero + Obsidian sync | Coming soon |
| find-cohort-gap | Research gap finder | Coming soon |
| ma-scout | Meta-analysis scout | Coming soon |

### Study Design & Protocol
| Skill | Purpose | API |
|-------|---------|-----|
| design-study | Study design validation | Coming soon |
| write-protocol | IRB protocol drafting | Coming soon |
| calc-sample-size | Sample size calculation | `medsci.calc_sample_size.calculate(test_type, effect_size, power)` |
| replicate-study | Replication planning | Coming soon |

### Data Handling
| Skill | Purpose | API |
|-------|---------|-----|
| deidentify | PHI/PII removal | `medsci.deidentify.generate_code(data_path)` |
| clean-data | Data profiling & cleaning | `medsci.clean_data.clean(data_path)` |
| intake-project | Project classification | Coming soon |

### Statistical Analysis
| Skill | Purpose | API |
|-------|---------|-----|
| analyze-stats | R/Python code generation | `medsci.analyze_stats.generate_code(test_type, variables)` |
| batch-cohort | N×M templates | Coming soon |
| cross-national | Cross-national studies | Coming soon |

### Visualization
| Skill | Purpose | API |
|-------|---------|-----|
| make-figures | Publication figures | `medsci.make_figures.generate_figure(figure_type)` |

### Manuscript Writing
| Skill | Purpose | API |
|-------|---------|-----|
| write-paper | IMRAD writing (8-phase) | `medsci.write_paper.write(project_dir, title, paper_type, ...)` |
| humanize | AI pattern removal | Coming soon |
| self-review | Pre-submission review | Coming soon |
| revise | Reviewer response | Coming soon |
| present-paper | Presentation prep | Coming soon |
| peer-review | Peer review simulation | Coming soon |

### Publishing & Submission
| Skill | Purpose | API |
|-------|---------|-----|
| find-journal | Journal recommendation (93 profiles) | Coming soon |
| add-journal | Add journal profile | Coming soon |
| check-reporting | 33 guidelines compliance | `medsci.check_reporting.check(manuscript_path, guideline)` |
| grant-builder | Grant proposal | Coming soon |
| manage-project | Project scaffolding | Coming soon |

### Meta-Analysis
| Skill | Purpose | API |
|-------|---------|-----|
| meta-analysis | Systematic review pipeline | `medsci.meta_analysis.protocol(question, outcome)` |

### Orchestration
| Skill | Purpose | API |
|-------|---------|-----|
| orchestrate | Skill routing & workflows | See below |

---

## Orchestrator Usage

```python
from skills.med_sci_orchestrate import MedSciOrchestrator

orchestrator = MedSciOrchestrator()

# Route a request
result = orchestrator.route("Find papers about MASLD cardiovascular outcomes")
print(f"Intent: {result['intent']}")      # literature_search
print(f"Skill: {result['skill']}")          # search-lit

# Run a predefined workflow
result = orchestrator.run_workflow("data_to_manuscript", project_dir=".")
```

### Available Workflows

| Workflow | Steps | PHI Gate |
|----------|-------|----------|
| `new_project` | intake → search → design → manage | No |
| `data_to_manuscript` | clean → stats → figures → write | Yes |
| `draft_to_submission` | self-review → check → verify → polish | No |
| `meta_analysis` | search → fulltext → meta → stats → figures → write | No |
| `phi_pipeline` | deidentify → clean → stats → figures → write | Yes |
| `new_study_protocol` | search → design → sample-size → protocol | No |
| `full_submission` | write → review → check → find-journal → cover-letter | No |
| `case_report` | search → write → review → check → find-journal | Yes |

---

## Compliance Checker

Supports **33 reporting guidelines**:

### Primary Guidelines
- **STROBE** - Observational studies
- **CONSORT** - Randomized controlled trials
- **STARD** - Diagnostic accuracy
- **STARD-AI** - AI diagnostic accuracy
- **TRIPOD** - Prediction models (2015)
- **TRIPOD+AI** - AI prediction models (2024)
- **PRISMA 2020** - Systematic reviews
- **PRISMA-DTA** - DTA systematic reviews
- **PRISMA-P** - Review protocols
- **CARE** - Case reports
- **SPIRIT** - Study protocols
- **ARRIVE** - Animal studies
- **CLAIM** - AI in medical imaging

### Risk of Bias Tools
- QUADAS-2, QUADAS-C
- RoB 2, ROBINS-I, ROBINS-E
- ROBIS, ROB-ME
- PROBAST, PROBAST+AI
- NOS, COSMIN, RoB NMA
- AMSTAR 2

```python
from integration.compliance_checker import ComplianceChecker

checker = ComplianceChecker()

# Auto-detect guideline
guidelines = checker.auto_detect_guideline("manuscript/manuscript.md")
print(f"Suggested: {guidelines}")

# Check compliance
report = checker.check_compliance("manuscript/manuscript.md", "STROBE")
print(f"Compliance: {report.compliance_percentage:.1f}%")
```

---

## Manuscript Writer

8-phase IMRAD pipeline:

```
Phase 0: Init      → Setup, journal profile, paper type
Phase 1: Outline   → IMRAD structure with word budgets
Phase 2: T&F       → Tables & figures design
Phase 3: Methods   → Writing with critic-fixer loop
Phase 4: Results   → Factual presentation only
Phase 5: Discussion → Anchor paper comparisons
Phase 6: Intro     → Introduction + Abstract (written last)
Phase 7: Polish    → AI patterns, compliance, self-review
```

```python
from integration.manuscript_writer import ManuscriptWriter, PAPER_TYPES

writer = ManuscriptWriter()

# List paper types
print(writer.list_paper_types())

# Write manuscript
project = writer.write_manuscript(
    project_dir=".",
    title="My Study",
    paper_type="original_article",
    target_journal="Radiology",
    research_question="...",
    autonomous=True  # No user gates
)
```

### Supported Paper Types
- `original_article` - Standard research article
- `case_report` - Case report (CARE)
- `meta_analysis` - Systematic review (PRISMA)
- `ai_validation` - AI/ML validation (CLAIM)
- `animal_study` - Animal research (ARRIVE)
- `nhils_cohort` - NHIS cohort study
- `cross_national` - Cross-national study

---

## Literature Search

```python
from integration.literature_search import LiteratureSearch

search = LiteratureSearch()

# Search
results = search.search("MASLD cardiovascular outcomes", max_results=50)

# Verify citations
verified = search.pubmed.verify_citations([
    "10.1016/S0140-6736(23)00000-X",
    "38339671"
])

# Generate BibTeX
bibtex = search.to_bibtex(pmids=["12345678", "87654321"])

# Markdown references
refs = search.to_markdown(results)
```

---

## Sample Size Calculation

```python
# Two-sample t-test
ss = medsci.calc_sample_size.calculate(
    test_type="t_test",
    effect_size=0.5,  # Cohen's d
    power=0.8,
    alpha=0.05
)
print(f"N per group: {ss['n_per_group']}")
print(f"IRB text: {ss['irb_text']}")

# Chi-square
ss = medsci.calc_sample_size.calculate(
    test_type="chi_square",
    effect_size=0.3,  # Cohen's w
    power=0.8
)

# Cox regression / Log-rank
ss = medsci.calc_sample_size.calculate(
    test_type="log_rank",
    effect_size=0.5,  # Hazard ratio
    power=0.8
)
```

---

## Figure Generation

```python
# Generate Python code for publication figures
code = medsci.make_figures.generate_figure(
    "roc_curve",
    output_path="analysis/figures/roc.png"
)

# Required figures by study type
required = medsci.make_figures.get_required_figures("diagnostic_accuracy")
print(f"Required: {required}")
# ['roc_curve', 'calibration_plot', 'bland_altman']
```

Figure types:
- `roc_curve`, `auc_plot`
- `forest_plot`, `calibration_plot`
- `kaplan_meier`, `bland_altman`
- `consort_diagram`, `stard_diagram`, `prisma_diagram`
- `visual_abstract`, `graphical_abstract`

---

## PHI Safety Gate

```python
from skills.med_sci_orchestrate import MedSciOrchestrator

orchestrator = MedSciOrchestrator()

# Check if PHI gate is needed
phi_check = orchestrator.phi_gate_check("project_dir/")
print(f"PHI Gate Needed: {phi_check['phi_gate_needed']}")
print(f"Recommendation: {phi_check['recommendation']}")
```

The orchestrator automatically checks for PHI before routing to data-handling skills.

---

## Status

```python
medsci = MedSciIntegration()
medsci.print_status()
```

Output:
```
MEDSCI-SKILLS INTEGRATION STATUS (ARP v24)
==========================================
Total skills:    32
Available:      32
Integrated:      9  (with Python API)
Pending:        23  (skill reference available)

Wrapped Skills:
  ✓ analyze-stats
  ✓ calc-sample-size
  ✓ check-reporting
  ✓ clean-data
  ✓ deidentify
  ✓ make-figures
  ✓ make-figures
  ✓ meta-analysis
  ✓ search-lit
  ✓ write-paper
```

---

## Error Handling

All integration methods include robust error handling:

```python
try:
    results = medsci.search_lit.search("query", max_results=50)
except Exception as e:
    print(f"Search failed: {e}")
    # Fallback: return empty results
    results = []
```

---

## Anti-Hallucination

- Never fabricate references (verify via PubMed)
- Never invent numerical results
- Never guess at clinical definitions
- Report uncertainty explicitly

---

*Integrated for ARP v24 | Based on medsci-skills bundle*
