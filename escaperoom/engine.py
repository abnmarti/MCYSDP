from dataclasses import dataclass, field

@dataclass
class GameState:
    current_room: str = "intro"
    inventory: set[str] = field(default_factory=set)
    tokens: dict[str, str] = field(default_factory=dict)
    evidence: dict = field(default_factory=dict)

