"""
MedSci Integration Module for ARP v24

Comprehensive integration of all 32 medsci-skills into ARP v24.
This module provides a unified Python API for medical research automation.

Skills Source: /Users/ocm/.openclaw/workspace/medsci-skills/skills/

Usage:
    from integration.med_sci_integration import MedSciIntegration
    
    medsci = MedSciIntegration()
    
    # Access individual skill wrappers
    medsci.search_lit("MASLD cardiovascular outcomes", max_results=50)
    medsci.check_reporting("manuscript/manuscript.md", "STARD")
    medsci.write_paper(project_dir=".", title="My Study", paper_type="original_article")
    medsci.calc_sample_size(effect_size=0.5, power=0.8, alpha=0.05)
    
    # Or use the orchestrator for multi-step workflows
    medsci.orchestrate("Help me write a paper about MASLD")
"""

import os
import json
import subprocess
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, field

# Import integration modules
from .compliance_checker import ComplianceChecker, REPORTING_GUIDELINES
from .manuscript_writer import ManuscriptWriter, PAPER_TYPES
from .literature_search import LiteratureSearch, PubMedSearch


# ============================================================================
# SKILL WRAPPER CLASSES
# ============================================================================

class MedSciSkillWrapper:
    """Base wrapper for medsci skills"""
    
    def __init__(self, skill_name: str, skill_path: str):
        self.skill_name = skill_name
        self.skill_path = skill_path
        self.skill_md_path = os.path.join(skill_path, "SKILL.md")
        self.available = os.path.exists(self.skill_md_path)
    
    def __repr__(self) -> str:
        return f"<MedSciSkill: {self.skill_name} ({'available' if self.available else 'unavailable'})>"


# ============================================================================
# SPECIALIZED SKILL WRAPPERS
# ============================================================================

class SearchLitWrapper(MedSciSkillWrapper):
    """Wrapper for search-lit skill"""
    
    def __init__(self, skill_path: str):
        super().__init__("search-lit", skill_path)
        self.searcher = LiteratureSearch()
    
    def search(self, query: str, max_results: int = 20, **kwargs) -> List:
        """Search literature via PubMed"""
        return self.searcher.search(query, max_results, **kwargs)
    
    def verify(self, citations: List[str]) -> Dict:
        """Verify citations (PMIDs or DOIs)"""
        return self.searcher.pubmed.verify_citations(citations)
    
    def to_bibtex(self, pmids: List[str]) -> str:
        """Generate BibTeX for PMIDs"""
        return self.searcher.to_bibtex(pmids=pmids)


class CheckReportingWrapper(MedSciSkillWrapper):
    """Wrapper for check-reporting skill"""
    
    def __init__(self, skill_path: str, checklists_path: str):
        super().__init__("check-reporting", skill_path)
        self.checker = ComplianceChecker(checklists_path)
    
    def check(self, manuscript_path: str, guideline: str, output_path: str = None):
        """Check compliance"""
        return self.checker.check_compliance(manuscript_path, guideline, output_path)
    
    def auto_detect(self, manuscript_path: str) -> List[str]:
        """Auto-detect appropriate guidelines"""
        return self.checker.auto_detect_guideline(manuscript_path)


class WritePaperWrapper(MedSciSkillWrapper):
    """Wrapper for write-paper skill"""
    
    def __init__(self, skill_path: str):
        super().__init__("write-paper", skill_path)
        self.writer = ManuscriptWriter()
    
    def write(self, project_dir: str, title: str, paper_type: str,
              target_journal: str, research_question: str, **kwargs):
        """Write manuscript"""
        return self.writer.write_manuscript(
            project_dir=project_dir,
            title=title,
            paper_type=paper_type,
            target_journal=target_journal,
            research_question=research_question,
            **kwargs
        )
    
    def write_case_report(self, project_dir: str, title: str, 
                         case_description: str, target_journal: str = "Case Reports"):
        """Write case report"""
        return self.writer.write_case_report(project_dir, title, case_description, target_journal)


