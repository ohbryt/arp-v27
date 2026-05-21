# GStack Integration

## Overview

**Source:** https://github.com/garrytan/gstack  
**Creator:** Garry Tan (Y Combinator CEO)  
**GitHub:** 70,000+ ⭐  
**Purpose:** AI coding agent framework with sprint structure

---

## Core Philosophy

**"Thin shell, thick skills"**

- No complex runtime
- Markdown-based structured prompts
- Skills execute on existing slash command infrastructure
- 23 specialized skills in sprint structure

---

## Sprint Workflow

```
생각하기 → 계획 → 구축 → 리뷰 → 테스트 → 배포 → 회고
(Think)   (Plan)  (Build) (Review) (Test)  (Ship)  (Retro)
```

---

## Available Skills

### OpenClaw Integration

| Skill | Purpose |
|-------|---------|
| **office-hours** | YC-style product thinking - forcing questions |
| **investigate** | Deep debugging and root cause analysis |
| **ceo-review** | Business value and product alignment review |
| **retro** | Sprint retrospective and learnings |

### Core Skills

| Skill | Purpose |
|-------|---------|
| `plan-design-review` | Design document review |
| `plan-eng-review` | Engineering review |
| `design-consultation` | Design consultation |
| `review` | Code review |
| `qa` | Playwright browser QA |
| `office-hours` | Product validation |
| `learn` | Learn from codebase |

---

## Key Features

### 1. Parallel Execution
- 10-15 simultaneous Claude Code sessions
- Up to 50 PRs/day
- Work tree-based independent branches

### 2. Cross-Model Review
`/codex` command for Claude + Codex cross-review

### 3. Browser QA
`/qa` with Playwright for real browser testing

### 4. Adversarial Review
Automated design document validation

---

## Integration with ARP v24

### GStack → ARP v24 Mapping

| GStack Concept | ARP v24 Implementation |
|----------------|------------------------|
| Sprint workflow | Director Agent orchestration |
| Office Hours | Research question validation |
| CEO Review | Business value alignment |
| Cross-model review | Groq + GLM + Qwen fallback |
| Parallel execution | Sub-agent parallel tasks |
| QA | Test suite validation |

---

## Usage in ARP v24

```bash
# Install gstack for OpenClaw
cd ~/.openclaw/workspace/gstack
./setup --tool openclaw

# Or copy skills directly
cp -r openclaw/skills/* ~/.openclaw/skills/
```

---

## GStack Skills for ARP v24

Copied to: `arp-v24/skills/gstack/`

- `gstack-openclaw-ceo-review/` - Business value review
- `gstack-openclaw-investigate/` - Deep debugging
- `gstack-openclaw-office-hours/` - Product validation
- `gstack-openclaw-retro/` - Sprint retrospective

---

## Reference Documents

- `docs/ARCHITECTURE.md` - Full architecture
- `docs/SKILL.md` - Skill template
- `docs/README.md` - Getting started

---

## Key Insights from GStack

1. **Process over tools** - AI's bottleneck is process, not intelligence
2. **Team simulation** - Multiple agents working in parallel
3. **Adversarial review** - Always challenge assumptions
4. **Forcing questions** - "가장 강력한 증거가 뭔가요?"

---

## Status

- [x] Cloned from GitHub
- [x] OpenClaw skills copied
- [ ] Full installation
- [ ] Integration with Director Agent

---

*Source: garrytan/gstack · 70k+ stars · MIT License*