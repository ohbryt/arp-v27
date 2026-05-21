#!/usr/bin/env python3
"""
ARP v27 - Main Orchestrator
============================
Unified orchestrator: v26 traceable OS + v24 pipeline + v25 self-healing

Usage:
    python3 arp_orchestrator.py discover DGAT1 --disease lung_cancer --depth full
    python3 arp_orchestrator.py hypothesis list
    python3 arp_orchestrator.py trace show <run_id>
"""

import asyncio
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
from core.self_healing.harness import SelfHealingHarness

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
        Integrates v24 pipeline with v26/v25 orchestration
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
            try:
                lit_results = self.pubmed.search(f'{target} {disease}', max_results=5)
                results["evidence"]["literature"] = lit_results
                print(f"   📚 Literature: {len(lit_results)} results")
            except Exception as e:
                print(f"   📚 Literature: error ({e})")
                results["evidence"]["literature"] = []
            
            # Step 2: DTI prediction (v24 integration)  
            trace.log("dti_prediction", "DTIPredictor",
                      f"Predicting drug-target interactions for {target}", "")
            try:
                dti_results = self.dti.predict_dti(target, '', protein_sequence=None, ligand_smiles=None)
                results["evidence"]["dti"] = dti_results
                print(f"   🎯 DTI: predicted")
            except Exception as e:
                print(f"   🎯 DTI: error ({e})")
                results["evidence"]["dti"] = {}
            
            # Step 3: Generate candidates (v24 pipeline)
            trace.log("candidate_generation", "CandidateEngine",
                      f"Generating candidates for {target}", f"disease={disease}")
            try:
                cand_result = self.candidate_engine.generate_candidates(target, disease)
                candidates = cand_result.candidates if hasattr(cand_result, 'candidates') else []
                results["candidates"] = [c.to_dict() for c in candidates[:5]] if candidates else []
                print(f"   🏆 Candidates: {len(results['candidates'])} generated")
                
                # Print top candidates
                for i, c in enumerate(results["candidates"][:3]):
                    name = c.get('name', 'Unknown')
                    stage = c.get('development_stage', 'unknown')
                    score = c.get('composite_score', 0)
                    print(f"      {i+1}. {name} ({stage}) - score: {score:.3f}")
            except Exception as e:
                print(f"   🏆 Candidates: error ({e})")
                results["candidates"] = []
            
            # Step 4: Generate hypotheses (v26 + v25)
            trace.log("hypothesis_generation", "HypothesisAgent",
                      f"Generating hypotheses for {target}", "")
            try:
                hyp_list = asyncio.run(self.hypothesis_agent.generate(target, disease))
                if isinstance(hyp_list, list):
                    hypotheses = hyp_list
                else:
                    hypotheses = []
                
                for h in hypotheses:
                    h_obj = self.hypothesis_manager.create(
                        target=target,
                        claim=h.description if hasattr(h, 'description') else str(h),
                        source="hypothesis_agent"
                    )
                    trace.log_hypothesis_generated(h_obj.id, h_obj.claim)
                    results["hypotheses"].append(h_obj.to_dict())
                print(f"   💡 Hypotheses: {len(hypotheses)} generated")
            except Exception as e:
                print(f"   💡 Hypotheses: error ({e})")
            
            # Step 5: Rank hypotheses by candidate scores
            if results["candidates"]:
                conf = 0.5 + (0.1 * min(len(results["candidates"]), 5))
                for h in results["hypotheses"]:
                    self.hypothesis_manager.rank(h["id"], min(conf, 0.95))
            
            # Complete
            trace.log("research_complete", "ARP27Orchestrator",
                      f"Discovery complete for {target}", 
                      f"{len(results['hypotheses'])} hypotheses, {len(results['candidates'])} candidates")
            
            print(f"\n✅ Complete! Run ID: {trace.run_id}")
            print(f"   Hypotheses: {len(results['hypotheses'])}")
            print(f"   Candidates: {len(results['candidates'])}")
            
        except Exception as e:
            print(f"⚠️ Error: {e}")
            trace.log("error", "ARP27Orchestrator", str(e), traceback.format_exc())
        
        # Save trace
        trace.save()
        return results


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
        print(f"   Groq models: {list(GROQ_MODELS.keys())}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()