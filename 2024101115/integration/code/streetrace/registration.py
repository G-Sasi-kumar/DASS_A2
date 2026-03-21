"""Driver and vehicle registration module."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Member:
    """Represents a registered crew member."""

    member_id: int
    name: str
    role: str
    available: bool = True


class RegistrationModule:
    """Handles registration of drivers and vehicles."""

    def __init__(self) -> None:
        """Initialize registration module."""
        self.members = {}
        self.next_member_id = 1

    def register_member(self, name: str, role: str) -> Member:
        """Register a new crew member."""
        member_id = self.next_member_id
        self.next_member_id += 1
        member = Member(member_id=member_id, name=name, role=role)
        self.members[member_id] = member
        return member

    def get_member(self, member_id: int) -> Member | None:
        """Retrieve member information."""
        return self.members.get(member_id)
