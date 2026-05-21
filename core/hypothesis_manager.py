#!/usr/bin/env python3
"""
ARP v26 - Traceable Agentic Research Operating System
====================================================

Integration of:
- v24: arp_pipeline.py, arp_db.py, arp_cli.py, molecular_gpt.py
- v25: Agentic framework concepts
- v26: Hypothesis lifecycle, falsification-first, provenance

Usage:
    python3 arp_v26.py discover DGAT1 --depth full
    python3 arp_v26.py hypothesis list
    python3 arp_v26.py trace show <run_id>
"""

import json
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum

# ============================================================
# HYPOTHESIS LIFECYCLE MANAGER
# ============================================================
class HypothesisState(Enum):
    GENERATED = "generated"
    RANKED = "ranked"
    TESTABLE = "testable"
    TESTED = "tested"
    SUPPORTED = "supported"
    FALSIFIED = "falsified"
    RETIRED = "retired"


class Hypothesis:
    """Hypothesis = Managed Object with full provenance"""
    
    def __init__(
        self,
        target: str,
        claim: str,
        supporting_evidence: List[str] = None,
        conflicting_evidence: List[str] = None,
        missing_evidence: List[str] = None,
        experimental_design: str = None,
        confidence: float = 0.5,
        source: str = "system"
    ):
        self.id = f"hyp_{uuid.uuid4().hex[:12]}"
        self.target = target
        self.claim = claim
        self.supporting_evidence = supporting_evidence or []
        self.conflicting_evidence = conflicting_evidence or []
        self.missing_evidence = missing_evidence or []
        self.experimental_design = experimental_design or ""
        self.confidence = confidence
        self.state = HypothesisState.GENERATED
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
        self.source = source
        self.trace_id = None  # Link to provenance trace
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "target": self.target,
            "claim": self.claim,
            "state": self.state.value,
            "confidence": self.confidence,
            "supporting_evidence": self.supporting_evidence,
            "conflicting_evidence": self.conflicting_evidence,
            "missing_evidence": self.missing_evidence,
            "experimental_design": self.experimental_design,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "source": self.source,
            "trace_id": self.trace_id
        }
    
    def transition(self, new_state: HypothesisState, reason: str = ""):
        """Transition hypothesis state with logging"""
        old_state = self.state
        self.state = new_state
        self.updated_at = datetime.now().isoformat()
        print(f"  [{self.id}] {old_state.value} → {new_state.value} ({reason})")


class HypothesisManager:
    """Hypothesis Lifecycle Manager - v26 core feature"""
    
    def __init__(self, storage_path: str = None):
        self.hypotheses: Dict[str, Hypothesis] = {}
        self.storage_path = storage_path or ".hypotheses"
        self._load()
    
    def _load(self):
        """Load hypotheses from storage"""
        storage_file = Path(self.storage_path) / "hypotheses.json"
        if storage_file.exists():
            with open(storage_file) as f:
                data = json.load(f)
                for h_data in data:
                    h = Hypothesis(
                        target=h_data["target"],
                        claim=h_data["claim"],
                        supporting_evidence=h_data.get("supporting_evidence", []),
                        conflicting_evidence=h_data.get("conflicting_evidence", []),
                        missing_evidence=h_data.get("missing_evidence", []),
                        experimental_design=h_data.get("experimental_design", ""),
                        confidence=h_data.get("confidence", 0.5),
                        source=h_data.get("source", "system")
                    )
                    h.id = h_data["id"]
                    h.state = HypothesisState(h_data["state"])
                    h.created_at = h_data.get("created_at", datetime.now().isoformat())
                    h.updated_at = h_data.get("updated_at", datetime.now().isoformat())
                    h.trace_id = h_data.get("trace_id")
                    self.hypotheses[h.id] = h
    
    def _save(self):
        """Save hypotheses to storage"""
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
        storage_file = Path(self.storage_path) / "hypotheses.json"
        with open(storage_file, 'w') as f:
            json.dump([h.to_dict() for h in self.hypotheses.values()], f, indent=2)
    
    def create(self, target: str, claim: str, source: str = "system") -> Hypothesis:
        """Create new hypothesis"""
        h = Hypothesis(target=target, claim=claim, source=source)
        self.hypotheses[h.id] = h
        self._save()
        print(f"✅ Created hypothesis: {h.id} for {target}")
        return h
    
    def rank(self, hypothesis_id: str, confidence: float):
        """Rank hypothesis by confidence score"""
        h = self.hypotheses.get(hypothesis_id)
        if h:
            h.confidence = confidence
            h.transition(HypothesisState.RANKED, f"confidence={confidence:.2f}")
            self._save()
    
    def mark_testable(self, hypothesis_id: str, experimental_design: str):
        """Mark hypothesis as testable with experimental design"""
        h = self.hypotheses.get(hypothesis_id)
        if h:
            h.experimental_design = experimental_design
            h.transition(HypothesisState.TESTABLE, "experimental design provided")
            self._save()
    
    def test(self, hypothesis_id: str, result: str, supported: bool):
        """Record test results"""
        h = self.hypotheses.get(hypothesis_id)
        if h:
            h.transition(HypothesisState.TESTED, result)
            if supported:
                h.transition(HypothesisState.SUPPORTED, "evidence supports claim")
            else:
                h.transition(HypothesisState.FALSIFIED, "counterevidence found")
            self._save()
    
    def retire(self, hypothesis_id: str, reason: str = ""):
        """Retire a hypothesis"""
        h = self.hypotheses.get(hypothesis_id)
        if h:
            h.transition(HypothesisState.RETIRED, reason)
            self._save()
    
    def list_by_state(self, state: HypothesisState = None) -> List[Hypothesis]:
        """List hypotheses, optionally filtered by state"""
        if state:
            return [h for h in self.hypotheses.values() if h.state == state]
        return list(self.hypotheses.values())
    
    def list_by_target(self, target: str) -> List[Hypothesis]:
        """List hypotheses for a specific target"""
        return [h for h in self.hypotheses.values() if h.target == target]
    
    def get_active_count(self) -> dict:
        """Get counts by state"""
        counts = {}
        for state in HypothesisState:
            counts[state.value] = len([h for h in self.hypotheses.values() if h.state == state])
        return counts


