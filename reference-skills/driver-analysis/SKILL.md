---
name: driver-analysis
description: >
  A complete, production-grade workflow for analyzing Windows, Linux, or macOS
  kernel drivers using pyghidra-mcp. Provides comprehensive step-by-step procedures
  for driver model identification, device discovery, memory analysis, synchronization,
  privilege checks, and vulnerability assessment.
license: Apache-2.0
metadata:
  author: clearselabs
  version: "2.0"
---

# Driver Analysis Skill

This skill provides a complete, production-grade workflow for analyzing kernel drivers
using pyghidra-mcp's HTTP tools. It covers the full reverse engineering pipeline from
OS/driver model identification through final vulnerability reporting, including threat
modeling and common vulnerability patterns.

The agent should use this skill whenever:
- A user asks to analyze a driver or kernel module
- A user wants to understand driver behavior, dispatch routines, or IOCTL handling
- A user wants structured reverse-engineering steps using pyghidra-mcp
- A user requests security analysis or vulnerability assessment of drivers

---

## Workflow Overview

The agent should follow these steps unless the user requests a specific tool:

### 1. **Identify OS & Driver Model**
Analyze binary metadata and key symbols to determine:
- Operating system (Windows, Linux, macOS)
- Driver model (WDM, KMDF, UMDF for Windows; char/block/netlink for Linux; IOKit/DriverKit for macOS)
- Driver type (filter, filesystem, network, etc.)

Use `pyghidra-mcp-http_list_project_binary_metadata` and `pyghidra-mcp-http_search_symbols_by_name`
to identify OS-specific patterns and entry points.

### 2. **Enumerate Device Objects & Symbolic Links**
Discover device objects exposed by the driver:
- Search for `IoCreateDevice`, `IoCreateSymbolicLink` calls
- Extract device names from strings and symbol references
- Map device objects to their dispatch routines

Use `pyghidra-mcp-http_search_code` and `pyghidra-mcp-http_search_strings` for this step.

### 3. **List Loaded Binaries**
Use `pyghidra-mcp-http_list_project_binaries` to enumerate all binaries in the project.
- Identify likely driver binaries (e.g., `.sys`, `.ko`, `.kext`).
- If none are loaded, ask the user whether to import one.

### 4. **Inspect Binary Metadata**
Use `pyghidra-mcp-http_list_project_binary_metadata` to retrieve:
- Architecture
- Base address
- Sections
- Entry point
- Analysis status

This helps determine whether further analysis is needed.

### 5. **Enumerate Exports & Imports**
Use:
- `pyghidra-mcp-http_list_exports`
- `pyghidra-mcp-http_list_imports`

Look for:
- DriverEntry/init routines
- Dispatch routines (e.g., IRP_MJ_*)
- OS kernel API usage
- Suspicious imports (e.g., MmMapIoSpace, PsLookupProcessByProcessId)

### 6. **Search for Key Symbols**
Use `pyghidra-mcp-http_search_symbols_by_name` to locate:
- `DriverEntry` / init functions
- `AddDevice`
- `DriverUnload`
- `IRP_MJ_*` handlers
- IOCTL dispatchers (e.g., `DeviceIoControl`, `IoCreateDevice`)

If multiple matches exist, ask the user which one to analyze.

### 7. **Analyze DriverEntry / Init Routines**
Decompile and analyze initialization code:
- Control flow and API calls
- Device creation and registration
- Global state initialization
- Error handling in init paths

Use `pyghidra-mcp-http_decompile_function` and `pyghidra-mcp-http_gen_callgraph`.

### 8. **Analyze Global State & Configuration**
Identify persistent state structures:
- Global variables and statics
- Configuration tables
- Function pointer arrays
- Shared buffers and objects

Use `pyghidra-mcp-http_search_symbols_by_name` for globals and `pyghidra-mcp-http_search_code` for initialization patterns.

### 9. **Analyze Memory Allocation & Buffer Handling**
Examine memory management:
- Search for `ExAllocatePool*`, `MmAllocate*`, `new`, `malloc`
- Track buffer lifetimes and validation
- Identify user-mode pointer dereferences
- Flag missing bounds checks

Use `pyghidra-mcp-http_search_code` for allocation patterns and `pyghidra-mcp-http_decompile_function` for validation logic.

### 10. **Analyze Synchronization & Concurrency**
Identify thread-safety mechanisms:
- Spinlocks, mutexes, semaphores
- Interlocked operations
- Reference counting
- IRQL transitions and APC usage

Use `pyghidra-mcp-http_search_code` for synchronization primitives.

### 11. **Identify Subsystem Hooks & Callbacks**
Find registrations into OS subsystems:
- File system filter hooks
- Network stack callbacks
- Registry/process/thread notifications
- Filter manager registrations

Use `pyghidra-mcp-http_search_symbols_by_name` and `pyghidra-mcp-http_list_imports` for hook APIs.

### 12. **Generate IOCTL Table**
Map IOCTL codes to handlers:
- Extract IOCTL dispatch tables
- Identify control codes and their functions
- Correlate with device objects

Use `pyghidra-mcp-http_decompile_function` on dispatch routines and `pyghidra-mcp-http_search_code` for IOCTL patterns.

### 13. **Generate IRP Callgraphs**
Use `pyghidra-mcp-http_gen_callgraph` to produce MermaidJS callgraphs for:
- DriverEntry
- Dispatch routines
- IOCTL handlers

Summarize:
- Major execution paths
- Initialization flow
- IOCTL routing
- Potential attack surfaces