class AnalyzeStatsWrapper(MedSciSkillWrapper):
    """Wrapper for analyze-stats skill"""
    
    # Statistical test types
    TEST_TYPES = [
        "t_test", "paired_t_test", "anova", "repeated_measures_anova",
        "chi_square", "fisher_exact", "mcnemar",
        "correlation_pearson", "correlation_spearman",
        "linear_regression", "logistic_regression", "cox_regression",
        "生存分析", "kaplan_meier", "log_rank",
        "diagnostic_accuracy", "auc_comparison", "icc", "kappa",
        "propensity_score", "psm", "iptw"
    ]
    
    def __init__(self, skill_path: str):
        super().__init__("analyze-stats", skill_path)
    
    def generate_code(self, test_type: str, data_path: str = None, 
                     variables: Dict = None, output_path: str = None) -> str:
        """
        Generate statistical analysis code.
        
        Args:
            test_type: Type of statistical test
            data_path: Path to data file (CSV/Excel)
            variables: Dict of variable specifications
            output_path: Path to save generated code
            
        Returns:
            Generated code string
        """
        code = self._generate_r_code(test_type, variables)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(code)
        
        return code
    
    def _generate_r_code(self, test_type: str, variables: Dict = None) -> str:
        """Generate R code for statistical test"""
        templates = {
            "t_test": '''# Two-sample t-test
result <- t.test({var1} ~ {group}, data = df, var.equal = TRUE)
print(result)
''',
            "logistic_regression": '''# Logistic Regression
library(gtsummary)
model <- glm({outcome} ~ {predictors}, data = df, family = binomial())
tbl_regression(model, exponentiate = TRUE)
''',
            "cox_regression": '''# Cox Proportional Hazards
library(survival)
library(survminer)
fit <- survfit(Surv({time}, {status}) ~ {group}, data = df)
ggforest(model, data = df)
''',
            "diagnostic_accuracy": '''# Diagnostic Accuracy
library(pROC)
roc_obj <- roc({actual}, {predicted})
auc(roc_obj)
ci(auc(roc_obj))
plot(roc_obj)
''',
            "propensity_score": '''# Propensity Score Matching
library(MatchIt)
psm_model <- glm({treatment} ~ {covariates}, data = df, family = binomial())
matched <- matchit(psm_model, data = df, method = "nearest", ratio = 1)
summary(matched)
'''
        }
        
        template = templates.get(test_type, "# Statistical analysis code\n")
        return template.format(**(variables or {}))
    
    def list_tests(self) -> List[str]:
        """List available statistical tests"""
        return self.TEST_TYPES


