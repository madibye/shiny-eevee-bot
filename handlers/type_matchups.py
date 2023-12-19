from enum import StrEnum, auto
from itertools import product, combinations
from numpy import prod
from datetime import datetime

from discord import File


class PokeType(StrEnum):
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

    @property
    def type_matchups(self) -> dict:
        return type_matchup_db.get(self, {})

    def get_defensive_type_matchup(self, attacking_type):
        return prod([key for key in self.type_matchups if attacking_type in self.type_matchups[key]])


type_matchup_db: dict[PokeType, dict[int, list[PokeType]]] = {
    PokeType.Normal: {2: [PokeType.Fighting], 0: [PokeType.Ghost]},
    PokeType.Fighting: {2: [PokeType.Fairy, PokeType.Flying, PokeType.Psychic], 0.5: [PokeType.Bug, PokeType.Dark, PokeType.Rock]},
    PokeType.Flying: {2: [PokeType.Electric, PokeType.Ice, PokeType.Rock], 0.5: [PokeType.Bug, PokeType.Fighting, PokeType.Grass], 0: [PokeType.Ground]},
    PokeType.Poison: {2: [PokeType.Ground, PokeType.Psychic], 0.5: [PokeType.Grass, PokeType.Fighting, PokeType.Poison, PokeType.Bug, PokeType.Fairy]},
    PokeType.Ground: {2: [PokeType.Water, PokeType.Grass, PokeType.Ice], 0.5: [PokeType.Poison, PokeType.Rock], 0: [PokeType.Electric]},
    PokeType.Rock: {2: [PokeType.Water, PokeType.Grass, PokeType.Fighting, PokeType.Ground, PokeType.Steel], 0.5: [PokeType.Normal, PokeType.Fire, PokeType.Poison, PokeType.Flying]},
    PokeType.Bug: {2: [PokeType.Fire, PokeType.Flying, PokeType.Rock], 0.5: [PokeType.Grass, PokeType.Fighting, PokeType.Ground]},
    PokeType.Ghost: {2: [PokeType.Ghost, PokeType.Dark], 0.5: [PokeType.Poison, PokeType.Bug], 0: [PokeType.Normal, PokeType.Fighting]},
    PokeType.Steel: {2: [PokeType.Fire, PokeType.Fighting, PokeType.Ground], 0: [PokeType.Poison], 0.5: [PokeType.Normal, PokeType.Grass, PokeType.Ice, PokeType.Flying, PokeType.Psychic, PokeType.Bug, PokeType.Rock, PokeType.Dragon, PokeType.Steel, PokeType.Fairy]},
    PokeType.Fire: {2: [PokeType.Water, PokeType.Ground, PokeType.Rock], 0.5: [PokeType.Fire, PokeType.Grass, PokeType.Ice, PokeType.Bug, PokeType.Steel, PokeType.Fairy]},
    PokeType.Water: {2: [PokeType.Electric, PokeType.Grass], 0.5: [PokeType.Fire, PokeType.Water, PokeType.Ice, PokeType.Steel]},
    PokeType.Grass: {2: [PokeType.Fire, PokeType.Ice, PokeType.Poison, PokeType.Flying, PokeType.Bug], 0.5: [PokeType.Water, PokeType.Electric, PokeType.Grass, PokeType.Ground]},
    PokeType.Electric: {2: [PokeType.Ground], 0.5: [PokeType.Electric, PokeType.Flying, PokeType.Steel]},
    PokeType.Psychic: {2: [PokeType.Bug, PokeType.Dark, PokeType.Ghost], 0.5: [PokeType.Fighting, PokeType.Psychic]},
    PokeType.Ice: {2: [PokeType.Fire, PokeType.Fighting, PokeType.Rock, PokeType.Steel], 0.5: [PokeType.Ice]},
    PokeType.Dragon: {2: [PokeType.Ice, PokeType.Dragon, PokeType.Fairy], 0.5: [PokeType.Fire, PokeType.Water, PokeType.Electric, PokeType.Grass]},
    PokeType.Dark: {2: [PokeType.Fighting, PokeType.Bug, PokeType.Fairy], 0.5: [PokeType.Ghost, PokeType.Dark], 0: [PokeType.Psychic]},
    PokeType.Fairy: {2: [PokeType.Poison, PokeType.Steel], 0.5: [PokeType.Dark, PokeType.Fighting, PokeType.Bug], 0: [PokeType.Dragon]}}

def generate_type_loops(side_count: int = 3, type_count: int = 2):
    def get_type_matchup(ats: set[PokeType], dts: set[PokeType]):
        number = max({at: prod([dt.get_defensive_type_matchup(at) for dt in dts]) for at in ats}.values())
        return int(number) if number >= 1 else number

    valid_loops = []
    i = 0
    with open('type_loops.txt', 'w') as type_loop_file, open('perfect_loops.txt', 'w') as perfect_loop_file:
        for combo in product([set(t) for n in range(type_count) for t in combinations(PokeType, n+1)], repeat=side_count):
            if (all(c not in valid_loops for c in product(combo, repeat=side_count)) and
                    all(get_type_matchup(combo[n-1], combo[n]) > 1 for n in range(len(combo)))):
                valid_loops.append(combo)
                write_str = ''.join(f"{'/'.join(combo[n]).title()} -> " for n in range(len(combo)-1)) + \
                            '/'.join(combo[-1]).title()
                if (all(get_type_matchup(combo[n - 1], combo[n]) == get_type_matchup(combo[-1], combo[0]) for n in range(len(combo)))
                        and all(get_type_matchup(combo[n], combo[n - 1]) == get_type_matchup(combo[0], combo[-1]) for n in range(len(combo)))):
                    perfect_loop_file.writelines((write_str := write_str + f" (<- {get_type_matchup(combo[0], combo[-1])}x | {get_type_matchup(combo[-1], combo[0])}x ->)") + '\n')
                    write_str = '[!!] ' + write_str
                type_loop_file.writelines(write_str + '\n')
            i += 1
            if i % 50000 == 0:
                print(f"I'm {round(i/50000)}% of the way there... I think!?!")
        type_loop_file.seek(0)
        perfect_loop_file.seek(0)
        return File('./type_loops.txt'), File('./perfect_loops.txt')


if __name__ == "__main__":
    print(start := datetime.now())
    generate_type_loops(3, 2)
    print(f"Operation took {datetime.now() - start} to complete")