### 14. **Perform Reachability / Attack Surface Analysis**
Analyze code coverage and accessibility:
- Identify unreachable functions
- Map functions reachable via IOCTLs
- Discover hidden dispatch paths
- Assess overall attack surface

Use xrefs and callgraphs from previous steps.

### 15. **Search Strings & Correlate with Code**
Use `pyghidra-mcp-http_search_strings` to find:
- Device names and symbolic links
- Registry paths and keys
- Debug/error messages
- Hardcoded credentials, URLs, or magic values

Correlate strings with decompiled code for context.

### 16. **Cross-Reference Analysis**
Use `pyghidra-mcp-http_list_cross_references` to:
- Find callers of dispatch routines
- Identify where IOCTL codes are used
- Track pointer usage and suspicious references

### 17. **Hunt for Suspicious Behavior**
Search for security-relevant patterns:
- Privilege escalation
- Arbitrary memory access
- Process/thread manipulation
- Dangerous API usage

Use `pyghidra-mcp-http_search_code` for vulnerability patterns.

### 18. **Analyze Error Paths & Cleanup Routines**
Examine failure handling:
- Error returns and exception paths
- Cleanup and unload routines
- Rare branches and edge cases
- Resource leak potential

Use `pyghidra-mcp-http_decompile_function` on error paths.

### 19. **Generate Final Structured Report**
Summarize all findings in a structured format:
- Driver overview and model
- Key functions and behaviors
- Identified vulnerabilities and risks
- Attack surface assessment
- Recommended next steps

Use the JSON schema below for structured output.

---

## Driver Threat Model

Drivers operate with high privilege and access to sensitive kernel resources. Common threat vectors include:

- **IOCTL Abuse**: Malformed inputs leading to buffer overflows, privilege escalation
- **Memory Corruption**: Improper buffer handling in user-kernel data transfer
- **Race Conditions**: Incorrect synchronization allowing TOCTOU attacks
- **Callback Exploitation**: Hooked functions manipulated for code execution
- **Symbolic Link Attacks**: Predictable names allowing squatting
- **Unload Vulnerabilities**: Cleanup races during driver unloading

---

## Common Vulnerability Patterns

Watch for these patterns during analysis:

- **Buffer Overflows**: `memcpy`/`strcpy` without bounds checking
- **Integer Overflows**: Size calculations not validating against limits
- **Use-After-Free**: Pointers used after `ExFreePool`/`free`
- **Null Pointer Derefs**: Missing null checks on user pointers
- **Privilege Escalation**: `PsLookupProcessByProcessId` + `KeAttachProcess`
- **Arbitrary Memory Access**: `MmMapIoSpace` without validation
- **Race Conditions**: Shared state without proper locking
- **Callback Table Corruption**: Writable function pointer arrays

---

## JSON Schema for Structured Output

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "driver_info": {
      "type": "object",
      "properties": {
        "os": {"type": "string", "enum": ["Windows", "Linux", "macOS"]},
        "model": {"type": "string"},
        "type": {"type": "string"},
        "architecture": {"type": "string"},
        "entry_point": {"type": "string"}
      },
      "required": ["os", "model"]
    },
    "devices": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {"type": "string"},
          "symbolic_link": {"type": "string"},
          "dispatch_routines": {"type": "array", "items": {"type": "string"}}
        }
      }
    },
    "ioctls": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "code": {"type": "string"},
          "handler": {"type": "string"},
          "description": {"type": "string"},
          "risk_level": {"type": "string", "enum": ["low", "medium", "high", "critical"]}
        }
      }
    },
    "vulnerabilities": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": {"type": "string"},
          "location": {"type": "string"},
          "description": {"type": "string"},
          "severity": {"type": "string", "enum": ["info", "low", "medium", "high", "critical"]},
          "cwe": {"type": "string"}
        }
      }
    },
    "attack_surface": {
      "type": "object",
      "properties": {
        "reachable_functions": {"type": "integer"},
        "exported_functions": {"type": "integer"},
        "ioctl_handlers": {"type": "integer"},
        "global_state": {"type": "array", "items": {"type": "string"}}
      }
    },
    "recommendations": {
      "type": "array",
      "items": {"type": "string"}
    }
  },
  "required": ["driver_info", "devices", "ioctls", "vulnerabilities"]
}
```

---

## Best Practices

- Always confirm the correct binary before analysis.
- When multiple symbols match, ask the user which one to inspect.
- Summarize decompiled code in clear, high-level language.
- Highlight security-relevant behavior:
  - privilege escalation
  - arbitrary memory access
  - process/thread manipulation
  - IOCTL misuse
  - insecure buffer handling
- Use the structured JSON output for comprehensive reports.
- Cross-reference findings across multiple analysis phases.

---

## Example Agent Behaviors

### **Example: Find DriverEntry**
1. Search for symbol `"DriverEntry"`.
2. If found, decompile it.
3. Summarize initialization logic.
4. Generate a callgraph.

### **Example: Analyze IOCTL Handling**
1. Search for `"IRP_MJ_DEVICE_CONTROL"`.
2. Decompile the dispatch routine.
3. Identify IOCTL codes.
4. Trace each IOCTL handler via xrefs.
5. Summarize behavior and risks.

### **Example: Vulnerability Assessment**
1. Perform full workflow analysis.
2. Identify buffer handling issues.
3. Check for race conditions.
4. Generate structured JSON report.

---

## When Not to Use This Skill
- When analyzing user‑mode binaries (use a general RE skill instead)
- When the user wants high-level OS driver theory (not binary analysis)
- When no pyghidra-mcp tools are available

---

## References
- Agent Skills Specification
- pyghidra-mcp toolset (internal)
- MITRE CWE for vulnerability classification