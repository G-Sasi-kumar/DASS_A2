"""Mission planning and crew requirements."""

from __future__ import annotations

from dataclasses import dataclass

from streetrace.crew_management import CrewManagementModule


@dataclass
class Mission:
    """Represents a mission."""

    mission_id: int
    name: str
    required_roles: list[str]
    status: str = "PENDING"


class MissionPlanningModule:
    """Plans missions and checks crew availability."""

    def __init__(self, crew: CrewManagementModule) -> None:
        """Initialize mission planning."""
        self.crew = crew
        self.missions = {}
        self.next_mission_id = 1

    def create_mission(self, name: str, required_roles: list[str]) -> Mission:
        """Create a new mission."""
        mission_id = self.next_mission_id
        self.next_mission_id += 1
        mission = Mission(mission_id=mission_id, name=name, required_roles=required_roles)
        self.missions[mission_id] = mission
        return mission

    def start_mission(self, mission_id: int) -> bool:
        """Start a mission if all required roles are available."""
        mission = self.missions.get(mission_id)
        if not mission:
            return False

        # Check if all required roles have available crew members
        for role in mission.required_roles:
            if not self.crew.has_role_available(role):
                raise ValueError("Required role unavailable for mission")

        mission.status = "ACTIVE"
        return True

    def can_start_mission(self, mission_id: int) -> bool:
        """Check if a mission can start."""
        mission = self.missions.get(mission_id)
        if not mission:
            return False
        for role in mission.required_roles:
            if not self.crew.has_role_available(role):
                return False
        return True
