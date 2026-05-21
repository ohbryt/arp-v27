#!/usr/bin/env python3
"""
ARP v27 - Main Orchestrator
============================
Unified orchestrator: v26 traceable OS + v24 pipeline + v25 self-healing

Phase 4: Pipeline + Disease Packs Integration

Usage:
    python3 arp_orchestrator.py discover DGAT1 --disease lung_cancer --depth full
    python3 arp_orchestrator.py hypothesis list
    python3 arp_orchestrator.py trace show <run_id>
"""

import sys
import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any

# Core v26 (Traceable Research OS)
from core.hypothesis_manager import (
    HypothesisManager, HypothesisState, ProvenanceTrace, 
    FalsificationWorkflow, Director
)

# Core v25 (Self-Healing)
from core.self_healing.harness import SelfHealingHarness, ErrorType

# v24 integrations
from integration.groq_client import client, GROQ_MODELS
from integration.literature_search import PubMedSearch
from integration.dti_prediction import DTIPredictor

# v24 pipeline
from pipeline.candidate_engine import CandidateEngine
from pipeline.scoring_engine import TargetScorer as ScoringEngine
from pipeline.modality_routing import ModalityRouter

# v22 schema
from core.schema import DiseaseType

# v25 agents
from core.agents.hypothesis_agent import HypothesisAgent
from core.agents.experiment_agent import ExperimentAgent


