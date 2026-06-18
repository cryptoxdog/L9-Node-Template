# L9META: file=enginehandlers.py | type=generated_skeleton | spec_section=actions
# L9META: node=l9_service | version=0.1.0 | transport=TransportPacket
"""
Engine action handlers - the sole SDK transport bridge for this node.

CONTRACT INVARIANTS:
  - Every public function: async def handle_{action_slug}(packet: TransportPacket) -> TransportPacket
  - No dict-typed handler parameters.
  - No envelope-wrapper imports (only TransportPacket is permitted).
  - No direct HTTP client imports (httpx / requests / aiohttp).
  - Gate router is the sole caller of functions in this file.

CODEGEN INSTRUCTIONS:
  - Replace each `raise NotImplementedError` body with domain logic once
    enginespec.yaml actions are declared in nodespec.yaml.
  - Do not add handler functions manually - run codegen with updated nodespec.yaml.
  - Do not import SDK transport from any other file in this package.
"""
from __future__ import annotations

from l9_sdk.transport import TransportPacket  # sole SDK bridge import


async def handle_example(packet: TransportPacket) -> TransportPacket:
    """Handle example action.

    Mutation class: READ
    Intent: Placeholder - replace via codegen with action defined in nodespec.yaml.

    Args:
        packet: Inbound TransportPacket routed by the Gate.

    Returns:
        TransportPacket: Response packet containing action result.
    """
    raise NotImplementedError(
        "handle_example is a codegen skeleton. "
        "Declare actions in nodespec.yaml and re-run codegen to generate real handlers."
    )
