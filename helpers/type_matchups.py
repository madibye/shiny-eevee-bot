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

    def get_type_matchups(self):
        return type_matchups.get(self, {})


PTN = PokemonTypeName

type_matchups: dict[PTN, dict[int, PTN]] = {
    PTN.Normal: {
        2: [PTN.Fighting],
        0.5: [],
        0: [PTN.Ghost],
    },
    PTN.Fighting: {
        2: [PTN.Fairy, PTN.Flying, PTN.Psychic],
        0.5: [PTN.Bug, PTN.Dark, PTN.Rock],
        0: [],
    },
    PTN.Flying: {
        2: [PTN.Electric, PTN.Ice, PTN.Rock],
        0.5: [PTN.Bug, PTN.Fighting, PTN.Grass],
        0: [PTN.Ground],
    },
    PTN.Poison: {
        2: [PTN.Ground, PTN.Psychic],
        0.5: [PTN.Grass, PTN.Fighting, PTN.Poison, PTN.Bug, PTN.Fairy],
        0: [],
    },
    PTN.Ground: {
        2: [PTN.Water, PTN.Grass, PTN.Ice],
        0.5: [PTN.Poison, PTN.Rock],
        0: [PTN.Electric],
    },
    PTN.Rock: {
        2: [PTN.Water, PTN.Grass, PTN.Fighting, PTN.Ground, PTN.Steel],
        0.5: [PTN.Normal, PTN.Fire, PTN.Poison, PTN.Flying],
        0: [],
    },
    PTN.Bug: {
        2: [PTN.Fire, PTN.Flying, PTN.Rock],
        0.5: [PTN.Grass, PTN.Fighting, PTN.Ground],
        0: [],
    },
    PTN.Ghost: {
        2: [PTN.Ghost, PTN.Dark],
        0.5: [PTN.Poison, PTN.Bug],
        0: [PTN.Normal, PTN.Fighting],
    },
    PTN.Steel: {
        2: [PTN.Fire, PTN.Fighting, PTN.Ground],
        0.5: [PTN.Normal, PTN.Grass, PTN.Ice, PTN.Flying, PTN.Psychic, PTN.Bug, PTN.Rock, PTN.Dragon, PTN.Steel, PTN.Fairy],
        0: [PTN.Poison],
    },
    PTN.Fire: {
        2: [PTN.Water, PTN.Ground, PTN.Rock],
        0.5: [PTN.Fire, PTN.Grass, PTN.Ice, PTN.Bug, PTN.Steel, PTN.Fairy],
        0: [],
    },
    PTN.Water: {
        2: [PTN.Electric, PTN.Grass],
        0.5: [PTN.Fire, PTN.Water, PTN.Ice, PTN.Steel],
        0: [],
    },
    PTN.Grass: {
        2: [PTN.Fire, PTN.Ice, PTN.Poison, PTN.Flying, PTN.Bug],
        0.5: [PTN.Water, PTN.Electric, PTN.Grass, PTN.Ground],
        0: [],
    },
    PTN.Electric: {
        2: [PTN.Ground],
        0.5: [PTN.Electric, PTN.Flying, PTN.Steel],
        0: [],
    },
    PTN.Psychic: {
        2: [PTN.Bug, PTN.Dark, PTN.Ghost],
        0.5: [PTN.Fighting, PTN.Psychic],
        0: [],
    },
    PTN.Ice: {
        2: [PTN.Fire, PTN.Fighting, PTN.Rock, PTN.Steel],
        0.5: [PTN.Ice],
        0: [],
    },
    PTN.Dragon: {
        2: [PTN.Ice, PTN.Dragon, PTN.Fairy],
        0.5: [PTN.Fire, PTN.Water, PTN.Electric, PTN.Grass],
        0: [],
    },
    PTN.Dark: {
        2: [PTN.Fighting, PTN.Bug, PTN.Fairy],
        0.5: [PTN.Ghost, PTN.Dark],
        0: [PTN.Psychic],
    },
    PTN.Fairy: {
        2: [PTN.Poison, PTN.Steel],
        0.5: [PTN.Dark, PTN.Fighting, PTN.Bug],
        0: [PTN.Dragon],
    },
}