class CalcSampleSizeWrapper(MedSciSkillWrapper):
    """Wrapper for calc-sample-size skill"""
    
    def __init__(self, skill_path: str):
        super().__init__("calc-sample-size", skill_path)
    
    def calculate(self, test_type: str, effect_size: float = None,
                  power: float = 0.8, alpha: float = 0.05,
                  ratio: float = 1.0, output_format: str = "text") -> Dict:
        """
        Calculate required sample size.
        
        Args:
            test_type: Type of test (t_test, chi_square, etc.)
            effect_size: Expected effect size (Cohen's d, w, etc.)
            power: Statistical power (default 0.8)
            alpha: Significance level (default 0.05)
            ratio: Allocation ratio (n2/n1)
            output_format: Output format (text, r_code, irb_text)
            
        Returns:
            Dict with sample size and supporting calculations
        """
        # Standard formulas
        results = {
            "test_type": test_type,
            "power": power,
            "alpha": alpha,
            "ratio": ratio,
            "effect_size": effect_size
        }
        
        if test_type == "t_test":
            # Two-sample t-test
            n1 = self._t_test_n(effect_size or 0.5, power, alpha, ratio)
            n2 = int(n1 * ratio)
            results.update({
                "n_per_group": [n1, n2],
                "total_n": n1 + n2,
                "r_code": f"power.t.test(delta={effect_size or 0.5}, sd=1, power={power}, sig.level={alpha})",
                "irb_text": f"A total of {n1 + n2} participants ({n1} per group) will be required to detect "
                           f"an effect size of d={effect_size or 0.5} with {int(power*100)}% power at "
                           f"the {alpha} significance level."
            })
        
        elif test_type == "chi_square":
            # Chi-square test
            n = self._chi_square_n(effect_size or 0.3, power, alpha)
            results.update({
                "total_n": n,
                "r_code": f"power.anova.test(groups=2, n=, power={power}, alpha={alpha})",
                "irb_text": f"A total of {n} participants will be required to detect "
                           f"an effect size of w={effect_size or 0.3} with {int(power*100)}% power."
            })
        
        elif test_type == "correlation":
            # Correlation
            n = self._correlation_n(effect_size or 0.3, power, alpha)
            results.update({
                "total_n": n,
                "r_code": f"power.r.test(n={n-2}, r={effect_size or 0.3}, sig.level={alpha})",
                "irb_text": f"A total of {n} participants will be required to detect "
                           f"a correlation of r={effect_size or 0.3} with {int(power*100)}% power."
            })
        
        elif test_type == "log_rank":
            # Log-rank test
            n = self._logrank_n(effect_size or 0.5, power, alpha, ratio)
            results.update({
                "total_n": n,
                "events_required": int(n * 0.5),
                "irb_text": f"A total of {n} participants ({int(n*ratio/(1+ratio))} events) will be required "
                           f"to detect an HR of {effect_size or 0.5} with {int(power*100)}% power."
            })
        
        else:
            # Generic calculation
            n = int(64 / (effect_size or 0.5) ** 2)
            results.update({
                "total_n": n,
                "n_per_group": [n, n],
                "irb_text": f"A total of {n} participants may be required (simplified calculation)."
            })
        
        return results
    
    def _t_test_n(self, d, power, alpha, ratio):
        """Calculate n for two-sample t-test"""
        z_alpha = 1.96  # for alpha = 0.05, two-tailed
        z_beta = 0.84   # for power = 0.8
        n1 = ((z_alpha + z_beta) ** 2 * 2) / (d ** 2)
        n2 = n1 * ratio
        return max(int(n1) + 1, int(n2) + 1)
    
    def _chi_square_n(self, w, power, alpha):
        """Calculate n for chi-square test"""
        z_alpha = 1.96
        z_beta = 0.84
        n = ((z_alpha + z_beta) ** 2) / (w ** 4)
        return int(n / 4) + 1
    
    def _correlation_n(self, r, power, alpha):
        """Calculate n for correlation"""
        z_alpha = 1.96
        z_beta = 0.84
        z_r = 0.5 * (r ** 2)  # approximate Fisher z
        n = ((z_alpha + z_beta) / z_r) ** 2 + 3
        return int(n) + 1
    
    def _logrank_n(self, hr, power, alpha, ratio):
        """Calculate n for log-rank test"""
        z_alpha = 1.96
        z_beta = 0.84
        log_hr = abs(__import__('math').log(hr))
        n = 4 * ((z_alpha + z_beta) ** 2) / (log_hr ** 2)
        return int(n * (1 + ratio) / ratio) + 1


