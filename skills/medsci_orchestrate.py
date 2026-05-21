"""
MedSci Orchestrator for ARP v24

Unified entry point for all medsci-skills. Routes requests to appropriate skills,
chains multi-step workflows, and manages the PHI safety gate.

Based on: medsci-skills/skills/orchestrate

Usage:
    from skills.med_sci_orchestrate import MedSciOrchestrator
    
    orchestrator = MedSciOrchestrator()
    result = orchestrator.route("Find papers about MASLD")
    result = orchestrator.run_workflow("data_to_manuscript", project_dir=".")
"""

import os
import json
import re
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Import medsci integration
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from integration.med_sci_integration import MedSciIntegration


class IntentType(Enum):
    """User intent types for routing"""
    LITERATURE_SEARCH = "literature_search"
    MANUSCRIPT_WRITING = "manuscript_writing"
    STATISTICAL_ANALYSIS = "statistical_analysis"
    FIGURE_GENERATION = "figure_generation"
    COMPLIANCE_CHECK = "compliance_check"
    SAMPLE_SIZE = "sample_size"
    DATA_CLEANING = "data_cleaning"
    DEIDENTIFICATION = "deidentification"
    STUDY_DESIGN = "study_design"
    PROTOCOL_WRITING = "protocol_writing"
    JOURNAL_SELECTION = "journal_selection"
    REVISION = "revision"
    META_ANALYSIS = "meta_analysis"
    GRANT_WRITING = "grant_writing"
    PRESENTATION = "presentation"
    PROJECT_INTAKE = "project_intake"
    UNKNOWN = "unknown"


@dataclass
class WorkflowStep:
    """A single step in a workflow"""
    skill: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    output_artifact: Optional[str] = None
    status: str = "pending"  # pending, running, completed, failed


@dataclass
class Workflow:
    """A complete workflow with multiple steps"""
    name: str
    description: str
    steps: List[WorkflowStep]
    phi_gate: bool = False  # Whether this workflow requires PHI check


