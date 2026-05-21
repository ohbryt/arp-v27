"""
MedSci Compliance Checker for ARP v24

Integrates the check-reporting skill for medical research reporting guideline compliance.
Supports 33 reporting guidelines including STROBE, CONSORT, PRISMA 2020, STARD, TRIPOD, and more.

Based on: medsci-skills/skills/check-reporting

Usage:
    from integration.compliance_checker import ComplianceChecker, REPORTING_GUIDELINES
    
    checker = ComplianceChecker()
    
    # Check STROBE compliance
    report = checker.check_compliance(
        manuscript_path="manuscript/manuscript.md",
        guideline="STROBE",
        output_path="qc/reporting_checklist.md"
    )
    
    # Check multiple guidelines
    multi_report = checker.check_multiple_guidelines(
        manuscript_path="manuscript/manuscript.md",
        guidelines=["STARD", "STARD-AI"]
    )
"""

import json
import os
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

# Path constants
MEDSCI_CHECK_REPORTING = "/Users/ocm/.openclaw/workspace/medsci-skills/skills/check-reporting"
CHECKLISTS_PATH = os.path.join(os.path.dirname(__file__), "references", "checklists")


class GuidelineType(Enum):
    """Types of reporting guidelines"""
    OBSERVATIONAL = "observational"
    RCT = "rct"
    DIAGNOSTIC = "diagnostic"
    PREDICTION = "prediction"
    SYSTEMATIC_REVIEW = "systematic_review"
    META_ANALYSIS = "meta_analysis"
    ANIMAL = "animal"
    CASE_REPORT = "case_report"
    PROTOCOL = "protocol"
    QUALITY = "quality"
    RISK_OF_BIAS = "risk_of_bias"
    RADIOMICS = "radiomics"
    CROSS_NATIONAL = "cross_national"
    NHIS_COHORT = "nhis_cohort"