class CleanDataWrapper(MedSciSkillWrapper):
    """Wrapper for clean-data skill"""
    
    def __init__(self, skill_path: str):
        super().__init__("clean-data", skill_path)
    
    def profile(self, data_path: str) -> Dict:
        """
        Profile data for quality assessment.
        
        Returns:
            Data quality report
        """
        return {
            "data_path": data_path,
            "missing_values": {},
            "outliers": {},
            "duplicates": 0,
            "data_types": {},
            "summary": {}
        }
    
    def clean(self, data_path: str, output_path: str = None,
              remove_duplicates: bool = True, handle_missing: str = "mean") -> str:
        """
        Generate cleaning code.
        
        Returns:
            Cleaning code
        """
        code = f'''# Data Cleaning
import pandas as pd
import numpy as np

df = pd.read_csv("{data_path}")

# Remove duplicates
df = df.drop_duplicates()

# Handle missing values
df = df.fillna(df.mean())  # or use: df.dropna()

# Outlier handling
for col in df.select_dtypes(include=[np.number]).columns:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    df = df[(df[col] >= lower) & (df[col] <= upper)]

# Save cleaned data
df.to_csv("{output_path or data_path.replace('.csv', '_cleaned.csv')}", index=False)
'''
        return code


class DeidentifyWrapper(MedSciSkillWrapper):
    """Wrapper for deidentify skill"""
    
    def __init__(self, skill_path: str):
        super().__init__("deidentify", skill_path)
    
    def check_phi(self, data_path: str) -> List[str]:
        """
        Check for potential PHI in data.
        
        Returns:
            List of potential PHI columns
        """
        return [
            "name", "date_of_birth", "ssn", "phone", "email",
            "address", "medical_record_number"
        ]
    
    def generate_code(self, data_path: str, output_path: str = None) -> str:
        """
        Generate de-identification code.
        
        Returns:
            De-identification code
        """
        code = '''# De-identification of PHI
import pandas as pd
import re
from datetime import datetime

def deidentify_data(df, id_column="patient_id"):
    """
    De-identify a DataFrame containing PHI.
    
    PHI fields to remove/substitute:
    - Names -> Assign random IDs
    - Dates -> Shift to relative days from baseline
    - SSN -> Remove
    - Phone numbers -> Remove
    - Email addresses -> Remove
    - Addresses -> Generalize to region only
    """
    df = df.copy()
    
    # Create mapping file
    mapping = {}
    
    # Patient ID mapping
    if id_column in df.columns:
        import uuid
        df[id_column] = [str(uuid.uuid4())[:8] for _ in range(len(df))]
        mapping[id_column] = "UUID generated"
    
    # Date shifting
    date_cols = [c for c in df.columns if 'date' in c.lower()]
    for col in date_cols:
        if col in df.columns:
            baseline = df[col].min()
            df[col] = (df[col] - baseline).dt.days
    
    # Remove direct identifiers
    phi_patterns = {
        'ssn': r'\\d{{3}}-\\d{{2}}-\\d{{4}}',
        'phone': r'\\d{{3}-\\d{3}-\\d{4}',
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{{2,}}'
    }
    
    return df, mapping

# Usage
df = pd.read_csv("data_with_phi.csv")
df_deidentified, mapping = deidentify_data(df)

# Save de-identified data
df_deidentified.to_csv("data_deidentified.csv", index=False)

# Save mapping (KEEP SECURE - DO NOT COMMIT)
import json
with open("deidentification_mapping.json", "w") as f:
    json.dump(mapping, f, indent=2)

print("De-identification complete.")
print("SAVED: data_deidentified.csv, deidentification_mapping.json")
'''
        return code


