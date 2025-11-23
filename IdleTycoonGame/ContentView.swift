import SwiftUI

struct ContentView: View {
    @EnvironmentObject private var game: GameState
    private let numberFormatter: NumberFormatter = {
        let formatter = NumberFormatter()
        formatter.numberStyle = .decimal
        formatter.maximumFractionDigits = 1
        return formatter
    }()

    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                header
                incomeStats
                tapButton
                upgradeList
                Spacer()
            }
            .padding()
            .navigationTitle("Idle Tycoon")
            .background(Color(.systemGroupedBackground))
            .onAppear { UITableView.appearance().backgroundColor = .clear }
        }
    }

    private var header: some View {
        VStack(spacing: 8) {
            Text("Coins")
                .font(.headline)
            Text(formatted(game.coins))
                .font(.largeTitle.bold())
            Text("Income: \(formatted(game.projectedIncomePerSecond())) / sec")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(RoundedRectangle(cornerRadius: 16).fill(.ultraThickMaterial))
    }

    private var incomeStats: some View {
        HStack(spacing: 16) {
            statTile(title: "Per Tap", value: formatted(game.coinsPerTap * game.efficiency))
            statTile(title: "Passive", value: formatted(game.passiveRate * game.efficiency))
            statTile(title: "Efficiency", value: String(format: "x%.2f", game.efficiency))
        }
    }

    private var tapButton: some View {
        Button(action: { game.manualCollect() }) {
            VStack(spacing: 8) {
                Image(systemName: "hammer.circle.fill")
                    .resizable()
                    .frame(width: 72, height: 72)
                    .foregroundStyle(.orange.gradient)
                Text("Tap to collect")
                    .font(.headline)
                Text("+\(formatted(game.coinsPerTap * game.efficiency))")
                    .font(.subheadline)
            }
            .padding()
            .frame(maxWidth: .infinity)
            .background(RoundedRectangle(cornerRadius: 16).fill(.orange.opacity(0.2)))
        }
        .buttonStyle(.plain)
    }

    private var upgradeList: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Upgrades")
                .font(.headline)
                .frame(maxWidth: .infinity, alignment: .leading)
            ForEach(game.upgrades) { upgrade in
                upgradeCell(for: upgrade)
            }
        }
    }

    private func upgradeCell(for upgrade: Upgrade) -> some View {
        let currentLevel = upgrade.level
        let cost = upgrade.cost(forNextLevel: currentLevel)
        let affordable = game.coins >= cost
        return Button(action: { game.purchase(upgrade: upgrade) }) {
            HStack {
                VStack(alignment: .leading, spacing: 6) {
                    HStack {
                        Text(upgrade.name)
                            .font(.headline)
                        Spacer()
                        Text("Lvl \(upgrade.level)")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                    }
                    Text(upgrade.description)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    Text("Cost: \(formatted(cost)) coins")
                        .font(.footnote.bold())
                        .foregroundStyle(affordable ? .green : .secondary)
                }
                Spacer()
                Image(systemName: "plus.circle.fill")
                    .font(.title)
                    .foregroundStyle(affordable ? Color.green : Color.gray)
            }
            .padding()
            .background(RoundedRectangle(cornerRadius: 14).fill(.ultraThickMaterial))
        }
        .buttonStyle(.plain)
        .disabled(!affordable)
    }

    private func statTile(title: String, value: String) -> some View {
        VStack(spacing: 6) {
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.title3.bold())
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(RoundedRectangle(cornerRadius: 12).fill(.thinMaterial))
    }

    private func formatted(_ value: Double) -> String {
        if value >= 1_000_000 {
            return String(format: "%.2fM", value / 1_000_000)
        } else if value >= 1_000 {
            return String(format: "%.1fk", value / 1_000)
        }

        return numberFormatter.string(from: NSNumber(value: value)) ?? "0"
    }
}

#Preview {
    ContentView()
        .environmentObject(GameState())
}
