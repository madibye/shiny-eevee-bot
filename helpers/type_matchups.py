from dataclasses import dataclass
from enum import StrEnum, auto


class PokemonTypeName(StrEnum):
    Normal = auto()
    Fighting = auto()
    Flying = auto()
    Poison = auto()
    Ground = auto()
    Rock = auto()
    Bug = auto()
    Ghost = auto()
    Steel = auto()
    Fire = auto()
    Water = auto()
    Grass = auto()
    Electric = auto()
    Psychic = auto()
    Ice = auto()
    Dragon = auto()
    Dark = auto()
    Fairy = auto()
    

@dataclass
class PokemonType:
    weak: list[PokemonTypeName]
    resist: list[PokemonTypeName]
    immune: list[PokemonTypeName]


PTN = PokemonTypeName

type_list: dict[PTN, PokemonType] = {
    PTN.Normal: PokemonType(
        weak=[PTN.Fighting],
        resist=[],
        immune=[PTN.Ghost],
    ),
    PTN.Fighting: PokemonType(
        weak=[PTN.Fairy, PTN.Flying, PTN.Psychic],
        resist=[PTN.Bug, PTN.Dark, PTN.Rock],
        immune=[],
    ),
    PTN.Flying: PokemonType(
        weak=[PTN.Electric, PTN.Ice, PTN.Rock],
        resist=[PTN.Bug, PTN.Fighting, PTN.Grass],
        immune=[PTN.Ground],
    ),
    PTN.Poison: PokemonType(
        weak=[PTN.Ground, PTN.Psychic],
        resist=[PTN.Grass, PTN.Fighting, PTN.Poison, PTN.Bug, PTN.Fairy],
        immune=[],
    ),
    PTN.Ground: PokemonType(
        weak=[PTN.Water, PTN.Grass, PTN.Ice],
        resist=[PTN.Poison, PTN.Rock],
        immune=[PTN.Electric],
    ),
    PTN.Rock: PokemonType(
        weak=[PTN.Water, PTN.Grass, PTN.Fighting, PTN.Ground, PTN.Steel],
        resist=[PTN.Normal, PTN.Fire, PTN.Poison, PTN.Flying],
        immune=[],
    ),
    PTN.Bug: PokemonType(
        weak=[PTN.Fire, PTN.Flying, PTN.Rock],
        resist=[PTN.Grass, PTN.Fighting, PTN.Ground],
        immune=[],
    ),
    PTN.Ghost: PokemonType(
        weak=[PTN.Ghost, PTN.Dark],
        resist=[PTN.Poison, PTN.Bug],
        immune=[PTN.Normal, PTN.Fighting],
    ),
    PTN.Steel: PokemonType(
        weak=[PTN.Fire, PTN.Fighting, PTN.Ground],
        resist=[PTN.Normal, PTN.Grass, PTN.Ice, PTN.Flying, PTN.Psychic, PTN.Bug, PTN.Rock, PTN.Dragon, PTN.Steel, PTN.Fairy],
        immune=[PTN.Poison],
    ),
    PTN.Fire: PokemonType(
        weak=[PTN.Water, PTN.Ground, PTN.Rock],
        resist=[PTN.Fire, PTN.Grass, PTN.Ice, PTN.Bug, PTN.Steel, PTN.Fairy],
        immune=[],
    ),
    PTN.Water: PokemonType(
        weak=[PTN.Electric, PTN.Grass],
        resist=[PTN.Fire, PTN.Water, PTN.Ice, PTN.Steel],
        immune=[],
    ),
    PTN.Grass: PokemonType(
        weak=[PTN.Fire, PTN.Ice, PTN.Poison, PTN.Flying, PTN.Bug],
        resist=[PTN.Water, PTN.Electric, PTN.Grass, PTN.Ground],
        immune=[],
    ),
    PTN.Electric: PokemonType(
        weak=[PTN.Ground],
        resist=[PTN.Electric, PTN.Flying, PTN.Steel],
        immune=[],
    ),
    PTN.Psychic: PokemonType(
        weak=[PTN.Bug, PTN.Dark, PTN.Ghost],
        resist=[PTN.Fighting, PTN.Psychic],
        immune=[],
    ),
    PTN.Ice: PokemonType(
        weak=[PTN.Fire, PTN.Fighting, PTN.Rock, PTN.Steel],
        resist=[PTN.Ice],
        immune=[],
    ),
    PTN.Dragon: PokemonType(
        weak=[PTN.Ice, PTN.Dragon, PTN.Fairy],
        resist=[PTN.Fire, PTN.Water, PTN.Electric, PTN.Grass],
        immune=[],
    ),
    PTN.Dark: PokemonType(
        weak=[PTN.Fighting, PTN.Bug, PTN.Fairy],
        resist=[PTN.Ghost, PTN.Dark],
        immune=[PTN.Psychic],
    ),
    PTN.Fairy: PokemonType(
        weak=[PTN.Poison, PTN.Steel],
        resist=[PTN.Dark, PTN.Fighting, PTN.Bug],
        immune=[PTN.Dragon],
    ),
}
