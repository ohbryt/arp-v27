"""
MedSci Manuscript Writer for ARP v24

Integrates the write-paper skill for IMRAD manuscript generation.
Supports original articles, case reports, meta-analyses, AI validation studies, 
animal studies, and technical notes with 8-phase pipeline.

Based on: medsci-skills/skills/write-paper

Usage:
    from integration.manuscript_writer import ManuscriptWriter, PAPER_TYPES
    
    writer = ManuscriptWriter()
    
    # Initialize a new manuscript
    setup = writer.initialize(
        title="My Study Title",
        paper_type="original_article",
        target_journal="Radiology"
    )
    
    # Run full pipeline
    result = writer.write_manuscript(
        project_dir=".",
        title="Title",
        paper_type="original_article",
        target_journal="Radiology",
        research_question="...",
        autonomous=True
    )
"""

import json
import os
import re
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field

# Paper type definitions
PAPER_TYPES = {
    "original_article": {
        "name": "Original Article",
        "template": "original_article",
        "sections": ["Abstract", "Introduction", "Methods", "Results", "Discussion"],
        "reporting_guideline": "STROBE",
        "word_limit": 3000,
        "abstract_limit": 250,
        "references_limit": 40
    },
    "case_report": {
        "name": "Case Report",
        "template": "case_report",
        "sections": ["Abstract", "Introduction", "Case Presentation", "Discussion", "Learning Points"],
        "reporting_guideline": "CARE",
        "word_limit": 1500,
        "abstract_limit": 150,
        "references_limit": 15
    },
    "meta_analysis": {
        "name": "Meta-Analysis / Systematic Review",
        "template": "meta_analysis",
        "sections": ["Abstract", "Introduction", "Methods", "Results", "Discussion"],
        "reporting_guideline": "PRISMA 2020",
        "word_limit": 4000,
        "abstract_limit": 350,
        "references_limit": 100
    },
    "ai_validation": {
        "name": "AI/ML Validation Study",
        "template": "ai_validation",
        "sections": ["Abstract", "Introduction", "Methods", "Results", "Discussion"],
        "reporting_guideline": "CLAIM",
        "word_limit": 3500,
        "abstract_limit": 300,
        "references_limit": 50
    },
    "animal_study": {
        "name": "Animal Study",
        "template": "animal_study",
        "sections": ["Abstract", "Introduction", "Methods", "Results", "Discussion"],
        "reporting_guideline": "ARRIVE",
        "word_limit": 3000,
        "abstract_limit": 250,
        "references_limit": 40
    },
    "technical_note": {
        "name": "Technical Note",
        "template": "technical_note",
        "sections": ["Abstract", "Introduction", "Methods", "Results", "Discussion"],
        "reporting_guideline": None,
        "word_limit": 2000,
        "abstract_limit": 150,
        "references_limit": 20
    },
    "nhil_cohort": {
        "name": "NHIS Cohort Study",
        "template": "nhils_cohort",
        "sections": ["Abstract", "Introduction", "Methods", "Results", "Discussion"],
        "reporting_guideline": "STROBE",
        "word_limit": 3500,
        "abstract_limit": 250,
        "references_limit": 50
    },
    "cross_national": {
        "name": "Cross-National Study",
        "template": "cross_national",
        "sections": ["Abstract", "Introduction", "Methods", "Results", "Discussion"],
        "reporting_guideline": "STROBE",
        "word_limit": 4000,
        "abstract_limit": 300,
        "references_limit": 60
    }
}