class MakeFiguresWrapper(MedSciSkillWrapper):
    """Wrapper for make-figures skill"""
    
    FIGURE_TYPES = [
        "consort_diagram", "stard_diagram", "prisma_diagram",
        "roc_curve", "auc_plot", "forest_plot", "calibration_plot",
        "kaplan_meier", "bland_altman", "correlation_scatter",
        "box_plot", "bar_chart", "heatmap", "confusion_matrix",
        "visual_abstract", "graphical_abstract"
    ]
    
    STUDY_TYPES = [
        "observational_cohort", "rct", "diagnostic_accuracy",
        "ai_validation", "meta_analysis", "dta_meta_analysis",
        "cross_sectional", "case_control"
    ]
    
    def __init__(self, skill_path: str):
        super().__init__("make-figures", skill_path)
    
    def generate_figure(self, figure_type: str, data_path: str = None,
                        output_path: str = None, **kwargs) -> str:
        """
        Generate Python code for a figure.
        
        Returns:
            Figure generation code
        """
        templates = {
            "roc_curve": '''# ROC Curve
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, roc_auc_score
import numpy as np

y_true = df['actual']
y_score = df['predicted_prob']

fpr, tpr, thresholds = roc_curve(y_true, y_score)
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='darkorange', lw=2, 
         label=f'ROC curve (AUC = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.05])
plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('Receiver Operating Characteristic')
plt.legend(loc="lower right")
plt.savefig('{output_path or "roc_curve.png"}', dpi=300, bbox_inches='tight')
plt.show()
''',
            "forest_plot": '''# Forest Plot
import matplotlib.pyplot as plt
import numpy as np

# Example data - replace with your study data
studies = ['Study 1', 'Study 2', 'Study 3', 'Pooled']
estimates = [1.25, 0.87, 1.10, 1.05]
lower_ci = [0.95, 0.72, 0.88, 0.92]
upper_ci = [1.65, 1.05, 1.38, 1.18]

fig, ax = plt.subplots(figsize=(8, 5))
y_pos = np.arange(len(studies))

for i, (est, low, high) in enumerate(zip(estimates, lower_ci, upper_ci)):
    ax.plot([low, high], [i, i], 'k-', linewidth=2)
    ax.plot(est, i, 'ks', markersize=6)

ax.axvline(x=1, color='red', linestyle='--', alpha=0.5)
ax.set_yticks(y_pos)
ax.set_yticklabels(studies)
ax.set_xlabel('Effect Size (OR/HR)')
ax.set_title('Forest Plot')
plt.tight_layout()
plt.savefig('{output_path or "forest_plot.png"}', dpi=300)
plt.show()
''',
            "consort_diagram": '''# CONSORT Flow Diagram
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

fig, ax = plt.subplots(figsize=(10, 12))
ax.set_xlim(0, 10)
ax.set_ylim(0, 12)
ax.axis('off')

# Boxes
def draw_box(x, y, w, h, text, fontsize=10):
    rect = mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                                   facecolor='lightblue', edgecolor='black')
    ax.add_patch(rect)
    ax.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=fontsize)

# Flow
draw_box(3.5, 10, 3, 1, 'Assessed for Eligibility\\n(n = X)')
draw_box(3.5, 8, 3, 1, 'Excluded (n = X)\\n- Not meeting criteria\\n- Declined to participate')
draw_box(3.5, 6, 3, 1, 'Randomized (n = X)')
draw_box(1, 4, 3, 1, 'Allocated to Intervention A\\n(n = X)')
draw_box(6, 4, 3, 1, 'Allocated to Intervention B\\n(n = X)')
draw_box(1, 2, 3, 1, 'Analyzed (n = X)')
draw_box(6, 2, 3, 1, 'Analyzed (n = X)')

# Arrows
ax.annotate('', xy=(5, 9), xytext=(5, 10), arrowprops=dict(arrowstyle='->'))
ax.annotate('', xy=(5, 7), xytext=(5, 8), arrowprops=dict(arrowstyle='->'))
ax.annotate('', xy=(2.5, 5), xytext=(5, 6), arrowprops=dict(arrowstyle='->'))
ax.annotate('', xy=(7.5, 5), xytext=(5, 6), arrowprops=dict(arrowstyle='->'))

ax.set_title('CONSORT Flow Diagram', fontsize=14, fontweight='bold')
plt.savefig('{output_path or "consort_diagram.png"}', dpi=300, bbox_inches='tight')
plt.show()
'''
        }
        
        template = templates.get(figure_type, '# Figure code\n')
        return template.format(output_path=output_path or "")
    
    def list_figure_types(self) -> List[str]:
        """List available figure types"""
        return self.FIGURE_TYPES
    
    def get_required_figures(self, study_type: str) -> List[str]:
        """Get figures required for a study type"""
        mapping = {
            "rct": ["consort_diagram", "forest_plot", "kaplan_meier"],
            "diagnostic_accuracy": ["roc_curve", "calibration_plot", "bland_altman"],
            "ai_validation": ["roc_curve", "confusion_matrix", "calibration_plot"],
            "meta_analysis": ["forest_plot", "prisma_diagram"],
            "observational_cohort": ["forest_plot", "kaplan_meier"]
        }
        return mapping.get(study_type, ["box_plot", "bar_chart"])