# ============================================================
# PROVENANCE / TRACE SYSTEM
# ============================================================
class ProvenanceTrace:
    """Trace every important decision with evidence"""
    
    def __init__(self, run_id: str = None):
        self.run_id = run_id or f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.events: List[dict] = []
        self.started_at = datetime.now().isoformat()
    
    def log(self, event_type: str, tool: str, decision: str, reason: str, 
            inputs: dict = None, outputs: dict = None):
        """Log an event with full context"""
        event = {
            "run_id": self.run_id,
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "tool": tool,
            "decision": decision,
            "reason": reason,
            "inputs": inputs or {},
            "outputs": outputs or {}
        }
        self.events.append(event)
        return event
    
    def log_tool_choice(self, tool: str, alternative: str, reason: str):
        """Log why a specific tool was chosen over alternatives"""
        self.log(
            event_type="tool_selection",
            tool=tool,
            decision=f"Selected {tool}",
            reason=f"Over {alternative}: {reason}"
        )
    
    def log_hypothesis_generated(self, hypothesis_id: str, claim: str):
        """Log hypothesis generation"""
        self.log(
            event_type="hypothesis_generated",
            tool="HypothesisAgent",
            decision=f"Generated {hypothesis_id}",
            reason=f"Claim: {claim[:100]}..."
        )
    
    def log_validation(self, hypothesis_id: str, result: str, supported: bool):
        """Log validation result"""
        self.log(
            event_type="validation",
            tool="FalsifierAgent",
            decision=f"{hypothesis_id}: {'supported' if supported else 'falsified'}",
            reason=result
        )
    
    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "started_at": self.started_at,
            "events": self.events,
            "event_count": len(self.events)
        }
    
    def save(self, path: str = ".traces"):
        """Save trace to file"""
        Path(path).mkdir(parents=True, exist_ok=True)
        trace_file = Path(path) / f"{self.run_id}.json"
        with open(trace_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"✅ Trace saved: {trace_file}")
        return trace_file


# ============================================================
# FALSIFICATION WORKFLOW
# ============================================================
class FalsificationWorkflow:
    """Falsification-First Workflow for every hypothesis"""
    
    def __init__(self, hypothesis_manager: HypothesisManager):
        self.hm = hypothesis_manager
    
    def create_with_falsification(self, target: str, claim: str, 
                                  supporting_evidence: List[str] = None,
                                  conflicting_evidence: List[str] = None,
                                  missing_evidence: List[str] = None) -> Hypothesis:
        """Create hypothesis with full falsification context"""
        h = self.hm.create(target, claim)
        h.supporting_evidence = supporting_evidence or []
        h.conflicting_evidence = conflicting_evidence or []
        h.missing_evidence = missing_evidence or []
        
        # If conflicting evidence exists, set lower confidence
        if conflicting_evidence:
            h.confidence = min(h.confidence, 0.3)
        
        return h
    
    def generate_evidence_for_hypothesis(self, hypothesis_id: str) -> dict:
        """Generate supporting, conflicting, and missing evidence for hypothesis"""
        h = self.hm.hypotheses.get(hypothesis_id)
        if not h:
            return {}
        
        # This is where you'd integrate with literature search, etc.
        # For now, return placeholder structure
        return {
            "supporting": h.supporting_evidence,
            "conflicting": h.conflicting_evidence,
            "missing": h.missing_evidence,
            "experimental_test": h.experimental_design or "Not yet designed"
        }