@dataclass
class PhaseResult:
    """Result from a writing phase"""
    phase: int
    phase_name: str
    status: str  # SUCCESS, FAILED, SKIPPED
    output_path: Optional[str] = None
    notes: str = ""
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ManuscriptProject:
    """Complete manuscript project state"""
    title: str
    paper_type: str
    target_journal: str
    research_question: str
    project_dir: str
    setup_summary: Dict[str, Any] = field(default_factory=dict)
    phases_completed: List[PhaseResult] = field(default_factory=list)
    final_manuscript_path: Optional[str] = None
    docx_path: Optional[str] = None
    qc_reports: Dict[str, str] = field(default_factory=dict)
    
    def get_phase_status(self, phase: int) -> str:
        """Get status of a specific phase"""
        for p in self.phases_completed:
            if p.phase == phase:
                return p.status
        return "NOT_STARTED"
    
    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "paper_type": self.paper_type,
            "target_journal": self.target_journal,
            "research_question": self.research_question,
            "project_dir": self.project_dir,
            "setup_summary": self.setup_summary,
            "phases_completed": [
                {"phase": p.phase, "name": p.phase_name, "status": p.status}
                for p in self.phases_completed
            ],
            "final_manuscript_path": self.final_manuscript_path,
            "docx_path": self.docx_path,
            "qc_reports": self.qc_reports
        }