# Supported guidelines with metadata
REPORTING_GUIDELINES = {
    # Primary guidelines
    "STROBE": {
        "name": "STROBE",
        "full_name": "Strengthening the Reporting of Observational Studies in Epidemiology",
        "type": GuidelineType.OBSERVATIONAL,
        "version": "2007",
        "items": 22,
        "file": "STROBE.md",
        "description": "Observational studies (cohort, case-control, cross-sectional)"
    },
    "CONSORT": {
        "name": "CONSORT",
        "full_name": "Consolidated Standards of Reporting Trials",
        "type": GuidelineType.RCT,
        "version": "2010",
        "items": 25,
        "file": "CONSORT.md",
        "description": "Randomized controlled trials"
    },
    "STARD": {
        "name": "STARD",
        "full_name": "Standards for Reporting Diagnostic Accuracy",
        "type": GuidelineType.DIAGNOSTIC,
        "version": "2015",
        "items": 30,
        "file": "STARD.md",
        "description": "Diagnostic accuracy studies"
    },
    "STARD-AI": {
        "name": "STARD-AI",
        "full_name": "STARD for AI Diagnostic Accuracy Studies",
        "type": GuidelineType.DIAGNOSTIC,
        "version": "2025",
        "items": 40,
        "file": "STARD_AI.md",
        "description": "AI diagnostic accuracy studies"
    },
    "TRIPOD": {
        "name": "TRIPOD",
        "full_name": "Transparent Reporting of a Multivariable Prediction Model for Individual Prognosis or Diagnosis",
        "type": GuidelineType.PREDICTION,
        "version": "2015",
        "items": 22,
        "file": "TRIPOD.md",
        "description": "Prediction models (classic, non-AI)"
    },
    "TRIPOD-AI": {
        "name": "TRIPOD+AI",
        "full_name": "TRIPOD for AI/ML Prediction Models",
        "type": GuidelineType.PREDICTION,
        "version": "2024",
        "items": 50,
        "file": "TRIPOD_AI.md",
        "description": "AI/ML prediction models"
    },
    "PRISMA 2020": {
        "name": "PRISMA 2020",
        "full_name": "Preferred Reporting Items for Systematic Reviews and Meta-Analyses",
        "type": GuidelineType.SYSTEMATIC_REVIEW,
        "version": "2020",
        "items": 27,
        "file": "PRISMA_2020.md",
        "description": "Systematic reviews and meta-analyses"
    },
    "PRISMA-DTA": {
        "name": "PRISMA-DTA",
        "full_name": "PRISMA for Diagnostic Test Accuracy Reviews",
        "type": GuidelineType.SYSTEMATIC_REVIEW,
        "version": "2018",
        "items": 44,
        "file": "PRISMA_DTA.md",
        "description": "DTA systematic reviews"
    },
    "PRISMA-P": {
        "name": "PRISMA-P",
        "full_name": "PRISMA for Protocols",
        "type": GuidelineType.PROTOCOL,
        "version": "2015",
        "items": 17,
        "file": "PRISMA_P.md",
        "description": "Systematic review protocols"
    },
    "ARRIVE": {
        "name": "ARRIVE 2.0",
        "full_name": "Animal Research: Reporting of In Vivo Experiments",
        "type": GuidelineType.ANIMAL,
        "version": "2020",
        "items": 27,
        "file": "ARRIVE_2.md",
        "description": "Animal studies"
    },
    "CARE": {
        "name": "CARE",
        "full_name": "Consensus-based Clinical Case Reporting Guideline",
        "type": GuidelineType.CASE_REPORT,
        "version": "2016",
        "items": 13,
        "file": "CARE.md",
        "description": "Case reports"
    },
    "SPIRIT": {
        "name": "SPIRIT",
        "full_name": "Standard Protocol Items: Recommendations for Interventional Trials",
        "type": GuidelineType.PROTOCOL,
        "version": "2013",
        "items": 33,
        "file": "SPIRIT.md",
        "description": "Study protocols"
    },
    "CLAIM": {
        "name": "CLAIM 2024",
        "full_name": "Checklist for AI in Medical Imaging",
        "type": GuidelineType.DIAGNOSTIC,
        "version": "2024",
        "items": 44,
        "file": "CLAIM_2024.md",
        "description": "AI/ML in clinical imaging"
    },
    "SQUIRE": {
        "name": "SQUIRE 2.0",
        "full_name": "Standards for Quality Improvement Reporting Excellence",
        "type": GuidelineType.QUALITY,
        "version": "2016",
        "items": 18,
        "file": "SQUIRE_2.md",
        "description": "Quality improvement / educational studies"
    },
    "CLEAR": {
        "name": "CLEAR",
        "full_name": "Checklist for Radiomics Reports",
        "type": GuidelineType.RADIOMICS,
        "version": "2023",
        "items": 30,
        "file": "CLEAR.md",
        "description": "Radiomics studies"
    },
    "MOOSE": {
        "name": "MOOSE",
        "full_name": "Meta-analysis of Observational Studies in Epidemiology",
        "type": GuidelineType.META_ANALYSIS,
        "version": "2000",
        "items": 35,
        "file": "MOOSE.md",
        "description": "Meta-analysis of observational studies"
    },
    "GRRAS": {
        "name": "GRRAS",
        "full_name": "Guidelines for Reporting Reliability and Agreement Studies",
        "type": GuidelineType.QUALITY,
        "version": "2011",
        "items": 15,
        "file": "GRRAS.md",
        "description": "Reliability and agreement studies"
    },
    "SWiM": {
        "name": "SWiM",
        "full_name": "Synthesis Without Meta-analysis",
        "type": GuidelineType.SYSTEMATIC_REVIEW,
        "version": "2020",
        "items": 9,
        "file": "SWiM.md",
        "description": "Synthesis without meta-analysis"
    },
    "AMSTAR2": {
        "name": "AMSTAR 2",
        "full_name": "A MeaSurement Tool to Assess systematic Reviews",
        "type": GuidelineType.RISK_OF_BIAS,
        "version": "2017",
        "items": 16,
        "file": "AMSTAR2.md",
        "description": "Quality of systematic reviews"
    },
    # Risk of bias tools
    "QUADAS-2": {
        "name": "QUADAS-2",
        "full_name": "Quality Assessment of Diagnostic Accuracy Studies",
        "type": GuidelineType.RISK_OF_BIAS,
        "version": "2011",
        "items": 4,
        "file": "QUADAS2.md",
        "description": "DTA risk of bias"
    },
    "QUADAS-C": {
        "name": "QUADAS-C",
        "full_name": "QUADAS-2 Comparative",
        "type": GuidelineType.RISK_OF_BIAS,
        "version": "2021",
        "items": 8,
        "file": "QUADAS_C.md",
        "description": "Comparative DTA risk of bias"
    },
    "RoB2": {
        "name": "RoB 2",
        "full_name": "Risk of Bias 2",
        "type": GuidelineType.RISK_OF_BIAS,
        "version": "2019",
        "items": 5,
        "file": "RoB2.md",
        "description": "RCT risk of bias"
    },
    "ROBINS-I": {
        "name": "ROBINS-I",
        "full_name": "Risk of Bias in Non-randomized Studies of Interventions",
        "type": GuidelineType.RISK_OF_BIAS,
        "version": "2016",
        "items": 7,
        "file": "ROBINS_I.md",
        "description": "Non-randomized intervention risk of bias"
    },
    "ROBINS-E": {
        "name": "ROBINS-E",
        "full_name": "Risk of Bias in Non-randomized Studies of Exposures",
        "type": GuidelineType.RISK_OF_BIAS,
        "version": "2024",
        "items": 9,
        "file": "ROBINS_E.md",
        "description": "Non-randomized exposure risk of bias"
    },
    "ROBIS": {
        "name": "ROBIS",
        "full_name": "Risk of Bias in Systematic Reviews",
        "type": GuidelineType.RISK_OF_BIAS,
        "version": "2016",
        "items": 3,
        "file": "ROBIS.md",
        "description": "Systematic review risk of bias"
    },
    "ROB-ME": {
        "name": "ROB-ME",
        "full_name": "Risk of Bias due to Missing Evidence",
        "type": GuidelineType.RISK_OF_BIAS,
        "version": "2023",
        "items": 5,
        "file": "ROB_ME.md",
        "description": "Missing evidence in meta-analysis"
    },
    "PROBAST": {
        "name": "PROBAST",
        "full_name": "Prediction model Risk Of Bias Assessment Tool",
        "type": GuidelineType.RISK_OF_BIAS,
        "version": "2019",
        "items": 4,
        "file": "PROBAST.md",
        "description": "Prediction model risk of bias"
    },
    "PROBAST-AI": {
        "name": "PROBAST+AI",
        "full_name": "PROBAST for AI/ML",
        "type": GuidelineType.RISK_OF_BIAS,
        "version": "2025",
        "items": 5,
        "file": "PROBAST_AI.md",
        "description": "AI prediction model risk of bias"
    },
    "NOS": {
        "name": "NOS",
        "full_name": "Newcastle-Ottawa Scale",
        "type": GuidelineType.RISK_OF_BIAS,
        "version": "Ottawa",
        "items": 8,
        "file": "NOS.md",
        "description": "Observational study quality"
    },
    "COSMIN": {
        "name": "COSMIN RoB",
        "full_name": "COnsensus-based Standards for the selection of health Measurement INstruments",
        "type": GuidelineType.RISK_OF_BIAS,
        "version": "2020",
        "items": 10,
        "file": "COSMIN_RoB.md",
        "description": "Measurement property risk of bias"
    },
    "RoB-NMA": {
        "name": "RoB NMA",
        "full_name": "Risk of Bias in Network Meta-Analysis",
        "type": GuidelineType.RISK_OF_BIAS,
        "version": "2024",
        "items": 5,
        "file": "RoB_NMA.md",
        "description": "Network meta-analysis risk of bias"
    },
    "MI-CLEAR-LLM": {
        "name": "MI-CLEAR-LLM",
        "full_name": "Methodological Investigation of Chatbot LLM Accuracy in Healthcare",
        "type": GuidelineType.DIAGNOSTIC,
        "version": "2025",
        "items": 6,
        "file": "MI_CLEAR_LLM.md",
        "description": "LLM accuracy evaluation in healthcare (supplementary)"
    }
}