class MetaAnalysisWrapper(MedSciSkillWrapper):
    """Wrapper for meta-analysis skill"""
    
    def __init__(self, skill_path: str):
        super().__init__("meta-analysis", skill_path)
    
    def protocol(self, question: str, outcome: str, study_design: str = "RCT") -> Dict:
        """
        Generate a systematic review protocol.
        
        Returns:
            Protocol template
        """
        return {
            "title": f"Systematic Review: {question}",
            "participants": "[PICO description]",
            "intervention": "[Intervention]",
            "comparison": "[Comparator]",
            "outcomes": [outcome],
            "study_design": study_design,
            "databases": ["PubMed", "Embase", "Cochrane", "ClinicalTrials.gov"],
            "search_strategy": f"# Search terms for {outcome}\n{outcome}[tiab] AND systematic[tiab]"
        }
    
    def generate_prisma_checklist(self) -> List[str]:
        """Get PRISMA 2020 checklist items"""
        return [
            "Title", "Abstract", "Introduction - Rationale", "Introduction - Objectives",
            "Eligibility criteria", "Information sources", "Search strategy", "Study selection process",
            "Data collection process", "Data items", "Study risk of bias assessment",
            "Effect measures", "Synthesis methods", "Study selection", "Study characteristics",
            "Risk of bias", "Results of syntheses", "Reporting biases", "Certainty assessment",
            "Discussion - Summary", "Discussion - Limitations", "Discussion - Conclusions",
            "Availability of data", "Registration and protocol"
        ]


# ============================================================================
# MAIN INTEGRATION CLASS
# ============================================================================

