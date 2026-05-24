// swift-tools-version: 5.9

import PackageDescription

let package = Package(
    name: "IterativMac",
    platforms: [
        .macOS(.v13)
    ],
    products: [
        .executable(name: "IterativMac", targets: ["IterativMac"])
    ],
    targets: [
        .executableTarget(
            name: "IterativMac",
            path: "Sources/IterativMac"
        )
    ]
)
