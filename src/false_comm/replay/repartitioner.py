"""Splits analyzed diffs into an ordered sequence of logical atomic commit steps."""

from pathlib import Path
from typing import NamedTuple

from false_comm.replay.analyzer import CommitDiffAnalysis, DiffFileEntry, SemanticPhase


class ReplayStep(NamedTuple):
    step_index: int
    phase: SemanticPhase
    message: str
    files: list[str]


class DiffRepartitioner:
    """Groups categorized diff files into atomic progressive commit steps."""

    PHASE_ORDER = [
        SemanticPhase.INTERFACE_SCHEMA,
        SemanticPhase.CORE_LOGIC,
        SemanticPhase.TESTS,
        SemanticPhase.DOCS_POLISH,
    ]

    PHASE_MESSAGES = {
        SemanticPhase.INTERFACE_SCHEMA: (
            "feat({scope}): define data models and configuration schemas",
            "chore({scope}): add type definitions and base interfaces",
        ),
        SemanticPhase.CORE_LOGIC: (
            "feat({scope}): implement core logic and handlers",
            "refactor({scope}): modularize internal service routines",
        ),
        SemanticPhase.TESTS: (
            "test({scope}): add unit tests and validation suites",
            "test({scope}): expand test coverage and edge case assertions",
        ),
        SemanticPhase.DOCS_POLISH: (
            "docs: update documentation and usage guidelines",
            "chore: clean up helper scripts and documentation notes",
        ),
    }

    def partition(
        self, analysis: CommitDiffAnalysis, max_files_per_step: int = 3
    ) -> list[ReplayStep]:
        """Convert analysis into ordered progressive steps."""
        steps: list[ReplayStep] = []
        step_idx = 1

        for phase in self.PHASE_ORDER:
            entries = analysis.files_by_phase.get(phase, [])
            if not entries:
                continue

            # Group files into chunks of up to max_files_per_step
            file_chunks: list[list[DiffFileEntry]] = []
            current_chunk: list[DiffFileEntry] = []

            for entry in entries:
                current_chunk.append(entry)
                if len(current_chunk) >= max_files_per_step:
                    file_chunks.append(current_chunk)
                    current_chunk = []
            if current_chunk:
                file_chunks.append(current_chunk)

            # Generate step for each chunk
            for chunk in file_chunks:
                # Deduce scope
                first_path = chunk[0].path
                scope = Path(first_path).parts[0] if len(Path(first_path).parts) > 1 else "core"
                if scope.startswith(".") or scope in {"src", "lib"}:
                    if len(Path(first_path).parts) > 2:
                        scope = Path(first_path).parts[1]
                    else:
                        scope = "core"

                templates = self.PHASE_MESSAGES[phase]
                msg_template = templates[0] if (step_idx % 2 == 1) else templates[-1]
                msg = msg_template.format(scope=scope)

                steps.append(
                    ReplayStep(
                        step_index=step_idx,
                        phase=phase,
                        message=msg,
                        files=[e.path for e in chunk],
                    )
                )
                step_idx += 1

        return steps