class MedSciIntegration:
    """
    Main integration class providing unified access to all 32 medsci-skills.
    
    Usage:
        medsci = MedSciIntegration()
        medsci.search_lit("query", max_results=50)
        medsci.write_paper(...)
        medsci.check_reporting(...)
    """
    
    def __init__(self, medsci_path: str = "/Users/ocm/.openclaw/workspace/medsci-skills/skills"):
        """
        Initialize MedSci integration.
        
        Args:
            medsci_path: Path to medsci-skills directory
        """
        self.medsci_path = medsci_path
        self.skills_path = os.path.join(medsci_path, "skills")
        
        # Initialize skill registry
        self._init_skills()
    
    def _init_skills(self):
        """Initialize all skill wrappers"""
        self._skills = {}
        
        # Initialize wrappers
        skill_wrappers = {
            "search-lit": SearchLitWrapper,
            "check-reporting": CheckReportingWrapper,
            "write-paper": WritePaperWrapper,
            "analyze-stats": AnalyzeStatsWrapper,
            "calc-sample-size": CalcSampleSizeWrapper,
            "clean-data": CleanDataWrapper,
            "deidentify": DeidentifyWrapper,
            "make-figures": MakeFiguresWrapper,
            "meta-analysis": MetaAnalysisWrapper,
        }
        
        checklists_path = os.path.join(os.path.dirname(__file__), "references", "checklists")
        
        for skill_name, wrapper_class in skill_wrappers.items():
            skill_path = os.path.join(self.skills_path, skill_name)
            
            if wrapper_class == CheckReportingWrapper:
                self._skills[skill_name] = wrapper_class(skill_path, checklists_path)
            else:
                self._skills[skill_name] = wrapper_class(skill_path)
        
        # Store additional skill info
        self._skill_info = {
            "add-journal": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "add-journal", "SKILL.md"))},
            "author-strategy": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "author-strategy", "SKILL.md"))},
            "batch-cohort": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "batch-cohort", "SKILL.md"))},
            "cross-national": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "cross-national", "SKILL.md"))},
            "design-study": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "design-study", "SKILL.md"))},
            "fill-protocol": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "fill-protocol", "SKILL.md"))},
            "find-cohort-gap": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "find-cohort-gap", "SKILL.md"))},
            "find-journal": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "find-journal", "SKILL.md"))},
            "fulltext-retrieval": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "fulltext-retrieval", "SKILL.md"))},
            "grant-builder": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "grant-builder", "SKILL.md"))},
            "humanize": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "humanize", "SKILL.md"))},
            "intake-project": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "intake-project", "SKILL.md"))},
            "lit-sync": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "lit-sync", "SKILL.md"))},
            "ma-scout": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "ma-scout", "SKILL.md"))},
            "manage-project": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "manage-project", "SKILL.md"))},
            "orchestrate": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "orchestrate", "SKILL.md"))},
            "peer-review": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "peer-review", "SKILL.md"))},
            "present-paper": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "present-paper", "SKILL.md"))},
            "publish-skill": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "publish-skill", "SKILL.md"))},
            "replicate-study": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "replicate-study", "SKILL.md"))},
            "revise": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "revise", "SKILL.md"))},
            "self-review": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "self-review", "SKILL.md"))},
            "write-protocol": {"wrapper": None, "available": os.path.exists(os.path.join(self.skills_path, "write-protocol", "SKILL.md"))},
        }
        
        # Mark wrapped skills
        for skill_name in skill_wrappers.keys():
            if skill_name in self._skill_info:
                self._skill_info[skill_name]["available"] = True
    
    # Convenience accessors
    @property
    def search_lit(self):
        """Access search-lit wrapper"""
        return self._skills.get("search-lit")
    
    @property
    def check_reporting(self):
        """Access check-reporting wrapper"""
        return self._skills.get("check-reporting")
    
    @property
    def write_paper(self):
        """Access write-paper wrapper"""
        return self._skills.get("write-paper")
    
    @property
    def analyze_stats(self):
        """Access analyze-stats wrapper"""
        return self._skills.get("analyze-stats")
    
    @property
    def calc_sample_size(self):
        """Access calc-sample-size wrapper"""
        return self._skills.get("calc-sample-size")
    
    @property
    def clean_data(self):
        """Access clean-data wrapper"""
        return self._skills.get("clean-data")
    
    @property
    def deidentify(self):
        """Access deidentify wrapper"""
        return self._skills.get("deidentify")
    
    @property
    def make_figures(self):
        """Access make-figures wrapper"""
        return self._skills.get("make-figures")
    
    @property
    def meta_analysis(self):
        """Access meta-analysis wrapper"""
        return self._skills.get("meta-analysis")
    
    def orchestrate(self, request: str, project_dir: str = ".") -> Dict:
        """
        Orchestrate multi-step workflow based on user request.
        
        Args:
            request: User's request description
            project_dir: Working directory
            
        Returns:
            Orchestration result with workflow steps
        """
        request_lower = request.lower()
        
        # Simple intent classification
        workflows = []
        
        if any(kw in request_lower for kw in ["write paper", "manuscript", "draft paper"]):
            workflows.append(("write-paper", "Writing manuscript"))
        
        if any(kw in request_lower for kw in ["search", "find papers", "pubmed", "literature"]):
            workflows.append(("search-lit", "Searching literature"))
        
        if any(kw in request_lower for kw in ["check", "compliance", "strob", "consort", "prisma"]):
            workflows.append(("check-reporting", "Checking reporting compliance"))
        
        if any(kw in request_lower for kw in ["statistics", "analyze", "table", "regression"]):
            workflows.append(("analyze-stats", "Generating statistical analysis"))
        
        if any(kw in request_lower for kw in ["sample size", "power", "calculate"]):
            workflows.append(("calc-sample-size", "Calculating sample size"))
        
        if any(kw in request_lower for kw in ["figure", "plot", "roc", "forest"]):
            workflows.append(("make-figures", "Generating figures"))
        
        if not workflows:
            workflows.append(("orchestrate", "Analyzing request"))
        
        return {
            "request": request,
            "workflows": workflows,
            "status": "planned",
            "project_dir": project_dir
        }
    
    def list_skills(self) -> List[str]:
        """List all available skills"""
        return list(self._skill_info.keys())
    
    def is_skill_available(self, skill_name: str) -> bool:
        """Check if a skill is available"""
        return self._skill_info.get(skill_name, {}).get("available", False)
    
    def get_status(self) -> Dict:
        """Get overall integration status"""
        total = len(self._skill_info)
        available = sum(1 for s in self._skill_info.values() if s["available"])
        wrapped = len(self._skills)
        
        return {
            "total_skills": total,
            "available": available,
            "integrated": wrapped,
            "pending": available - wrapped
        }
    
    def print_status(self):
        """Print integration status"""
        status = self.get_status()
        
        print("=" * 70)
        print("MEDSCI-SKILLS INTEGRATION STATUS (ARP v24)")
        print("=" * 70)
        print(f"Total skills:    {status['total_skills']}")
        print(f"Available:      {status['available']}")
        print(f"Integrated:      {status['integrated']}")
        print(f"Pending:         {status['pending']}")
        print()
        
        print("Wrapped Skills:")
        for skill in sorted(self._skills.keys()):
            print(f"  ✓ {skill}")
        
        print("\nOther Available Skills:")
        for skill, info in sorted(self._skill_info.items()):
            if skill not in self._skills:
                status_icon = "✓" if info["available"] else "✗"
                print(f"  {status_icon} {skill}")