class ARP27Orchestrator:
    """
    Unified orchestrator for ARP v27
    Combines: v26 traceable OS + v24 pipeline + v25 self-healing
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # v26 core
        self.hypothesis_manager = HypothesisManager()
        self.director = Director()
        
        # v25 self-healing
        self.self_healing = SelfHealingHarness()
        
        # v24 integrations
        self.pubmed = PubMedSearch()
        self.dti = DTIPredictor()
        self.candidate_engine = CandidateEngine()
        self.scoring_engine = ScoringEngine()
        self.modality_router = ModalityRouter()
        
        # v25 agents
        self.hypothesis_agent = HypothesisAgent()
        self.experiment_agent = ExperimentAgent()
        
        # Active trace
        self.active_trace: Optional[ProvenanceTrace] = None
        
        print(f"✅ ARP27 Orchestrator initialized")
        print(f"   v26: HypothesisManager, ProvenanceTrace, FalsificationWorkflow")
        print(f"   v25: SelfHealingHarness, HypothesisAgent, ExperimentAgent")
        print(f"   v24: PubMedSearch, DTIPredictor, CandidateEngine, ScoringEngine")
    
    def create_trace(self) -> ProvenanceTrace:
        """Create new provenance trace"""
        trace = self.director.create_trace()
        self.active_trace = trace
        return trace
    
    def discover(self, target: str, disease: str = "cancer", depth: str = "standard") -> Dict:
        """
        Discover drug candidates for target
        Phase 4: Integrates v24 pipeline with v26/v25 orchestration
        """
        print(f"\n🔬 ARP27 Discover: {target} ({disease}, {depth})")
        
        # Create trace
        trace = self.create_trace()
        trace.log("research_start", "ARP27Orchestrator", 
                  f"Discovery started for {target}", f"disease={disease}, depth={depth}")
        
        results = {
            "target": target,
            "disease": disease,
            "depth": depth,
            "run_id": trace.run_id,
            "hypotheses": [],
            "candidates": [],
            "evidence": {}
        }
        
        try:
            # Step 1: Literature search (v24 integration)
            trace.log("literature_search", "PubMedSearch", 
                      f"Searching literature for {target}", f"disease={disease}")
            lit_results = self.pubmed.search(target, disease)
            results["evidence"]["literature"] = lit_results
            print(f"   📚 Literature: {len(lit_results)} results")
            
            # Step 2: DTI prediction (v24 integration)
            trace.log("dti_prediction", "DTIPredictor",
                      f"Predicting drug-target interactions for {target}", "")
            dti_results = self.dti.predict(target)
            results["evidence"]["dti"] = dti_results
            print(f"   🎯 DTI: {len(dti_results)} predictions")
            
            # Step 3: Generate hypotheses (v26 + v25)
            trace.log("hypothesis_generation", "HypothesisAgent",
                      f"Generating hypotheses for {target}", "")
            hypotheses = self.hypothesis_agent.generate(target, disease)
            for h in hypotheses:
                h_obj = self.hypothesis_manager.create(
                    target=target,
                    claim=h.description,
                    source="hypothesis_agent"
                )
                h_obj.supporting_evidence = [f"Literature: {lit_results[:3]}"]
                h_obj.conflicting_evidence = []
                h_obj.missing_evidence = []
                trace.log_hypothesis_generated(h_obj.id, h_obj.claim)
                results["hypotheses"].append(h_obj.to_dict())
            print(f"   💡 Hypotheses: {len(hypotheses)} generated")
            
            # Step 4: Score candidates (v24 pipeline)
            trace.log("candidate_scoring", "CandidateEngine",
                      f"Scoring candidates for {target}", "")
            candidates = self.candidate_engine.score_candidates(target, dti_results)
            results["candidates"] = candidates
            print(f"   🏆 Candidates: {len(candidates)} scored")
            
            # Step 5: Rank hypotheses
            for h in results["hypotheses"]:
                conf = 0.5 + (0.1 * len(results["candidates"]))
                self.hypothesis_manager.rank(h["id"], min(conf, 0.95))
            
            # Complete
            trace.log("research_complete", "ARP27Orchestrator",
                      f"Discovery complete for {target}", 
                      f"{len(hypotheses)} hypotheses, {len(candidates)} candidates")
            
            print(f"\n✅ Complete! Run ID: {trace.run_id}")
            print(f"   Hypotheses: {len(results['hypotheses'])}")
            print(f"   Candidates: {len(results['candidates'])}")
            
        except Exception as e:
            # Self-healing: attempt recovery
            error_record = self.self_healing.record_error(
                ErrorType.API_ERROR,
                str(e),
                {"target": target, "disease": disease}
            )
            print(f"⚠️ Error occurred, self-healing: {error_record.error_id}")
            trace.log("error", "ARP27Orchestrator", str(e), traceback.format_exc())
        
        # Save trace
        trace.save()
        return results
    
    def run_with_self_healing(self, func, *args, **kwargs):
        """Run function with self-healing wrapper"""
        return self.self_healing.execute(func, *args, **kwargs)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ARP v27 - Unified Orchestrator')
    parser.add_argument('--version', action='version', version='v27.0')
    
    subparsers = parser.add_subparsers(dest='command')
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Run discovery for target')
    discover_parser.add_argument('target', help='Target gene/protein name')
    discover_parser.add_argument('--disease', default='cancer', help='Disease type')
    discover_parser.add_argument('--depth', choices=['quick', 'standard', 'full'], default='standard')
    discover_parser.add_argument('--trace', action='store_true', help='Enable tracing')
    
    # Hypothesis commands
    hyp_parser = subparsers.add_parser('hypothesis', help='Hypothesis management')
    hyp_parser.add_argument('action', choices=['list', 'create', 'test', 'retire'])
    hyp_parser.add_argument('--id', help='Hypothesis ID')
    hyp_parser.add_argument('--target', help='Target name')
    hyp_parser.add_argument('--claim', help='Hypothesis claim')
    
    # Trace command
    trace_parser = subparsers.add_parser('trace', help='Provenance trace')
    trace_parser.add_argument('action', choices=['list', 'show'])
    trace_parser.add_argument('--id', help='Run ID')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = ARP27Orchestrator()
    
    if args.command == 'discover':
        results = orchestrator.discover(args.target, args.disease, args.depth)
        print(f"\n📊 Results saved to trace: {results['run_id']}")
        
    elif args.command == 'hypothesis':
        if args.action == 'list':
            hyps = orchestrator.hypothesis_manager.list_by_state()
            print(f"\n📋 Hypotheses ({len(hyps)} total):")
            for h in hyps:
                print(f"  {h.id} [{h.state.value}] {h.target}: {h.claim[:50]}...")
            counts = orchestrator.hypothesis_manager.get_active_count()
            print(f"\n📊 By state: {counts}")
        
        elif args.action == 'create' and args.target and args.claim:
            h = orchestrator.hypothesis_manager.create(args.target, args.claim)
            print(f"✅ Created: {h.id}")
    
    elif args.command == 'trace':
        if args.action == 'list':
            traces_dir = orchestrator.director.traces
            print(f"\n📜 Available traces: {len(traces_dir)}")
            for run_id in traces_dir:
                print(f"  {run_id}")
        
        elif args.action == 'show' and args.id:
            trace_file = f".traces/{args.id}.json"
            import os
            if os.path.exists(trace_file):
                with open(trace_file) as f:
                    data = json.load(f)
                    print(f"\n📜 Trace: {data['run_id']}")
                    print(f"Started: {data['started_at']}")
                    print(f"Events: {data['event_count']}")
                    for e in data['events']:
                        print(f"  [{e['timestamp']}] {e['event_type']}: {e['decision']}")
            else:
                print(f"❌ Trace not found: {args.id}")
    
    elif args.command == 'status':
        print(f"\n🔧 ARP v27 Status")
        print(f"   Hypotheses: {orchestrator.hypothesis_manager.get_active_count()}")
        print(f"   Self-healing: {orchestrator.self_healing.metrics}")
        print(f"   Groq models: {list(GROQ_MODELS.keys())}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()