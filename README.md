# ARP v27 - Unified Traceable Agentic Research OS
# https://github.com/ohbryt/arp-v27

## Quick Start
```bash
cd arp-v27
python3 arp_orchestrator.py status
python3 arp_orchestrator.py discover DGAT1 --disease lung_cancer --depth full
python3 arp_orchestrator.py hypothesis list
```

## Architecture
- v26: Traceable Research OS (HypothesisManager, ProvenanceTrace, FalsificationWorkflow)
- v25: Self-Healing Harness, DeepDock, HypothesisAgent, ExperimentAgent  
- v24: 16 integrations (Groq, PubMed, DTI, CandidateEngine...)
- v22: Disease packs (Cancer, MASLD, Sarcopenia, Cardiac Fibrosis)

## CLI Commands
```bash
# Discovery
python3 arp_orchestrator.py discover <TARGET> --disease <DISEASE> --depth [quick|standard|full]

# Hypothesis management
python3 arp_orchestrator.py hypothesis list
python3 arp_orchestrator.py hypothesis create --target <T> --claim <C>

# Trace provenance
python3 arp_orchestrator.py trace list
python3 arp_orchestrator.py trace show <RUN_ID>

# Status
python3 arp_orchestrator.py status
```

## Phases Completed
- Phase 1: Foundation (v26 core) ✅
- Phase 2: v24 integrations (16) ✅
- Phase 3: v25 self-healing + agents ✅
- Phase 4: Pipeline + disease packs ✅
- Phase 5: BioDesignBench validation (pending)

## License
MIT