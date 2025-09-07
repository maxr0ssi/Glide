// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "GlideHUD",
    platforms: [
        .macOS(.v12)
    ],
    products: [
        .executable(
            name: "GlideHUD",
            targets: ["GlideHUD"]
        )
    ],
    targets: [
        .executableTarget(
            name: "GlideHUD",
            path: "Sources/GlideHUD"
        )
    ]
)