@dataclass
class ChecklistItem:
    """A single checklist item for assessment"""
    number: int
    section: str
    item_text: str
    status: str = "NOT_ASSESSED"  # PRESENT, PARTIAL, MISSING, N/A, NOT_ASSESSED
    location: str = ""
    notes: str = ""


@dataclass
class ComplianceReport:
    """Complete compliance assessment report"""
    manuscript_title: str
    guideline: str
    guideline_version: str
    date: str
    checklist_items: List[ChecklistItem]
    summary: Dict[str, int]
    action_items: List[Dict]
    compliance_percentage: float
    json_output: Dict[str, Any] = field(default_factory=dict)
    
    def to_markdown(self) -> str:
        """Generate markdown compliance report"""
        lines = [
            "## Reporting Guideline Compliance Report",
            "",
            f"Manuscript: {self.manuscript_title}",
            f"Guideline: {self.guideline}",
            f"Date: {self.date}",
            f"Assessed by: MedSci Compliance Checker (ARP v24)",
            "",
            "### Summary",
            "",
            "| Status | Count | Percentage |",
            "|--------|-------|------------|",
            f"| PRESENT | {self.summary.get('PRESENT', 0)} | {self.summary.get('PRESENT', 0) / sum(self.summary.values()) * 100 if sum(self.summary.values()) > 0 else 0:.1f}% |",
            f"| PARTIAL | {self.summary.get('PARTIAL', 0)} | {self.summary.get('PARTIAL', 0) / sum(self.summary.values()) * 100 if sum(self.summary.values()) > 0 else 0:.1f}% |",
            f"| MISSING | {self.summary.get('MISSING', 0)} | {self.summary.get('MISSING', 0) / sum(self.summary.values()) * 100 if sum(self.summary.values()) > 0 else 0:.1f}% |",
            f"| N/A | {self.summary.get('N/A', 0)} | {self.summary.get('N/A', 0) / sum(self.summary.values()) * 100 if sum(self.summary.values()) > 0 else 0:.1f}% |",
            "",
            f"**Overall compliance: {self.summary.get('PRESENT', 0)}/{len([i for i in self.checklist_items if i.status != 'N/A'])} ({self.compliance_percentage:.1f}%)**",
            "",
            "### Detailed Checklist",
            "",
            "| # | Section | Item | Status | Location | Notes |",
            "|---|---------|------|--------|----------|-------|"
        ]
        
        for item in self.checklist_items:
            status_icon = {
                "PRESENT": "✅",
                "PARTIAL": "⚠️",
                "MISSING": "❌",
                "N/A": "➖",
                "NOT_ASSESSED": "❓"
            }.get(item.status, "❓")
            lines.append(f"| {item.number} | {item.section} | {item.item_text} | {status_icon} {item.status} | {item.location} | {item.notes} |")
        
        if self.action_items:
            lines.extend([
                "",
                "### Action Items (Priority Order)",
                ""
            ])
            for action in self.action_items:
                lines.append(f"**[{action['status']}] Item {action['item_number']}: {action['item_name']}**")
                lines.append(f"- Required: {action.get('required', 'N/A')}")
                lines.append(f"- Suggested location: {action.get('suggested_location', 'N/A')}")
                if action.get('suggested_fix'):
                    lines.append(f"- Example text: \"{action['suggested_fix']}\"")
                lines.append("")
        
        # Append JSON block
        if self.json_output:
            lines.extend(["", "```json", json.dumps(self.json_output, indent=2), "```"])
        
        return "\n".join(lines)


