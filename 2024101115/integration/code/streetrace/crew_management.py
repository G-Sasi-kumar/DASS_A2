"""Crew member management and role assignment."""

from __future__ import annotations

from streetrace.registration import RegistrationModule


class CrewManagementModule:
    """Manages crew members and their roles."""

    def __init__(self, registration: RegistrationModule) -> None:
        """Initialize crew management."""
        self.registration = registration
        self.skill_levels = {}
        self.availability = {}
        self.role_assignments = {}

    def set_skill_level(self, member_id: int, level: int) -> bool:
        """Set skill level for a crew member."""
        member = self.registration.get_member(member_id)
        if not member:
            return False
        self.skill_levels[member_id] = level
        return True

    def get_skill_level(self, member_id: int) -> int:
        """Get skill level for a crew member."""
        return self.skill_levels.get(member_id, 0)

    def set_availability(self, member_id: int, available: bool) -> bool:
        """Set availability status for a crew member."""
        member = self.registration.get_member(member_id)
        if not member:
            return False
        member.available = available
        self.availability[member_id] = available
        return True

    def is_available(self, member_id: int) -> bool:
        """Check if a crew member is available."""
        member = self.registration.get_member(member_id)
        if not member:
            return False
        return member.available

    def assign_role(self, member_id: int, role: str) -> bool:
        """Assign a role to a crew member."""
        member = self.registration.get_member(member_id)
        if not member:
            return False
        member.role = role
        self.role_assignments[member_id] = role
        return True

    def has_role_available(self, role: str) -> bool:
        """Check if any crew member with a role is available."""
        for member in self.registration.members.values():
            if member.role == role and member.available:
                return True
        return False

    def get_members_by_role(self, role: str) -> list[int]:
        """Get all available crew members with a specific role."""
        return [
            member_id
            for member_id, member in self.registration.members.items()
            if member.role == role and member.available
        ]
