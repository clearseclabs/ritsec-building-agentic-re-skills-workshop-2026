# Building Agentic Reverse Engineering "Skills"

Student workspace for the RITSEC 2026 workshop.

Friday, November 6, 2026 · 2:00–4:00 PM Eastern

This repository supplies the OpenCode configuration, workshop Skills, and output folders.
The [live workshop guide](https://ritsec-agentic-re-skills.clearseclabs.com/workshop) is the
canonical exercise sequence.

## Start here

```bash
bash scripts/configure-inference.sh
bash scripts/check-workshop.sh
bash scripts/run-opencode.sh windows
```

The first command asks for the room inference code without placing it in shell history. Switch to
the hosted Linux, DHCP patch-diff, or KSTHUNK capstone project later with:

```bash
bash scripts/run-opencode.sh linux
bash scripts/run-opencode.sh dhcp
bash scripts/run-opencode.sh ksthunk
```

The wrapper loads the Git-ignored room credential before starting OpenCode. If you launch OpenCode
manually, load that environment in the current shell first:

```bash
source .workshop.env
opencode
```

All binary-analysis exercises use workshop-hosted PyGhidra-MCP projects. There is no local MCP
server option. No local Ghidra, GPU, Python environment, API subscription, or devcontainer is
required.

Run every workshop command from this repository root. The context-surface demo utilities are
included under `instructor-tools/`; they also connect only to the hosted Windows MCP project.

## Generate or install a Skill

Generate from the captured room workflow with the current Agent Skills specification and hosted
workshop model:

```bash
bash scripts/create-skill.sh workflows/driver-ioctl-harness.txt
```

Or install a reviewed `SKILL.md` downloaded from the web builder:

```bash
bash scripts/install-skill.sh /path/to/downloaded/SKILL.md
```