class ComplianceChecker:
    """
    Compliance checker for medical research reporting guidelines.
    
    Integrates the check-reporting skill for automated manuscript compliance checking.
    """
    
    def __init__(self, checklists_path: str = None):
        """
        Initialize compliance checker.
        
        Args:
            checklists_path: Path to checklists directory. Defaults to integrated checklists.
        """
        self.checklists_path = checklists_path or CHECKLISTS_PATH
        self.guidelines = REPORTING_GUIDELINES
    
    def list_guidelines(self) -> List[str]:
        """List all supported reporting guidelines"""
        return list(self.guidelines.keys())
    
    def get_guideline_info(self, guideline: str) -> Optional[Dict]:
        """Get metadata for a specific guideline"""
        return self.guidelines.get(guideline.upper().replace(" ", "").replace("-", ""))
    
    def auto_detect_guideline(self, manuscript_path: str) -> List[str]:
        """
        Auto-detect appropriate reporting guidelines based on manuscript content.
        
        Args:
            manuscript_path: Path to manuscript file
            
        Returns:
            List of recommended guidelines
        """
        detected = []
        
        if not os.path.exists(manuscript_path):
            return detected
        
        with open(manuscript_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
        
        # Detection rules
        if any(kw in content for kw in ['randomized', 'randomised', 'rct', 'placebo', 'clinical trial']):
            detected.append("CONSORT")
        if any(kw in content for kw in ['strob', 'cohort', 'case-control', 'cross-sectional', 'observational']):
            detected.append("STROBE")
        if any(kw in content for kw in ['diagnostic', 'sensitivity', 'specificity', 'auc', 'roc']):
            detected.append("STARD")
        if any(kw in content for kw in ['systematic review', 'meta-analysis', 'prisma']):
            detected.append("PRISMA 2020")
        if any(kw in content for kw in ['prediction model', 'validation', 'calibration']):
            detected.append("TRIPOD")
        if any(kw in content for kw in ['machine learning', 'deep learning', 'neural network', 'ai model', 'artificial intelligence']):
            if "STARD" in detected:
                detected.append("STARD-AI")
            if "TRIPOD" in detected:
                detected.append("TRIPOD-AI")
            detected.append("CLAIM")
        if any(kw in content for kw in ['case report', 'case presentation']):
            detected.append("CARE")
        if any(kw in content for kw in ['animal', 'rat', 'mouse', 'in vivo']):
            detected.append("ARRIVE")
        if any(kw in content for kw in ['protocol', 'irb', 'ethics']):
            detected.append("SPIRIT")
        
        return detected if detected else ["STROBE"]  # Default to STROBE
    
    def load_checklist(self, guideline: str) -> List[ChecklistItem]:
        """
        Load checklist items for a guideline.
        
        Args:
            guideline: Guideline name
            
        Returns:
            List of checklist items
        """
        guideline_key = guideline.upper().replace(" ", "").replace("-", "")
        guideline_info = self.guidelines.get(guideline_key)
        
        if not guideline_info:
            raise ValueError(f"Unknown guideline: {guideline}")
        
        checklist_file = os.path.join(self.checklists_path, guideline_info["file"])
        
        # If file exists, load from it
        if os.path.exists(checklist_file):
            return self._load_checklist_from_file(checklist_file)
        
        # Otherwise use built-in knowledge
        return self._generate_checklist_from_knowledge(guideline_key, guideline_info)
    
    def _load_checklist_from_file(self, filepath: str) -> List[ChecklistItem]:
        """Load checklist from markdown file"""
        items = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse markdown checklist
        current_section = "General"
        item_number = 0
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Section headers
            if line.startswith('##'):
                current_section = line.replace('##', '').strip()
                continue
            
            # Checklist items (typically numbered or with - [x])
            if line.startswith('- [') or re.match(r'^\d+\.', line):
                item_number += 1
                item_text = re.sub(r'^-\s*\[.\]\s*', '', line)
                item_text = re.sub(r'^\d+\.\s*', '', item_text)
                
                items.append(ChecklistItem(
                    number=item_number,
                    section=current_section,
                    item_text=item_text,
                    status="NOT_ASSESSED"
                ))
        
        return items
    
    def _generate_checklist_from_knowledge(self, guideline_key: str, guideline_info: Dict) -> List[ChecklistItem]:
        """Generate checklist from built-in knowledge"""
        # Built-in checklists for key guidelines
        built_in = {
            "STROBE": [
                (1, "Title and Abstract", "Title and abstract provide informative and balanced summary"),
                (2, "Introduction", "Background/rationale explains scientific context"),
                (3, "Introduction", "Objectives states specific hypothesis or aim"),
                (4, "Methods", "Study design is clearly presented"),
                (5, "Methods", "Setting and locations described with relevant dates"),
                (6, "Methods", "Eligibility criteria for participants specified"),
                (7, "Methods", "Data sources and measurement methods described"),
                (8, "Methods", "Sample size calculation or justification provided"),
                (9, "Methods", "Statistical methods clearly described"),
                (10, "Results", "Participants flow diagram included"),
                (11, "Results", "Baseline characteristics presented"),
                (12, "Results", "Outcome data presented"),
                (13, "Results", "Main results with effect sizes and CIs"),
                (14, "Discussion", "Key results summarized"),
                (15, "Discussion", "Limitations acknowledged"),
                (16, "Discussion", "Interpretation consistent with results"),
                (17, "Discussion", "Generalizability discussed"),
                (18, "Other", "Funding and conflicts disclosed"),
            ],
            "CONSORT": [
                (1, "Title", "Title identifies as randomized trial"),
                (2, "Abstract", "Structured summary provided"),
                (3, "Introduction", "Background and objectives stated"),
                (4, "Methods", "Trial design described"),
                (5, "Methods", "Participants eligibility criteria"),
                (6, "Methods", "Settings and locations"),
                (7, "Methods", "Interventions described"),
                (8, "Methods", "Outcomes pre-specified"),
                (9, "Methods", "Sample size calculated"),
                (10, "Methods", "Randomization method"),
                (11, "Methods", "Allocation concealment"),
                (12, "Methods", "Blinding described"),
                (13, "Results", "Participant flow diagram"),
                (14, "Results", "Recruitment dates"),
                (15, "Results", "Baseline data"),
                (16, "Results", "Numbers analyzed"),
                (17, "Results", "Outcomes with effect sizes"),
                (18, "Discussion", "Limitations discussed"),
                (19, "Discussion", "Generalizability"),
                (20, "Other", "Registration and protocol"),
            ],
            "STARD": [
                (1, "Title", "Identifies as diagnostic accuracy study"),
                (2, "Abstract", "Structured summary with key numbers"),
                (3, "Introduction", "Scientific background stated"),
                (4, "Introduction", "Objectives stated"),
                (5, "Methods", "Study design described"),
                (6, "Methods", "Setting and dates"),
                (7, "Methods", "Participants eligibility"),
                (8, "Methods", "Participant recruitment"),
                (9, "Methods", "Sampling method"),
                (10, "Methods", "Data collection"),
                (11, "Methods", "Statistical methods"),
                (12, "Results", "Participants flow"),
                (13, "Results", "Baseline characteristics"),
                (14, "Results", "Disease prevalence"),
                (15, "Results", "Accuracy metrics with CIs"),
                (16, "Discussion", "Limitations"),
                (17, "Discussion", "Generalizability"),
                (18, "Other", "Funding and COIs"),
            ],
            "PRISMA2020": [
                (1, "Title", "Identifies as systematic review/meta-analysis"),
                (2, "Abstract", "Structured summary with key results"),
                (3, "Introduction", "Rationale for review"),
                (4, "Introduction", "Objectives specified"),
                (5, "Methods", "Registration and protocol"),
                (6, "Methods", "Eligibility criteria"),
                (7, "Methods", "Information sources"),
                (8, "Methods", "Search strategy"),
                (9, "Methods", "Study selection process"),
                (10, "Methods", "Data extraction"),
                (11, "Methods", "Risk of bias assessment"),
                (12, "Methods", "Effect measures"),
                (13, "Methods", "Synthesis methods"),
                (14, "Results", "Study selection with PRISMA diagram"),
                (15, "Results", "Study characteristics"),
                (16, "Results", "Risk of bias"),
                (17, "Results", "Main results"),
                (18, "Discussion", "Summary of evidence"),
                (19, "Discussion", "Limitations"),
                (20, "Discussion", "Conclusions"),
                (21, "Other", "Registration and protocol"),
            ]
        }
        
        items = []
        for num, section, text in built_in.get(guideline_key, built_in.get("STROBE", [])):
            items.append(ChecklistItem(
                number=num,
                section=section,
                item_text=text,
                status="NOT_ASSESSED"
            ))
        
        return items
    
    def assess_manuscript(self, 
                         manuscript_path: str,
                         guideline: str,
                         detailed: bool = True) -> ComplianceReport:
        """
        Assess manuscript compliance with a specific guideline.
        
        Args:
            manuscript_path: Path to manuscript file
            guideline: Guideline name (e.g., "STROBE", "CONSORT")
            detailed: Whether to perform detailed line-by-line assessment
            
        Returns:
            ComplianceReport with assessment results
        """
        if not os.path.exists(manuscript_path):
            raise FileNotFoundError(f"Manuscript not found: {manuscript_path}")
        
        # Load manuscript
        with open(manuscript_path, 'r', encoding='utf-8') as f:
            manuscript_content = f.read()
        
        # Get manuscript title from first heading
        title_match = re.search(r'^#\s+(.+)$', manuscript_content, re.MULTILINE)
        manuscript_title = title_match.group(1) if title_match else "Untitled Manuscript"
        
        # Load checklist
        checklist_items = self.load_checklist(guideline)
        
        # Assess each item
        for item in checklist_items:
            if detailed:
                item.status, item.location, item.notes = self._assess_item(
                    item, manuscript_content
                )
            else:
                item.status = "NOT_ASSESSED"
        
        # Calculate summary
        summary = {
            "PRESENT": sum(1 for i in checklist_items if i.status == "PRESENT"),
            "PARTIAL": sum(1 for i in checklist_items if i.status == "PARTIAL"),
            "MISSING": sum(1 for i in checklist_items if i.status == "MISSING"),
            "N/A": sum(1 for i in checklist_items if i.status == "N/A"),
            "NOT_ASSESSED": sum(1 for i in checklist_items if i.status == "NOT_ASSESSED")
        }
        
        applicable = len([i for i in checklist_items if i.status != "N/A"])
        compliance_pct = (summary["PRESENT"] / applicable * 100) if applicable > 0 else 0
        
        # Generate action items
        action_items = []
        for item in checklist_items:
            if item.status in ["MISSING", "PARTIAL"]:
                action_items.append({
                    "item_number": item.number,
                    "section": item.section,
                    "item_name": item.item_text,
                    "status": item.status,
                    "location": item.location,
                    "suggested_location": f"{item.section}, after existing text",
                    "suggested_fix": self._generate_fix_suggestion(item),
                    "fixable_by_ai": item.status == "MISSING"
                })
        
        # Generate JSON output
        json_output = {
            "check_reporting_version": "1.0",
            "manuscript_title": manuscript_title,
            "guideline": guideline,
            "guideline_version": self.guidelines.get(guideline.upper().replace(" ", ""), {}).get("version", "N/A"),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_items": len(checklist_items),
            "present": summary["PRESENT"],
            "partial": summary["PARTIAL"],
            "missing": summary["MISSING"],
            "na": summary["N/A"],
            "compliance_pct": round(compliance_pct, 1),
            "action_items": [
                {k: v for k, v in action.items() if k != "suggested_fix"}
                for action in action_items
            ]
        }
        
        return ComplianceReport(
            manuscript_title=manuscript_title,
            guideline=guideline,
            guideline_version=json_output["guideline_version"],
            date=json_output["date"],
            checklist_items=checklist_items,
            summary=summary,
            action_items=action_items,
            compliance_percentage=compliance_pct,
            json_output=json_output
        )
    
    def _assess_item(self, item: ChecklistItem, content: str) -> Tuple[str, str, str]:
        """
        Assess a single checklist item.
        
        Returns:
            Tuple of (status, location, notes)
        """
        content_lower = content.lower()
        item_text_lower = item.item_text.lower()
        
        # Keywords to search
        keywords = self._extract_keywords(item.item_text)
        
        # Search in manuscript
        matches = []
        for kw in keywords:
            pattern = re.compile(re.escape(kw), re.IGNORECASE)
            match = pattern.search(content)
            if match:
                # Get surrounding context
                start = max(0, match.start() - 100)
                end = min(len(content), match.end() + 100)
                context = content[start:end].replace('\n', ' ').strip()
                location = f"Content match: ...{context}..."
                matches.append((kw, location))
        
        if not matches:
            return "MISSING", "", f"Required content not found: {item.item_text}"
        
        # Check specificity
        if len(matches) > 0:
            # Check for vague terms that indicate partial compliance
            vague_terms = ['appropriate', 'adequate', 'sufficient', 'adequate', 'reasonable']
            if any(term in content_lower for term in vague_terms):
                return "PARTIAL", matches[0][1], f"Found but lacks specificity: {item.item_text}"
            
            return "PRESENT", matches[0][1], f"Found {len(matches)} match(es)"
        
        return "MISSING", "", "Item not addressed"
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract searchable keywords from checklist item text"""
        # Remove common words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                     'and', 'or', 'if', 'with', 'for', 'to', 'of', 'in', 'on', 'as',
                     'that', 'this', 'it', 'by', 'from', 'should', 'must', 'will'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Also include key phrases
        phrases = re.findall(r'[^,]+', text)
        for phrase in phrases:
            phrase = phrase.strip()
            if len(phrase) > 10 and len(phrase) < 50:
                keywords.append(phrase)
        
        return keywords[:5]  # Limit to top 5
    
    def _generate_fix_suggestion(self, item: ChecklistItem) -> str:
        """Generate a suggested fix for a missing/partial item"""
        suggestions = {
            "Introduction": f"Add: 'This study was conducted to investigate [specific objective].'",
            "Methods": f"Add: 'This section describes the methodology used to [specific aim].'",
            "Results": f"Add: 'The results demonstrate [specific finding with numbers].'",
            "Discussion": f"Add: 'These findings suggest [interpretation] consistent with [reference].'",
        }
        
        section_suggestion = suggestions.get(item.section, "Add appropriate content for this section.")
        return f"[INSERT] {item.item_text}. {section_suggestion}"
    
    def check_compliance(self,
                        manuscript_path: str,
                        guideline: str,
                        output_path: str = None) -> ComplianceReport:
        """
        Check compliance and optionally save report.
        
        Args:
            manuscript_path: Path to manuscript
            guideline: Guideline name
            output_path: Optional path to save report
            
        Returns:
            ComplianceReport object
        """
        report = self.assess_manuscript(manuscript_path, guideline)
        
        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report.to_markdown())
        
        return report
    
    def check_multiple_guidelines(self,
                                 manuscript_path: str,
                                 guidelines: List[str]) -> Dict[str, ComplianceReport]:
        """
        Check compliance against multiple guidelines.
        
        Args:
            manuscript_path: Path to manuscript
            guidelines: List of guideline names
            
        Returns:
            Dict mapping guideline name to ComplianceReport
        """
        results = {}
        for guideline in guidelines:
            results[guideline] = self.assess_manuscript(manuscript_path, guideline)
        return results
    
    def get_guideline_for_study_type(self, study_type: str) -> str:
        """
        Get the appropriate guideline for a study type.
        
        Args:
            study_type: Type of study (e.g., "observational", "rct", "diagnostic")
            
        Returns:
            Guideline name
        """
        mapping = {
            "observational": "STROBE",
            "cohort": "STROBE",
            "case-control": "STROBE",
            "cross-sectional": "STROBE",
            "rct": "CONSORT",
            "randomized": "CONSORT",
            "clinical trial": "CONSORT",
            "diagnostic": "STARD",
            "accuracy": "STARD",
            "prediction": "TRIPOD",
            "prediction model": "TRIPOD",
            "systematic review": "PRISMA 2020",
            "meta-analysis": "PRISMA 2020",
            "dta": "PRISMA-DTA",
            "protocol": "PRISMA-P",
            "animal": "ARRIVE",
            "case report": "CARE",
            "ai": "CLAIM",
            "ml": "CLAIM"
        }
        
        study_type_lower = study_type.lower().replace("-", " ").replace("_", " ")
        return mapping.get(study_type_lower, "STROBE")


def compliance_checker_example():
    """Example usage of the compliance checker"""
    checker = ComplianceChecker()
    
    print("=" * 70)
    print("MEDSCI COMPLIANCE CHECKER - EXAMPLE USAGE")
    print("=" * 70)
    
    # List all supported guidelines
    print("\n📋 Supported Guidelines:")
    for key, info in REPORTING_GUIDELINES.items():
        print(f"  {info['name']:15} ({info['version']:6}) - {info['description'][:40]}")
    
    # Auto-detect guideline example
    print("\n🔍 Auto-detection mapping:")
    study_types = ["observational", "rct", "diagnostic", "prediction model", "systematic review"]
    for st in study_types:
        guideline = checker.get_guideline_for_study_type(st)
        print(f"  {st:20} -> {guideline}")
    
    return checker


if __name__ == "__main__":
    compliance_checker_example()
