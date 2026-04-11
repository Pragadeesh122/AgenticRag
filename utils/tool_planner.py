"""Internal tool execution planning for the general chat orchestrator."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Literal


ExecutionMode = Literal["parallel_safe", "sequential_first"]
PlannerMode = Literal["parallel", "sequential"]


@dataclass(frozen=True)
class ToolPolicy:
    execution_mode: ExecutionMode = "sequential_first"
    max_parallel_instances: int = 1
    requires_fresh_input: bool = True
    dedupe_key_fields: tuple[str, ...] = ()
    verification_only_after_result: bool = False


DEFAULT_TOOL_POLICY = ToolPolicy()


@dataclass(frozen=True)
class PlannedToolCall:
    tool_call: dict[str, Any]
    tool_name: str
    args: dict[str, Any]
    fingerprint: str
    policy: ToolPolicy


@dataclass(frozen=True)
class SuppressedToolCall:
    planned_call: PlannedToolCall
    reason: str


@dataclass(frozen=True)
class ExecutionPlan:
    mode: PlannerMode
    selected_calls: tuple[PlannedToolCall, ...]
    suppressed_calls: tuple[SuppressedToolCall, ...]
    reason: str
    requested_count: int


def normalize_tool_policy(value: Any) -> ToolPolicy:
    if isinstance(value, ToolPolicy):
        return value

    if not isinstance(value, dict):
        return DEFAULT_TOOL_POLICY

    execution_mode = value.get("execution_mode", DEFAULT_TOOL_POLICY.execution_mode)
    if execution_mode not in {"parallel_safe", "sequential_first"}:
        execution_mode = DEFAULT_TOOL_POLICY.execution_mode

    try:
        max_parallel_instances = max(1, int(value.get("max_parallel_instances", 1)))
    except (TypeError, ValueError):
        max_parallel_instances = DEFAULT_TOOL_POLICY.max_parallel_instances

    dedupe_key_fields = tuple(
        str(field)
        for field in value.get("dedupe_key_fields", ())
        if isinstance(field, str) and field
    )

    return ToolPolicy(
        execution_mode=execution_mode,
        max_parallel_instances=max_parallel_instances,
        requires_fresh_input=bool(
            value.get(
                "requires_fresh_input", DEFAULT_TOOL_POLICY.requires_fresh_input
            )
        ),
        dedupe_key_fields=dedupe_key_fields,
        verification_only_after_result=bool(
            value.get(
                "verification_only_after_result",
                DEFAULT_TOOL_POLICY.verification_only_after_result,
            )
        ),
    )


def parse_tool_call_args(tool_call: dict[str, Any]) -> dict[str, Any]:
    arguments = ((tool_call or {}).get("function") or {}).get("arguments", "{}")
    try:
        parsed = json.loads(arguments)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def tool_call_name(tool_call: dict[str, Any]) -> str:
    return str(((tool_call or {}).get("function") or {}).get("name", "") or "")


def tool_call_fingerprint(
    tool_name: str, args: dict[str, Any], policy: ToolPolicy
) -> str:
    if policy.dedupe_key_fields:
        normalized_args = {
            field: args.get(field) for field in policy.dedupe_key_fields if field in args
        }
    else:
        normalized_args = args

    payload = json.dumps(
        {"tool": tool_name, "args": normalized_args},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_planned_tool_call(
    tool_call: dict[str, Any],
    tool_policies: dict[str, ToolPolicy],
) -> PlannedToolCall:
    name = tool_call_name(tool_call)
    args = parse_tool_call_args(tool_call)
    policy = tool_policies.get(name, DEFAULT_TOOL_POLICY)
    fingerprint = tool_call_fingerprint(name, args, policy)
    return PlannedToolCall(
        tool_call=tool_call,
        tool_name=name,
        args=args,
        fingerprint=fingerprint,
        policy=policy,
    )


def plan_tool_calls(
    tool_calls: list[dict[str, Any]],
    *,
    tool_policies: dict[str, ToolPolicy],
    last_evidence_by_fingerprint: dict[str, int],
    current_evidence_version: int,
    max_parallel_calls_per_step: int,
) -> ExecutionPlan:
    requested_count = len(tool_calls or [])
    if not tool_calls:
        return ExecutionPlan(
            mode="sequential",
            selected_calls=(),
            suppressed_calls=(),
            reason="no_tool_calls",
            requested_count=0,
        )

    candidates: list[PlannedToolCall] = []
    suppressed: list[SuppressedToolCall] = []
    seen_in_batch: set[str] = set()

    for tool_call in tool_calls:
        planned = build_planned_tool_call(tool_call, tool_policies)

        if planned.fingerprint in seen_in_batch:
            suppressed.append(
                SuppressedToolCall(
                    planned_call=planned,
                    reason="duplicate_in_batch",
                )
            )
            continue

        seen_in_batch.add(planned.fingerprint)

        if last_evidence_by_fingerprint.get(planned.fingerprint) == current_evidence_version:
            suppressed.append(
                SuppressedToolCall(
                    planned_call=planned,
                    reason="duplicate_without_new_evidence",
                )
            )
            continue

        candidates.append(planned)

    if not candidates:
        return ExecutionPlan(
            mode="sequential",
            selected_calls=(),
            suppressed_calls=tuple(suppressed),
            reason="all_calls_suppressed",
            requested_count=requested_count,
        )

    parallel_eligible = len(candidates) > 1 and all(
        candidate.policy.execution_mode == "parallel_safe"
        and not candidate.policy.requires_fresh_input
        for candidate in candidates
    )

    if parallel_eligible:
        max_allowed = min(
            max_parallel_calls_per_step,
            min(candidate.policy.max_parallel_instances for candidate in candidates),
        )
        selected = candidates[:max_allowed]
        if len(candidates) > max_allowed:
            suppressed.extend(
                SuppressedToolCall(
                    planned_call=planned,
                    reason="parallel_cap_exceeded",
                )
                for planned in candidates[max_allowed:]
            )
            reason = "parallel_truncated"
        else:
            reason = "parallel_safe_batch"
        return ExecutionPlan(
            mode="parallel",
            selected_calls=tuple(selected),
            suppressed_calls=tuple(suppressed),
            reason=reason,
            requested_count=requested_count,
        )

    selected = candidates[:1]
    deferred_reason = (
        "mixed_batch_requires_sequence"
        if len({candidate.tool_name for candidate in candidates}) > 1
        else "sequential_mode_deferred"
    )
    suppressed.extend(
        SuppressedToolCall(planned_call=planned, reason=deferred_reason)
        for planned in candidates[1:]
    )
    reason = "single_call" if len(candidates) == 1 else deferred_reason
    return ExecutionPlan(
        mode="sequential",
        selected_calls=tuple(selected),
        suppressed_calls=tuple(suppressed),
        reason=reason,
        requested_count=requested_count,
    )