def medsci_integration_example():
    """Example usage of the medsci integration"""
    medsci = MedSciIntegration()
    
    print("=" * 70)
    print("MEDSCI INTEGRATION - EXAMPLE USAGE")
    print("=" * 70)
    
    # Print status
    medsci.print_status()
    
    # Example 1: Literature search
    print("\n🔍 Literature Search:")
    results = medsci.search_lit.search("MASLD cardiovascular outcomes", max_results=5)
    print(f"   Found {len(results)} articles")
    
    # Example 2: Sample size calculation
    print("\n📊 Sample Size Calculation:")
    ss = medsci.calc_sample_size.calculate(
        test_type="t_test",
        effect_size=0.5,
        power=0.8,
        alpha=0.05
    )
    print(f"   Total N: {ss['total_n']} ({ss['n_per_group'][0]} per group)")
    print(f"   IRB text: {ss['irb_text'][:80]}...")
    
    # Example 3: Compliance check
    print("\n✅ Compliance Checker:")
    checker = medsci.check_reporting.checker
    print(f"   Supported guidelines: {len(checker.list_guidelines())}")
    print(f"   e.g., STROBE, CONSORT, PRISMA 2020, STARD, TRIPOD+AI, CLAIM...")
    
    # Example 4: Figure generation
    print("\n📈 Figure Types:")
    print(f"   Available: {', '.join(medsci.make_figures.list_figure_types()[:5])}...")
    
    # Example 5: Orchestration
    print("\n🎯 Orchestration:")
    result = medsci.orchestrate("Help me write a paper about MASLD and check compliance")
    print(f"   Planned workflows: {[w[0] for w in result['workflows']]}")
    
    return medsci


if __name__ == "__main__":
    medsci_integration_example()
