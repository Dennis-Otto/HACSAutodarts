"""Independent cloud and local coordinators for one board."""

from dataclasses import dataclass

from .coordinator import AutodartsDataUpdateCoordinator
from .local_coordinator import AutodartsLocalCoordinator


@dataclass
class AutodartsRuntimeData:
    cloud: AutodartsDataUpdateCoordinator | None = None
    local: AutodartsLocalCoordinator | None = None
