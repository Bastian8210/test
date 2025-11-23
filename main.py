import argparse
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Upgrade:
    key: str
    name: str
    description: str
    base_cost: float
    cost_multiplier: float
    passive_income: float = 0.0
    tap_bonus: float = 0.0

    def cost_for_purchase(self, owned: int) -> float:
        return self.base_cost * (self.cost_multiplier ** owned)


@dataclass
class GameState:
    coins: float = 0.0
    coins_per_tap: float = 1.0
    passive_rate: float = 0.0
    upgrades_owned: Dict[str, int] = field(default_factory=dict)
    upgrades: Dict[str, Upgrade] = field(default_factory=dict)
    last_tick: float = field(default_factory=time.time)

    def accrue_passive_income(self) -> None:
        now = time.time()
        elapsed = now - self.last_tick
        self.last_tick = now
        if self.passive_rate > 0:
            self.coins += self.passive_rate * elapsed

    def tap(self) -> float:
        self.accrue_passive_income()
        self.coins += self.coins_per_tap
        return self.coins_per_tap

    def buy_upgrade(self, key: str) -> bool:
        self.accrue_passive_income()
        if key not in self.upgrades:
            return False
        owned = self.upgrades_owned.get(key, 0)
        upgrade = self.upgrades[key]
        cost = upgrade.cost_for_purchase(owned)
        if self.coins < cost:
            return False

        self.coins -= cost
        self.upgrades_owned[key] = owned + 1
        self.passive_rate += upgrade.passive_income
        self.coins_per_tap += upgrade.tap_bonus
        return True

    def format_coins(self, amount: float) -> str:
        if amount >= 1_000_000:
            return f"{amount/1_000_000:.2f}M"
        if amount >= 1_000:
            return f"{amount/1_000:.2f}k"
        return f"{amount:.0f}"

    def summary_lines(self) -> List[str]:
        lines = [
            f"Coins: {self.format_coins(self.coins)}",
            f"Income per tap: {self.format_coins(self.coins_per_tap)}",
            f"Passive income: {self.passive_rate:.2f}/s",
        ]
        if self.upgrades_owned:
            owned_text = ", ".join(
                f"{self.upgrades[u].name} x{count}"
                for u, count in sorted(self.upgrades_owned.items())
            )
            lines.append(f"Owned upgrades: {owned_text}")
        else:
            lines.append("Owned upgrades: none yet")
        return lines

    def upgrade_catalog(self) -> List[str]:
        catalog_lines = []
        for key, upgrade in self.upgrades.items():
            owned = self.upgrades_owned.get(key, 0)
            cost = upgrade.cost_for_purchase(owned)
            catalog_lines.append(
                f"[{key}] {upgrade.name} — cost {self.format_coins(cost)}, "
                f"+{upgrade.passive_income:.2f}/s passive, "
                f"+{upgrade.tap_bonus:.1f} per tap (owned {owned})"
            )
        return catalog_lines


def build_default_game() -> GameState:
    upgrades = {
        "F": Upgrade(
            key="F",
            name="Fleet of Carts",
            description="Boosts tap strength and a bit of idle income.",
            base_cost=15,
            cost_multiplier=1.6,
            passive_income=0.5,
            tap_bonus=0.5,
        ),
        "M": Upgrade(
            key="M",
            name="Mine Shaft",
            description="Adds steady passive coins each second.",
            base_cost=60,
            cost_multiplier=1.65,
            passive_income=2.5,
        ),
        "R": Upgrade(
            key="R",
            name="Research Lab",
            description="Improves tapping efficiency.",
            base_cost=120,
            cost_multiplier=1.7,
            tap_bonus=2.0,
        ),
        "O": Upgrade(
            key="O",
            name="Outpost Manager",
            description="Significant boost to passive output.",
            base_cost=300,
            cost_multiplier=1.75,
            passive_income=7.5,
        ),
    }
    return GameState(upgrades=upgrades)


def print_banner() -> None:
    print("=" * 52)
    print(" Idle Tycoon — terminal edition ")
    print(" Tap (t) to collect coins, buy upgrades (b), or wait (w). Quit with (q).")
    print("=" * 52)


def interactive_loop(game: GameState) -> None:
    print_banner()
    while True:
        game.accrue_passive_income()
        for line in game.summary_lines():
            print(line)
        print("\nUpgrades available:")
        for line in game.upgrade_catalog():
            print(f"  {line}")
        print("\nOptions: (t)ap, (b)uy upgrade, (w)ait 5s, (q)uit")
        choice = input("> ").strip().lower()

        if choice == "q":
            print("Thanks for playing!")
            break
        if choice == "t":
            gained = game.tap()
            print(f"You tapped and earned {game.format_coins(gained)} coins!\n")
            continue
        if choice == "w":
            print("Waiting...")
            time.sleep(5)
            game.accrue_passive_income()
            print("Time advanced by 5 seconds.\n")
            continue
        if choice == "b":
            key = input("Choose an upgrade key to buy: ").strip().upper()
            if not key:
                print("No upgrade selected.\n")
                continue
            if game.buy_upgrade(key):
                print(f"Purchased {game.upgrades[key].name}!\n")
            else:
                print("Not enough coins or invalid choice.\n")
            continue
        print("Unknown option. Try again.\n")


def run_demo(game: GameState, steps: int = 6) -> None:
    print_banner()
    for _ in range(steps):
        game.accrue_passive_income()
        gained = game.tap()
        print(f"Tap! +{game.format_coins(gained)} coins (total {game.format_coins(game.coins)})")
        time.sleep(0.2)
    print("Attempting to buy the first available upgrade...")
    for key in game.upgrades:
        if game.buy_upgrade(key):
            print(f"Bought {game.upgrades[key].name}. Coins left: {game.format_coins(game.coins)}")
            break
    print("Final stats:")
    for line in game.summary_lines():
        print(f"- {line}")


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Play the Idle Tycoon terminal game")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run a short scripted sequence instead of interactive play.",
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=6,
        help="Number of taps to run during demo mode.",
    )
    return parser.parse_args(argv)


def main(argv: List[str]) -> int:
    args = parse_args(argv)
    game = build_default_game()
    if args.demo:
        run_demo(game, steps=max(1, args.steps))
    else:
        interactive_loop(game)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
