import Foundation
import Combine

struct Upgrade: Identifiable {
    let id: UUID = .init()
    let name: String
    let description: String
    let baseCost: Double
    let costGrowth: Double
    let effect: UpgradeEffect
    var level: Int = 0

    func cost(forNextLevel currentLevel: Int) -> Double {
        return baseCost * pow(costGrowth, Double(currentLevel))
    }
}

enum UpgradeEffect {
    case tapMultiplier(Double)
    case passiveRate(Double)
    case efficiency(Double)
}

final class GameState: ObservableObject {
    @Published private(set) var coins: Double
    @Published private(set) var coinsPerTap: Double
    @Published private(set) var passiveRate: Double
    @Published private(set) var efficiency: Double
    @Published private(set) var upgrades: [Upgrade]

    private var timer: AnyCancellable?
    private var lastTick: Date

    init() {
        coins = 0
        coinsPerTap = 1
        passiveRate = 0
        efficiency = 1
        lastTick = Date()
        upgrades = [
            Upgrade(name: "Heavy Tap", description: "Double coins for each tap.", baseCost: 15, costGrowth: 1.6, effect: .tapMultiplier(2)),
            Upgrade(name: "Auto Miner", description: "Generate coins every second.", baseCost: 50, costGrowth: 1.5, effect: .passiveRate(1)),
            Upgrade(name: "Smart Logistics", description: "Increase efficiency of all income.", baseCost: 120, costGrowth: 1.45, effect: .efficiency(0.15))
        ]
        startTimer()
    }

    func manualCollect() {
        let gained = coinsPerTap * efficiency
        coins += gained
    }

    func purchase(upgrade: Upgrade) {
        guard let index = upgrades.firstIndex(where: { $0.id == upgrade.id }) else { return }
        let currentLevel = upgrades[index].level
        let nextCost = upgrade.cost(forNextLevel: currentLevel)
        guard coins >= nextCost else { return }
        coins -= nextCost
        upgrades[index].level += 1
        apply(effect: upgrade.effect)
    }

    func projectedIncomePerSecond() -> Double {
        let tapIncome = coinsPerTap * efficiency * 2
        return passiveRate * efficiency + tapIncome
    }

    private func startTimer() {
        timer = Timer.publish(every: 0.5, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] now in
                self?.tick(now: now)
            }
    }

    private func tick(now: Date) {
        let delta = now.timeIntervalSince(lastTick)
        lastTick = now
        let gained = passiveRate * efficiency * delta
        coins += gained
    }

    private func apply(effect: UpgradeEffect) {
        switch effect {
        case .tapMultiplier(let value):
            coinsPerTap *= value
        case .passiveRate(let value):
            passiveRate += value
        case .efficiency(let value):
            efficiency += value
        }
    }
}