class IntentClassifier:
    """
    Classifies user intent from natural language requests.
    """
    
    # Keyword patterns for intent detection
    INTENT_PATTERNS = {
        IntentType.LITERATURE_SEARCH: [
            "find papers", "search pubmed", "search literature", "look up",
            "cite", "citation", "reference", "pubmed", "literature search",
            "검색", "논문 검색", "papers about", "studies on"
        ],
        IntentType.MANUSCRIPT_WRITING: [
            "write paper", "write manuscript", "draft paper", "manuscript",
            "write introduction", "write methods", "write results", "write discussion",
            "논문 작성", "원고 작성", "초록 작성"
        ],
        IntentType.STATISTICAL_ANALYSIS: [
            "analyze", "statistics", "statistical", "regression", "t-test",
            "anova", "chi-square", "logistic", "cox", "survival",
            "table 1", "분석", "통계 분석"
        ],
        IntentType.FIGURE_GENERATION: [
            "figure", "plot", "chart", "graph", "roc curve", "forest plot",
            "kaplan-meier", "visualize", "시각화", "플롯"
        ],
        IntentType.COMPLIANCE_CHECK: [
            "check compliance", "check reporting", "strob", "consort", "prisma",
            "stard", "tripod", "claim", "guideline", "checklist",
            "준수 检查", "체크리스트"
        ],
        IntentType.SAMPLE_SIZE: [
            "sample size", "sample size calculation", "power analysis",
            "power calculation", "how many patients", "n required",
            "표본 크기", "검정력", "환자 수"
        ],
        IntentType.DATA_CLEANING: [
            "clean data", "data cleaning", "missing values", "outliers",
            "data quality", "data profile", "정리", "데이터 정리"
        ],
        IntentType.DEIDENTIFICATION: [
            "deidentify", "anonymize", "phi", "remove identifiers",
            "patient data", "personal information", "비식별화", "익명화"
        ],
        IntentType.STUDY_DESIGN: [
            "study design", "design study", "bias", "leakage",
            "methodology", "방법론", "연구 설계"
        ],
        IntentType.PROTOCOL_WRITING: [
            "write protocol", "irb protocol", "ethics protocol",
            "protocol draft", "연구 계획서", "IRB"
        ],
        IntentType.JOURNAL_SELECTION: [
            "find journal", "journal recommendation", "which journal",
            "submit to", "target journal", "journal selection",
            "저널", "투고"
        ],
        IntentType.REVISION: [
            "revise", "reviewer comments", "response to reviewers",
            "revision letter", "수정", "사사평가"
        ],
        IntentType.META_ANALYSIS: [
            "meta-analysis", "meta analysis", "systematic review",
            "prisma", "pooled analysis", "메타 분석"
        ],
        IntentType.GRANT_WRITING: [
            "grant", "funding", "nih", "proposal", "aims page",
            "연구비", "지원 사업"
        ],
        IntentType.PRESENTATION: [
            "presentation", "talk", "slides", "journal club",
            "conference", "발표", "학회"
        ],
        IntentType.PROJECT_INTAKE: [
            "new project", "project setup", "start project",
            "organize", "새 프로젝트", "프로젝트 시작"
        ]
    }
    
    @classmethod
    def classify(cls, request: str) -> IntentType:
        """
        Classify user intent from request string.
        
        Args:
            request: User's natural language request
            
        Returns:
            IntentType enum value
        """
        request_lower = request.lower()
        
        # Count matches for each intent
        scores = {}
        for intent_type, patterns in cls.INTENT_PATTERNS.items():
            score = sum(1 for pattern in patterns if pattern in request_lower)
            if score > 0:
                scores[intent_type] = score
        
        if not scores:
            return IntentType.UNKNOWN
        
        # Return highest scoring intent
        return max(scores.items(), key=lambda x: x[1])[0]
    
    @classmethod
    def get_skill_for_intent(cls, intent: IntentType) -> str:
        """Map intent to skill name"""
        mapping = {
            IntentType.LITERATURE_SEARCH: "search-lit",
            IntentType.MANUSCRIPT_WRITING: "write-paper",
            IntentType.STATISTICAL_ANALYSIS: "analyze-stats",
            IntentType.FIGURE_GENERATION: "make-figures",
            IntentType.COMPLIANCE_CHECK: "check-reporting",
            IntentType.SAMPLE_SIZE: "calc-sample-size",
            IntentType.DATA_CLEANING: "clean-data",
            IntentType.DEIDENTIFICATION: "deidentify",
            IntentType.STUDY_DESIGN: "design-study",
            IntentType.PROTOCOL_WRITING: "write-protocol",
            IntentType.JOURNAL_SELECTION: "find-journal",
            IntentType.REVISION: "revise",
            IntentType.META_ANALYSIS: "meta-analysis",
            IntentType.GRANT_WRITING: "grant-builder",
            IntentType.PRESENTATION: "present-paper",
            IntentType.PROJECT_INTAKE: "intake-project"
        }
        return mapping.get(intent, "orchestrate")


