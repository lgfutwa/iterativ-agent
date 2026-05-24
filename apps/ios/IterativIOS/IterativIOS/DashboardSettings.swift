import Foundation

@MainActor
final class DashboardSettings: ObservableObject {
    @Published var dashboardURLString: String {
        didSet {
            UserDefaults.standard.set(dashboardURLString, forKey: Self.urlKey)
        }
    }

    @Published var lastError: String?

    private static let urlKey = "dashboardURLString"
    private static let defaultURL = "http://127.0.0.1:9119"

    init() {
        dashboardURLString = UserDefaults.standard.string(forKey: Self.urlKey) ?? Self.defaultURL
    }

    var dashboardURL: URL? {
        URL(string: dashboardURLString.trimmingCharacters(in: .whitespacesAndNewlines))
    }

    var displayHost: String {
        dashboardURL?.host(percentEncoded: false) ?? "not set"
    }

    func reset() {
        dashboardURLString = Self.defaultURL
        lastError = nil
    }
}
