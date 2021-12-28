from dataclasses import dataclass
from typing import List, Dict

@dataclass
class PType:
    weak: List[str]
    resist: List[str]
    immune: List[str]


type_list: Dict[str, PType] = {
    "normal": PType(
        weak=["fighting"],
        resist=[],
        immune=["ghost"],
    ),
    "fighting": PType(
        weak=["fairy", "flying", "psychic"],
        resist=["bug", "dark", "rock"],
        immune=[],
    ),
    "flying": PType(
        weak=["electric", "ice", "rock"],
        resist=["bug", "fighting", "grass"],
        immune=["ground"],
    ),
    "poison": PType(
        weak=["ground", "psychic"],
        resist=["grass", "fighting", "poison", "bug", "fairy"],
        immune=[],
    ),
    "ground": PType(
        weak=["water", "grass", "ice"],
        resist=["poison", "rock"],
        immune=["electric"],
    ),
    "rock": PType(
        weak=["water", "grass", "fighting", "ground", "steel"],
        resist=["normal", "fire", "poison", "flying"],
        immune=[],
    ),
    "bug": PType(
        weak=["fire", "flying", "rock"],
        resist=["grass", "fighting", "ground"],
        immune=[],
    ),
    "ghost": PType(
        weak=["ghost", "dark"],
        resist=["poison", "bug"],
        immune=["normal", "fighting"],
    ),
    "steel": PType(
        weak=["fire", "fighting", "ground"],
        resist=["normal", "grass", "ice", "flying", "psychic", "bug", "rock", "dragon", "steel", "fairy"],
        immune=["poison"],
    ),
    "fire": PType(
        weak=["water", "ground", "rock"],
        resist=["fire", "grass", "ice", "bug", "steel", "fairy"],
        immune=[],
    ),
    "water": PType(
        weak=["electric", "grass"],
        resist=["fire", "water", "ice", "steel"],
        immune=[],
    ),
    "grass": PType(
        weak=["fire", "ice", "poison", "flying", "bug"],
        resist=["water", "electric", "grass", "ground"],
        immune=[],
    ),
    "electric": PType(
        weak=["ground"],
        resist=["electric", "flying", "steel"],
        immune=[],
    ),
    "psychic": PType(
        weak=["bug", "dark", "ghost"],
        resist=["fighting", "psychic"],
        immune=[],
    ),
    "ice": PType(
        weak=["fire", "fighting", "rock", "steel"],
        resist=["ice"],
        immune=[],
    ),
    "dragon": PType(
        weak=["ice", "dragon", "fairy"],
        resist=["fire", "water", "electric", "grass"],
        immune=[],
    ),
    "dark": PType(
        weak=["fighting", "bug", "fairy"],
        resist=["ghost", "dark"],
        immune=["psychic"],
    ),
    "fairy": PType(
        weak=["poison", "steel"],
        resist=["dark", "fighting", "bug"],
        immune=["dragon"],
    ),
}