class MedSciOrchestrator:
    """
    Unified orchestrator for medsci-skills in ARP v24.
    
    Responsibilities:
    - Intent classification
    - Skill routing
    - Workflow orchestration
    - PHI safety gate
    - Multi-step workflow management
    """
    
    def __init__(self, medsci_path: str = "/Users/ocm/.openclaw/workspace/medsci-skills"):
        """
        Initialize orchestrator.
        
        Args:
            medsci_path: Path to medsci-skills directory
        """
        self.medsci_path = medsci_path
        self.classifier = IntentClassifier()
        self.med_sci = MedSciIntegration(medsci_path=os.path.join(medsci_path, "skills"))
        
        # Define standard workflows
        self._init_workflows()
    
    def _init_workflows(self):
        """Initialize predefined workflows"""
        self.WORKFLOWS = {
            "new_project": Workflow(
                name="New Project",
                description="Start a new research project from scratch",
                steps=[
                    WorkflowStep(skill="intake-project", action="classify"),
                    WorkflowStep(skill="search-lit", action="initial_search"),
                    WorkflowStep(skill="design-study", action="validate_design"),
                    WorkflowStep(skill="manage-project", action="initialize")
                ],
                phi_gate=False
            ),
            
            "data_to_manuscript": Workflow(
                name="Data to Manuscript",
                description="Full pipeline from raw data to submission-ready manuscript",
                steps=[
                    WorkflowStep(skill="clean-data", action="profile_and_clean"),
                    WorkflowStep(skill="analyze-stats", action="generate_analysis"),
                    WorkflowStep(skill="make-figures", action="generate_figures"),
                    WorkflowStep(skill="write-paper", action="write_manuscript")
                ],
                phi_gate=True
            ),
            
            "draft_to_submission": Workflow(
                name="Draft to Submission",
                description="Take existing draft to submission-ready",
                steps=[
                    WorkflowStep(skill="self-review", action="review"),
                    WorkflowStep(skill="check-reporting", action="check_compliance"),
                    WorkflowStep(skill="search-lit", action="verify_citations"),
                    WorkflowStep(skill="write-paper", action="final_polish")
                ],
                phi_gate=False
            ),
            
            "post_rejection": Workflow(
                name="Post-Rejection Revision",
                description="Handle reviewer comments and revise",
                steps=[
                    WorkflowStep(skill="revise", action="parse_comments"),
                    WorkflowStep(skill="analyze-stats", action="additional_analysis"),
                    WorkflowStep(skill="make-figures", action="revise_figures"),
                    WorkflowStep(skill="revise", action="generate_response")
                ],
                phi_gate=False
            ),
            
            "meta_analysis": Workflow(
                name="Meta-Analysis",
                description="Full systematic review and meta-analysis pipeline",
                steps=[
                    WorkflowStep(skill="search-lit", action="comprehensive_search"),
                    WorkflowStep(skill="fulltext-retrieval", action="download_pdfs"),
                    WorkflowStep(skill="meta-analysis", action="screen_and_extract"),
                    WorkflowStep(skill="analyze-stats", action="pooled_analysis"),
                    WorkflowStep(skill="make-figures", action="generate_forest_plots"),
                    WorkflowStep(skill="write-paper", action="write_systematic_review")
                ],
                phi_gate=False
            ),
            
            "phi_pipeline": Workflow(
                name="PHI-Safe Data Pipeline",
                description="Handle data with PHI from deidentification to manuscript",
                steps=[
                    WorkflowStep(skill="deidentify", action="deidentify_data"),
                    WorkflowStep(skill="clean-data", action="clean_deidentified"),
                    WorkflowStep(skill="analyze-stats", action="generate_analysis"),
                    WorkflowStep(skill="make-figures", action="generate_figures"),
                    WorkflowStep(skill="write-paper", action="write_manuscript")
                ],
                phi_gate=True
            ),
            
            "new_study_protocol": Workflow(
                name="New Study Protocol",
                description="Design new study and write IRB protocol",
                steps=[
                    WorkflowStep(skill="search-lit", action="literature_review"),
                    WorkflowStep(skill="design-study", action="design_methodology"),
                    WorkflowStep(skill="calc-sample-size", action="calculate_n"),
                    WorkflowStep(skill="write-protocol", action="write_irb_protocol")
                ],
                phi_gate=False
            ),
            
            "full_submission": Workflow(
                name="Full Submission Chain",
                description="Complete pipeline to journal submission",
                steps=[
                    WorkflowStep(skill="write-paper", action="write_manuscript"),
                    WorkflowStep(skill="self-review", action="review"),
                    WorkflowStep(skill="check-reporting", action="check_compliance"),
                    WorkflowStep(skill="find-journal", action="recommend_journal"),
                    WorkflowStep(skill="write-paper", action="generate_cover_letter")
                ],
                phi_gate=False
            ),
            
            "case_report": Workflow(
                name="Case Report",
                description="Write a case report from case description to submission",
                steps=[
                    WorkflowStep(skill="search-lit", action="similar_cases"),
                    WorkflowStep(skill="write-paper", action="write_case_report"),
                    WorkflowStep(skill="self-review", action="review"),
                    WorkflowStep(skill="check-reporting", action="check_care_compliance"),
                    WorkflowStep(skill="find-journal", action="recommend_journal")
                ],
                phi_gate=True
            )
        }
    
    def route(self, request: str, project_dir: str = ".") -> Dict[str, Any]:
        """
        Route a user request to the appropriate skill.
        
        Args:
            request: User's natural language request
            project_dir: Working directory
            
        Returns:
            Routing result with skill and parameters
        """
        intent = self.classifier.classify(request)
        skill_name = self.classifier.get_skill_for_intent(intent)
        
        # Extract parameters from request
        params = self._extract_params(request)
        
        return {
            "request": request,
            "intent": intent.value,
            "skill": skill_name,
            "parameters": params,
            "project_dir": project_dir,
            "suggested_workflow": self._suggest_workflow(intent),
            "timestamp": datetime.now().isoformat()
        }
    
    def _extract_params(self, request: str) -> Dict[str, Any]:
        """Extract parameters from request text"""
        params = {}
        
        # Extract topic/query
        topic_match = re.search(r'(?:about|on|regarding|for|과.*|について)', request)
        if topic_match:
            idx = topic_match.end()
            remaining = request[idx:].strip()
            # Take up to first punctuation or comma
            params["topic"] = re.split(r'[,.\n]|그리고', remaining)[0].strip()
        
        # Extract PMID/DOI
        pmid_matches = re.findall(r'\b(\d{7,8})\b', request)
        if pmid_matches:
            params["pmids"] = pmid_matches
        
        doi_matches = re.findall(r'10\.\d{4,}/[^\s]+', request)
        if doi_matches:
            params["dois"] = doi_matches
        
        # Extract file paths
        path_pattern = r'(?:manuscript|data|analysis|qc)/[^\s]+'
        path_matches = re.findall(path_pattern, request)
        if path_matches:
            params["paths"] = path_matches
        
        return params
    
    def _suggest_workflow(self, intent: IntentType) -> Optional[str]:
        """Suggest a workflow for an intent"""
        suggestions = {
            IntentType.LITERATURE_SEARCH: "meta_analysis",
            IntentType.MANUSCRIPT_WRITING: "draft_to_submission",
            IntentType.STATISTICAL_ANALYSIS: "data_to_manuscript",
            IntentType.COMPLIANCE_CHECK: "draft_to_submission",
            IntentType.PROTOCOL_WRITING: "new_study_protocol",
            IntentType.JOURNAL_SELECTION: "full_submission",
            IntentType.PROJECT_INTAKE: "new_project"
        }
        return suggestions.get(intent)
    
    def run_workflow(self, workflow_name: str, project_dir: str = ".", 
                    params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a predefined workflow.
        
        Args:
            workflow_name: Name of workflow to run
            project_dir: Working directory
            params: Additional parameters
            
        Returns:
            Workflow execution result
        """
        if workflow_name not in self.WORKFLOWS:
            return {
                "status": "error",
                "message": f"Unknown workflow: {workflow_name}",
                "available": list(self.WORKFLOWS.keys())
            }
        
        workflow = self.WORKFLOWS[workflow_name]
        params = params or {}
        
        # Check PHI gate
        phi_check_needed = workflow.phi_gate and self._check_phi_needed(project_dir)
        
        result = {
            "workflow": workflow_name,
            "description": workflow.description,
            "steps": [],
            "phi_gate_triggered": phi_check_needed,
            "status": "running",
            "start_time": datetime.now().isoformat()
        }
        
        if phi_check_needed:
            result["phi_warning"] = (
                "PHI gate triggered: Data files found without deidentification. "
                "Run deidentify skill first before proceeding with data analysis."
            )
            result["status"] = "phi_gate"
            return result
        
        # Execute steps
        for i, step in enumerate(workflow.steps, 1):
            step_result = self._execute_step(step, project_dir, params)
            result["steps"].append({
                "step": i,
                "skill": step.skill,
                "action": step.action,
                "status": step_result.get("status", "completed"),
                "output": step_result.get("output")
            })
            
            if step_result.get("status") == "failed":
                result["status"] = "failed"
                break
        
        if result["status"] == "running":
            result["status"] = "completed"
            result["end_time"] = datetime.now().isoformat()
        
        return result
    
    def _execute_step(self, step: WorkflowStep, project_dir: str, 
                     params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step"""
        try:
            skill = getattr(self.med_sci, step.skill.replace("-", "_"), None)
            
            if skill is None:
                return {"status": "failed", "error": f"Skill not found: {step.skill}"}
            
            # Call skill with appropriate method
            if hasattr(skill, step.action):
                method = getattr(skill, step.action)
                output = method(**step.parameters)
                return {"status": "completed", "output": output}
            else:
                # Try calling the skill directly
                output = skill(**step.parameters) if step.parameters else skill
                return {"status": "completed", "output": output}
                
        except Exception as e:
            return {"status": "failed", "error": str(e)}
    
    def _check_phi_needed(self, project_dir: str) -> bool:
        """Check if data files exist without deidentification"""
        data_files = []
        deidentified_files = []
        
        for root, dirs, files in os.walk(project_dir):
            for f in files:
                if f.endswith(('.csv', '.xlsx', '.xls')):
                    filepath = os.path.join(root, f)
                    if '_deidentified' in f or 'deidentified' in f:
                        deidentified_files.append(filepath)
                    elif 'phi' not in f.lower() and 'audit' not in f.lower():
                        data_files.append(filepath)
        
        return len(data_files) > 0 and len(deidentified_files) == 0
    
    def phi_gate_check(self, project_dir: str) -> Dict[str, Any]:
        """
        Perform PHI safety gate check.
        
        Returns:
            PHI assessment result
        """
        data_files = []
        deidentified_files = []
        
        for root, dirs, files in os.walk(project_dir):
            for f in files:
                if f.endswith(('.csv', '.xlsx', '.xls')):
                    filepath = os.path.join(root, f)
                    if '_deidentified' in f:
                        deidentified_files.append(filepath)
                    elif 'phi' not in f.lower():
                        data_files.append(filepath)
        
        return {
            "project_dir": project_dir,
            "data_files_found": len(data_files),
            "deidentified_files_found": len(deidentified_files),
            "phi_gate_needed": len(data_files) > 0 and len(deidentified_files) == 0,
            "phi_likely_present": len(data_files) > 0,
            "recommendation": (
                "De-identify data first" if len(data_files) > 0 and len(deidentified_files) == 0
                else "Proceed with analysis" if len(deidentified_files) > 0
                else "No data files found"
            )
        }
    
    def list_workflows(self) -> List[str]:
        """List all available workflows"""
        return list(self.WORKFLOWS.keys())
    
    def describe_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Get detailed description of a workflow"""
        if workflow_name not in self.WORKFLOWS:
            return {"error": f"Unknown workflow: {workflow_name}"}
        
        workflow = self.WORKFLOWS[workflow_name]
        return {
            "name": workflow.name,
            "description": workflow.description,
            "steps": [
                {"skill": s.skill, "action": s.action}
                for s in workflow.steps
            ],
            "phi_gate": workflow.phi_gate,
            "phi_gate_reason": "Data files may contain PHI" if workflow.phi_gate else "N/A"
        }


def med_sci_orchestrate_example():
    """Example usage of the orchestrator"""
    orchestrator = MedSciOrchestrator()
    
    print("=" * 70)
    print("MEDSCI ORCHESTRATOR - EXAMPLE USAGE")
    print("=" * 70)
    
    # Route examples
    print("\n🎯 Intent Classification Examples:")
    test_requests = [
        "Find papers about MASLD cardiovascular outcomes",
        "Write the methods section for my study",
        "Check STROBE compliance for my manuscript",
        "Calculate sample size for a two-group comparison",
        "Generate ROC curves for my diagnostic study",
        "Help me respond to reviewer comments",
        "Write an IRB protocol for my new study"
    ]
    
    for req in test_requests:
        result = orchestrator.route(req)
        print(f"\n  Request: {req}")
        print(f"  → Intent: {result['intent']}")
        print(f"  → Skill: {result['skill']}")
    
    # Workflow examples
    print("\n" + "=" * 70)
    print("Available Workflows:")
    print("=" * 70)
    for wf_name in orchestrator.list_workflows():
        wf_info = orchestrator.describe_workflow(wf_name)
        print(f"\n  {wf_name}: {wf_info['description']}")
        print(f"    Steps: {' → '.join([s['skill'] for s in wf_info['steps']])}")
        if wf_info['phi_gate']:
            print(f"    ⚠️  PHI Gate Required")
    
    return orchestrator


if __name__ == "__main__":
    med_sci_orchestrate_example()
