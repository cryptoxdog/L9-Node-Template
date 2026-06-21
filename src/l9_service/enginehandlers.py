# L9_META
# role: sdk_bridge
# version: 1.1.0
# status: derived_file
# generated_by: l9-codegen-engine
# source_contract: nodespec.yaml
# hand_editing: forbidden
# transport: TransportPacket
# enginespec_alignment: contracts/ENGINESPEC.yaml
# tags: [l9, sdk, transport, handlers, generated_only]
"""
GENERATED FILE: Engine action handlers, the sole SDK transport bridge for this node.

This file is derived from nodespec.yaml by l9-codegen-engine. Do not edit it by hand.
The repo template may carry this derived-file target path and validation markers, but it does
not own handler generation logic. Update nodespec.yaml and re-run l9-codegen-engine instead.

CONTRACT INVARIANTS:
  - Every public handler must have signature:
      async def handle_<action_slug>(packet: TransportPacket) -> TransportPacket
  - Every action listed in contracts/ENGINESPEC.yaml must align to nodespec.yaml actions.
  - No dict-typed handler parameters.
  - No legacy envelope-wrapper imports anywhere in this repo.
  - No direct node-to-node HTTP. Gate is the sole router.
  - This file is the only file allowed to import from the SDK transport layer.
"""
from __future__ import annotations

from l9_sdk.transport import TransportPacket  # sole SDK bridge import


async def handle_template_boundary(packet: TransportPacket) -> TransportPacket:
    """Template boundary handler proving the generated-only TransportPacket contract.

    This action is a non-production template sentinel. Concrete nodes must regenerate this
    file from nodespec.yaml so real actions replace this sentinel through l9-codegen-engine.
    """
    raise NotImplementedError(
        "src/l9_service/enginehandlers.py is generated-only. Declare actions in "
        "nodespec.yaml and run l9-codegen-engine to generate concrete handlers."
    )