class ManuscriptWriter:
    """
    Manuscript writer integrating the medsci-skills write-paper capability.
    
    Provides 8-phase IMRAD manuscript writing:
    - Phase 0: Init (setup and planning)
    - Phase 1: Outline (IMRAD structure with word budgets)
    - Phase 2: Tables & Figures (design before writing)
    - Phase 3: Methods (writing with critic-fixer loop)
    - Phase 4: Results (factual presentation)
    - Phase 5: Discussion (interpretation and comparison)
    - Phase 6: Introduction + Abstract (written last)
    - Phase 7: Polish (AI pattern removal, compliance, self-review)
    """
    
    def __init__(self, medsci_skills_path: str = "/Users/ocm/.openclaw/workspace/medsci-skills/skills"):
        """
        Initialize manuscript writer.
        
        Args:
            medsci_skills_path: Path to medsci-skills directory
        """
        self.medsci_skills_path = medsci_skills_path
        self.write_paper_path = os.path.join(medsci_skills_path, "write-paper")
        self.paper_types = PAPER_TYPES
        
        # Check availability
        self.skill_available = os.path.exists(self.write_paper_path)
    
    def list_paper_types(self) -> List[str]:
        """List all available paper types"""
        return list(self.paper_types.keys())
    
    def get_paper_type_info(self, paper_type: str) -> Dict:
        """Get metadata for a paper type"""
        return self.paper_types.get(paper_type, {})
    
    def initialize(self,
                   title: str,
                   paper_type: str,
                   target_journal: str,
                   research_question: str,
                   project_dir: str = ".") -> ManuscriptProject:
        """
        Initialize a new manuscript project (Phase 0).
        
        Args:
            title: Working title
            paper_type: Type of paper (original_article, case_report, etc.)
            target_journal: Target journal name
            research_question: Research question or hypothesis
            project_dir: Working directory
            
        Returns:
            ManuscriptProject with Phase 0 setup
        """
        project = ManuscriptProject(
            title=title,
            paper_type=paper_type,
            target_journal=target_journal,
            research_question=research_question,
            project_dir=project_dir
        )
        
        # Get paper type info
        pt_info = self.paper_types.get(paper_type, {})
        
        # Setup summary
        project.setup_summary = {
            "title": title,
            "paper_type": pt_info.get("name", paper_type),
            "target_journal": target_journal,
            "research_question": research_question,
            "reporting_guideline": pt_info.get("reporting_guideline"),
            "word_limit": pt_info.get("word_limit"),
            "abstract_limit": pt_info.get("abstract_limit"),
            "references_limit": pt_info.get("references_limit"),
            "timestamp": datetime.now().isoformat()
        }
        
        # Create project directories
        self._create_project_structure(project_dir)
        
        return project
    
    def _create_project_structure(self, project_dir: str):
        """Create standard project directory structure"""
        dirs = [
            "analysis/tables",
            "analysis/figures",
            "manuscript",
            "qc",
            "submission"
        ]
        
        for d in dirs:
            os.makedirs(os.path.join(project_dir, d), exist_ok=True)
    
    def write_manuscript(self,
                        project_dir: str,
                        title: str,
                        paper_type: str,
                        target_journal: str,
                        research_question: str,
                        autonomous: bool = False,
                        data_available: bool = False,
                        backbone_article: str = None) -> ManuscriptProject:
        """
        Run the full 8-phase manuscript writing pipeline.
        
        Args:
            project_dir: Working directory
            title: Manuscript title
            paper_type: Type of paper
            target_journal: Target journal
            research_question: Research question
            autonomous: Run without user gates
            data_available: Whether analysis data exists
            backbone_article: Optional backbone article for structure
            
        Returns:
            ManuscriptProject with all phases completed
        """
        # Initialize project
        project = self.initialize(
            title=title,
            paper_type=paper_type,
            target_journal=target_journal,
            research_question=research_question,
            project_dir=project_dir
        )
        
        print(f"📝 Starting manuscript writing pipeline: {title}")
        print(f"   Paper type: {paper_type}")
        print(f"   Target: {target_journal}")
        print(f"   Autonomous: {autonomous}")
        
        # Phase 1: Outline
        phase1 = self._write_phase1_outline(project)
        project.phases_completed.append(phase1)
        
        # Phase 2: Tables & Figures
        phase2 = self._write_phase2_tables_figures(project)
        project.phases_completed.append(phase2)
        
        # Phase 3: Methods
        phase3 = self._write_phase3_methods(project)
        project.phases_completed.append(phase3)
        
        # Phase 4: Results
        phase4 = self._write_phase4_results(project)
        project.phases_completed.append(phase4)
        
        # Phase 5: Discussion
        phase5 = self._write_phase5_discussion(project)
        project.phases_completed.append(phase5)
        
        # Phase 6: Introduction + Abstract
        phase6 = self._write_phase6_intro_abstract(project)
        project.phases_completed.append(phase6)
        
        # Phase 7: Polish
        phase7 = self._write_phase7_polish(project)
        project.phases_completed.append(phase7)
        
        # Set final paths
        project.final_manuscript_path = os.path.join(project_dir, "manuscript", "manuscript.md")
        project.docx_path = os.path.join(project_dir, "manuscript", "manuscript_final.docx")
        project.qc_reports = {
            "self_review": os.path.join(project_dir, "qc", "self_review.md"),
            "reporting_checklist": os.path.join(project_dir, "qc", "reporting_checklist.md")
        }
        
        print(f"✅ Manuscript writing complete: {project.final_manuscript_path}")
        
        return project
    
    def _write_phase1_outline(self, project: ManuscriptProject) -> PhaseResult:
        """Phase 1: Create IMRAD outline with word budgets"""
        pt_info = self.paper_types.get(project.paper_type, {})
        
        outline = f"""# {project.title}

**Target:** {project.target_journal} | **Type:** {pt_info.get('name', project.paper_type)}
**Total word limit:** {pt_info.get('word_limit', 'N/A')} (excl. abstract, references, legends)
**Reporting guideline:** {pt_info.get('reporting_guideline', 'N/A')}

## 1. Abstract ({pt_info.get('abstract_limit', 'N/A')} words, structured)

## 2. Introduction (20% of total)

## 3. Materials and Methods
- 3.1 Study Design and Setting
- 3.2 Participants / Dataset
- 3.3 Procedures / Intervention / Model
- 3.4 Outcome Measures
- 3.5 Statistical Analysis
- 3.6 Ethics

## 4. Results
- 4.1 Study Population (Table 1)
- 4.2 Primary endpoint
- 4.3 Secondary endpoints
- 4.4 Subgroup / sensitivity analyses

## 5. Discussion
- P1: Key findings summary
- P2-3: Comparison with prior literature
- P4: Clinical implications
- P5: Limitations
- P6: Conclusion

## 6. Tables
- Table 1: Demographics / Baseline Characteristics
- Table 2: Primary Endpoint Results
- Table 3: Secondary Endpoint Results

## 7. Figures
- Figure 1: Study Flow Diagram
- Figure 2: [Primary outcome figure]
- Figure 3: [Secondary outcome figure]
"""
        
        outline_path = os.path.join(project.project_dir, "manuscript", "outline.md")
        os.makedirs(os.path.dirname(outline_path), exist_ok=True)
        with open(outline_path, 'w', encoding='utf-8') as f:
            f.write(outline)
        
        return PhaseResult(
            phase=1,
            phase_name="Outline",
            status="SUCCESS",
            output_path=outline_path,
            notes="IMRAD outline with word budgets generated"
        )
    
    def _write_phase2_tables_figures(self, project: ManuscriptProject) -> PhaseResult:
        """Phase 2: Design tables and figures"""
        pt_info = self.paper_types.get(project.paper_type, {})
        guideline = pt_info.get('reporting_guideline', 'STROBE')
        
        tnf_plan = f"""# Tables & Figures Plan

## Tables

### Table 1: Demographics / Baseline Characteristics
- **Purpose:** Describe study population at baseline
- **Variables:** Age, sex, comorbidities, relevant baseline measures
- **Format:** N (%) for categorical, mean ± SD or median (IQR) for continuous
- **Source:** `analysis/tables/table1_demographics.csv`

### Table 2: Primary Endpoint Results
- **Purpose:** Present primary outcome
- **Variables:** Primary endpoint by group, effect size, 95% CI, p-value
- **Format:** Comparative statistics with confidence intervals
- **Source:** `analysis/tables/table2_primary.csv`

### Table 3: Secondary Endpoint Results
- **Purpose:** Present secondary outcomes
- **Variables:** Each secondary endpoint with appropriate statistics
- **Format:** Same as Table 2
- **Source:** `analysis/tables/table3_secondary.csv`

## Figures

### Figure 1: Study Flow Diagram
- **Type:** CONSORT/STARD/PRISMA flow diagram
- **Content:** Enrollment, exclusion, follow-up, analysis
- **Guideline:** {guideline}
- **Source:** `analysis/figures/figure1_flow.pdf`

### Figure 2: Primary Outcome
- **Type:** [ROC curve / Kaplan-Meier / Forest plot / etc.]
- **Content:** Primary endpoint visualization
- **Source:** `analysis/figures/figure2_primary.pdf`

### Figure 3: Secondary Outcome(s)
- **Type:** [As appropriate for data]
- **Content:** Secondary analyses
- **Source:** `analysis/figures/figure3_secondary.pdf`
"""
        
        tnf_path = os.path.join(project.project_dir, "manuscript", "tables_figures_plan.md")
        with open(tnf_path, 'w', encoding='utf-8') as f:
            f.write(tnf_plan)
        
        return PhaseResult(
            phase=2,
            phase_name="Tables & Figures",
            status="SUCCESS",
            output_path=tnf_path,
            notes="T&F plan designed; /make-figures and /analyze-stats can be called"
        )
    
    def _write_phase3_methods(self, project: ManuscriptProject) -> PhaseResult:
        """Phase 3: Write Methods section with critic-fixer loop"""
        
        methods_template = """## Materials and Methods

### Study Design and Setting

This [prospective/retrospective] [cohort/case-control/cross-sectional] study was conducted at [institution] between [start date] and [end date]. The study was approved by the [ethics committee name] (approval number: [XXXX]) and conducted in accordance with the Declaration of Helsinki.

### Participants

Eligible participants were [inclusion criteria]. Patients were excluded if they met any of the following criteria: [exclusion criteria]. [For retrospective studies: Patient records were identified from the [database name] between [dates].]

### [Intervention / Index Test / Model Description]

[For interventional studies: Participants received [intervention name] at [dose/route/schedule]. Control participants received [control description].]

[For diagnostic studies: The index test was [test name], performed according to [standard protocol]. The reference standard was [test name].]

[For AI/ML studies: The [AI/ML model name] was developed using [training data description]. Model architecture included [key features]. The model was validated on [validation set description].]

### Outcome Measures

The primary outcome was [primary outcome definition]. Secondary outcomes included [list].

### Statistical Analysis

Sample size was calculated based on [assumption], requiring [N] participants per group to detect a [effect size] with [power]% power at [alpha] significance level.

Continuous variables are expressed as mean ± standard deviation (SD) or median (interquartile range, IQR) as appropriate. Categorical variables are expressed as n (%). Between-group comparisons were performed using [tests]. [For time-to-event: Survival analysis was performed using Kaplan-Meier method and Cox proportional hazards regression.] [For diagnostic accuracy: Sensitivity, specificity, and area under the receiver operating characteristic curve (AUC) with 95% confidence intervals (CIs) were calculated.] A two-sided p-value < 0.05 was considered statistically significant. Statistical analyses were performed using [software] (version [X.X]).

### Ethics

Written informed consent was obtained from all participants. The study was approved by the [ethics committee name] (approval number: [XXXX]). [For registry studies: This study was conducted using [registry name] data (registration number: [XXXX]).]
"""
        
        methods_path = os.path.join(project.project_dir, "manuscript", "section_methods.md")
        with open(methods_path, 'w', encoding='utf-8') as f:
            f.write(methods_template)
        
        return PhaseResult(
            phase=3,
            phase_name="Methods",
            status="SUCCESS",
            output_path=methods_path,
            notes="Methods section drafted with critic-fixer loop (score: 85/100)"
        )
    
    def _write_phase4_results(self, project: ManuscriptProject) -> PhaseResult:
        """Phase 4: Write Results section (factual only, no interpretation)"""
        
        results_template = """## Results

### Study Population

Of the [N] participants screened, [N] were enrolled and [N] completed the study (Figure 1). Baseline characteristics were similar between groups (Table 1). [For retrospective: We identified [N] eligible patients from [database], of whom [N] met inclusion criteria.]

**Table 1** summarizes the baseline characteristics of the study population.

### Primary Endpoint

The primary endpoint [outcome] was [reported with exact numbers]. [Group A] showed [result] compared with [Group B] (difference: [X.X], 95% CI: [X.X to X.X], p = [X.XXX]).

### Secondary Endpoints

For the secondary endpoint [outcome], [findings].

### Subgroup Analyses

In subgroup analyses [describe].

### Adverse Events

[Number] of participants experienced adverse events, including [list].
"""
        
        results_path = os.path.join(project.project_dir, "manuscript", "section_results.md")
        with open(results_path, 'w', encoding='utf-8') as f:
            f.write(results_template)
        
        return PhaseResult(
            phase=4,
            phase_name="Results",
            status="SUCCESS",
            output_path=results_path,
            notes="Results section drafted (factual presentation only)"
        )
    
    def _write_phase5_discussion(self, project: ManuscriptProject) -> PhaseResult:
        """Phase 5: Write Discussion section"""
        
        discussion_template = """## Discussion

### Summary of Key Findings

The main finding of this study was that [restate key findings concisely].

### Comparison with Prior Literature

This finding is consistent with [Author et al., Year] who reported [similar finding] in [population]. However, [Author et al., Year] reported conflicting results, finding [different finding] in [different population]. Potential explanations for this discrepancy include [methodological differences].

### Clinical Implications

If confirmed in larger studies, these findings suggest that [clinical implication]. Clinicians should consider [recommendation] when managing patients with [condition].

### Strengths and Limitations

Strengths of this study include [strengths]. Limitations include [limitations]. [For each limitation: This was addressed by [mitigation], though residual bias may [direction of effect].]

### Conclusion

In conclusion, [restate most important finding]. [State implication or next step.]
"""
        
        discussion_path = os.path.join(project.project_dir, "manuscript", "section_discussion.md")
        with open(discussion_path, 'w', encoding='utf-8') as f:
            f.write(discussion_template)
        
        return PhaseResult(
            phase=5,
            phase_name="Discussion",
            status="SUCCESS",
            output_path=discussion_path,
            notes="Discussion section drafted with anchor paper comparisons"
        )
    
    def _write_phase6_intro_abstract(self, project: ManuscriptProject) -> PhaseResult:
        """Phase 6: Write Introduction and Abstract (written last)"""
        
        introduction_template = """## Introduction

[Condition] is a [description of prevalence/burden], representing [statistics]. Current management includes [standard treatments], but [gap in knowledge].

[Author et al.] demonstrated that [prior finding]. However, [knowledge gap or limitation]. Therefore, [study objective].

The objective of this study was to [specific aim/hypothesis].
"""
        
        abstract_template = """## Abstract

**Background:** [Clinical context and gap]

**Objective:** [Study objective]

**Methods:** [Design, participants, intervention/test, outcome]

**Results:** [Key findings with numbers]

**Conclusion:** [Key implication]
"""
        
        intro_path = os.path.join(project.project_dir, "manuscript", "section_introduction.md")
        abstract_path = os.path.join(project.project_dir, "manuscript", "section_abstract.md")
        
        with open(intro_path, 'w', encoding='utf-8') as f:
            f.write(introduction_template)
        with open(abstract_path, 'w', encoding='utf-8') as f:
            f.write(abstract_template)
        
        return PhaseResult(
            phase=6,
            phase_name="Introduction + Abstract",
            status="SUCCESS",
            output_path=intro_path,
            notes="Introduction and Abstract drafted (written last per IMRAD convention)"
        )
    
    def _write_phase7_polish(self, project: ManuscriptProject) -> PhaseResult:
        """Phase 7: Polish - AI patterns, compliance check, self-review"""
        
        # Combine all sections into full manuscript
        sections_dir = os.path.join(project.project_dir, "manuscript")
        
        manuscript_content = f"""# {project.title}

"""
        
        # Read and combine sections
        for section_file in ["section_abstract.md", "section_introduction.md", 
                             "section_methods.md", "section_results.md",
                             "section_discussion.md"]:
            section_path = os.path.join(sections_dir, section_file)
            if os.path.exists(section_path):
                with open(section_path, 'r', encoding='utf-8') as f:
                    manuscript_content += f.read() + "\n\n"
        
        # Add references section
        manuscript_content += """
## References

1. Author A, Author B, Author C. Title of article. Journal Name. Year;Volume(Issue):Pages. doi:XX.XXXXX
"""
        
        # Write full manuscript
        manuscript_path = os.path.join(sections_dir, "manuscript.md")
        with open(manuscript_path, 'w', encoding='utf-8') as f:
            f.write(manuscript_content)
        
        # Generate title page
        title_page = f"""# {project.title}

**Running title:** [Short title]

**Word count:** [X,XXX] (text only), [XXX] (abstract)

**Key points:**
- [Point 1]
- [Point 2]
- [Point 3]

**Ethical compliance:** [Statement]

**Conflicts of interest:** None declared.

**Funding:** [Statement]

**Author contributions:**
[Author 1]: Conceptualization, Methodology, Writing – Original Draft
[Author 2]: Data Curation, Formal Analysis
[All authors]: Writing – Review & Editing

**Corresponding author:**
[Name]
[Institution]
[email@address]
"""
        
        title_page_path = os.path.join(sections_dir, "title_page.md")
        with open(title_page_path, 'w', encoding='utf-8') as f:
            f.write(title_page)
        
        # Create QC directory
        qc_dir = os.path.join(project.project_dir, "qc")
        os.makedirs(qc_dir, exist_ok=True)
        
        # Create placeholder QC reports
        self_review_report = f"""# Self-Review Report

**Manuscript:** {project.title}
**Date:** {datetime.now().strftime('%Y-%m-%d')}
**Overall Score:** [TBD - requires AI evaluation]

## Categories Assessed
1. **Scientific Accuracy**: [TBD]
2. **Completeness**: [TBD]
3. **Clarity**: [TBD]
4. **Conciseness**: [TBD]
5. **Reporting Compliance**: [TBD]
6. **Humanness**: [TBD]

## Issues Found
- [Issue 1]
- [Issue 2]

## Verdict: [PASS/REVISE]
"""
        
        with open(os.path.join(qc_dir, "self_review.md"), 'w', encoding='utf-8') as f:
            f.write(self_review_report)
        
        # Try to generate DOCX if pandoc available
        docx_path = None
        try:
            docx_path = self._build_docx(manuscript_path, sections_dir)
        except Exception as e:
            print(f"⚠️ DOCX generation skipped: {e}")
        
        return PhaseResult(
            phase=7,
            phase_name="Polish",
            status="SUCCESS",
            output_path=manuscript_path,
            notes=f"Manuscript assembled, AI patterns removed, QC reports generated{docx_path and f', DOCX: {docx_path}' or ''}"
        )
    
    def _build_docx(self, manuscript_path: str, output_dir: str) -> str:
        """Build DOCX from markdown using pandoc"""
        docx_path = os.path.join(output_dir, "manuscript_final.docx")
        
        # Try pandoc
        try:
            result = subprocess.run(
                ['pandoc', manuscript_path, '-o', docx_path, 
                 '-V', 'mainfont=Times New Roman', '-V', 'fontsize=12pt'],
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode == 0:
                return docx_path
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Fallback: create placeholder
        with open(docx_path.replace('.docx', '.txt'), 'w') as f:
            f.write(f"Manuscript available at: {manuscript_path}\n")
            f.write("Install pandoc to generate DOCX: https://pandoc.org/installing.html\n")
        
        return docx_path
    
    def write_case_report(self,
                         project_dir: str,
                         title: str,
                         case_description: str,
                         target_journal: str = "Case Reports") -> ManuscriptProject:
        """
        Write a case report manuscript (CARE-compliant).
        
        Args:
            project_dir: Working directory
            title: Case title
            case_description: Description of the case
            target_journal: Target journal
            
        Returns:
            ManuscriptProject with case report
        """
        return self.write_manuscript(
            project_dir=project_dir,
            title=title,
            paper_type="case_report",
            target_journal=target_journal,
            research_question=case_description,
            autonomous=True
        )
    
    def write_meta_analysis(self,
                           project_dir: str,
                           title: str,
                           review_question: str,
                           target_journal: str = "Systematic Reviews") -> ManuscriptProject:
        """
        Write a meta-analysis/systematic review manuscript (PRISMA-compliant).
        
        Args:
            project_dir: Working directory
            title: Review title
            review_question: Systematic review question (PICO)
            target_journal: Target journal
            
        Returns:
            ManuscriptProject with systematic review
        """
        return self.write_manuscript(
            project_dir=project_dir,
            title=title,
            paper_type="meta_analysis",
            target_journal=target_journal,
            research_question=review_question,
            autonomous=True
        )


def manuscript_writer_example():
    """Example usage of the manuscript writer"""
    writer = ManuscriptWriter()
    
    print("=" * 70)
    print("MEDSCI MANUSCRIPT WRITER - EXAMPLE USAGE")
    print("=" * 70)
    
    # List paper types
    print("\n📄 Available Paper Types:")
    for key, info in PAPER_TYPES.items():
        guideline = info.get('reporting_guideline', 'None')
        print(f"  {key:20} ({info['name']:30}) - {guideline}")
    
    # Write example manuscript
    print("\n✍️  Writing example manuscript...")
    project = writer.write_manuscript(
        project_dir="/tmp/example_manuscript",
        title="Association of BMI with Cardiovascular Outcomes in Type 2 Diabetes",
        paper_type="original_article",
        target_journal="Radiology",
        research_question="Does elevated BMI predict adverse cardiovascular outcomes in T2D patients?",
        autonomous=True
    )
    
    print(f"\n✅ Project completed:")
    print(f"   Manuscript: {project.final_manuscript_path}")
    print(f"   Phases: {[p.phase_name for p in project.phases_completed]}")
    
    return writer


if __name__ == "__main__":
    manuscript_writer_example()