# ============================================================
# ORCHESTRATION LAYER
# ============================================================
class Director:
    """Directs research flow - top of orchestration layer"""
    
    def __init__(self):
        self.hypothesis_manager = HypothesisManager()
        self.traces: Dict[str, ProvenanceTrace] = {}
    
    def create_trace(self) -> ProvenanceTrace:
        """Create new trace for a run"""
        trace = ProvenanceTrace()
        self.traces[trace.run_id] = trace
        return trace
    
    def run_research(self, target: str, depth: str = "standard", trace: ProvenanceTrace = None) -> dict:
        """Run full research pipeline for a target"""
        if trace is None:
            trace = self.create_trace()
        
        trace.log("research_start", "Director", f"Research started for {target}", f"depth={depth}")
        
        results = {
            "target": target,
            "depth": depth,
            "run_id": trace.run_id,
            "hypotheses": [],
            "inhibitors": [],
            "structures": []
        }
        
        # Generate hypotheses
        trace.log("hypothesis_generation", "HypothesisAgent", "Generating hypotheses", f"target={target}")
        
        # Create example hypotheses for the target
        h1 = self.hypothesis_manager.create(
            target=target,
            claim=f"{target} is a valid drug target for cancer therapy via ferroptosis",
            source="literature_analysis"
        )
        h1.supporting_evidence = [f"{target} expression correlates with cancer progression"]
        h1.conflicting_evidence = [f"Some studies show {target} has no effect in certain cancer types"]
        trace.log_hypothesis_generated(h1.id, h1.claim)
        
        results["hypotheses"] = [h1.to_dict()]
        
        # Rank hypothesis
        self.hypothesis_manager.rank(h1.id, confidence=0.65)
        
        # Mark as testable
        self.hypothesis_manager.mark_testable(
            h1.id,
            experimental_design=f"In vitro binding assay + cell viability in {target} knockout cells"
        )
        
        trace.log("research_complete", "Director", f"Research complete for {target}", 
                  f"generated {len(results['hypotheses'])} hypotheses")
        
        return results


# ============================================================
# MAIN ENTRY POINT
# ============================================================
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='ARP v26 - Traceable Agentic Research OS')
    subparsers = parser.add_subparsers(dest='command')
    
    # Discover command
    discover_parser = subparsers.add_parser('discover', help='Run research for target')
    discover_parser.add_argument('target', help='Target gene name')
    discover_parser.add_argument('--depth', choices=['quick', 'standard', 'full'], default='standard')
    discover_parser.add_argument('--trace', action='store_true', help='Enable tracing')
    
    # Hypothesis commands
    hyp_parser = subparsers.add_parser('hypothesis', help='Hypothesis management')
    hyp_parser.add_argument('action', choices=['list', 'create', 'test', 'retire'])
    hyp_parser.add_argument('--id', help='Hypothesis ID')
    hyp_parser.add_argument('--target', help='Target name')
    hyp_parser.add_argument('--claim', help='Hypothesis claim')
    hyp_parser.add_argument('--result', help='Test result')
    hyp_parser.add_argument('--supported', type=bool, help='Is supported?')
    
    # Trace command
    trace_parser = subparsers.add_parser('trace', help='Provenance trace')
    trace_parser.add_argument('action', choices=['list', 'show'])
    trace_parser.add_argument('--id', help='Run ID')
    
    args = parser.parse_args()
    
    director = Director()
    
    if args.command == 'discover':
        trace = director.create_trace() if args.trace else None
        results = director.run_research(args.target, args.depth, trace)
        if trace:
            trace.save()
        print(f"\n✅ Research complete for {args.target}")
        print(f"   Hypotheses: {len(results['hypotheses'])}")
        if args.trace:
            print(f"   Trace ID: {results['run_id']}")
    
    elif args.command == 'hypothesis':
        if args.action == 'list':
            hyps = director.hypothesis_manager.list_by_state()
            print(f"\n📋 Hypotheses ({len(hyps)} total):")
            for h in hyps:
                print(f"  {h.id} [{h.state.value}] {h.target}: {h.claim[:50]}...")
            counts = director.hypothesis_manager.get_active_count()
            print(f"\n📊 By state: {counts}")
        
        elif args.action == 'create' and args.target and args.claim:
            h = director.hypothesis_manager.create(args.target, args.claim)
            print(f"✅ Created: {h.id}")
        
        elif args.action == 'test' and args.id:
            director.hypothesis_manager.test(args.id, args.result or "tested", args.supported or False)
            print(f"✅ Tested: {args.id}")
        
        elif args.action == 'retire' and args.id:
            director.hypothesis_manager.retire(args.id, args.result or "")
            print(f"✅ Retired: {args.id}")
    
    elif args.command == 'trace':
        if args.action == 'list':
            print(f"\n📜 Traces: {len(director.traces)}")
            for run_id, trace in director.traces.items():
                print(f"  {run_id}: {trace.events[-1]['event_type'] if trace.events else 'empty'}")
        
        elif args.action == 'show' and args.id:
            trace_file = Path(f".traces/{args.id}.json")
            if trace_file.exists():
                with open(trace_file) as f:
                    data = json.load(f)
                    print(f"\n📜 Trace: {data['run_id']}")
                    print(f"Started: {data['started_at']}")
                    print(f"Events: {data['event_count']}")
                    for e in data['events'][:5]:
                        print(f"  [{e['timestamp']}] {e['event_type']}: {e['decision']}")
            else:
                print(f"❌ Trace not found: {args.id}")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()