from dataclasses import dataclass

@dataclass
class Tile:
    position: tuple
    is_blocked: bool
    height: float
    