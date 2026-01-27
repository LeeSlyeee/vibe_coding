// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MindDiaryApp",
    platforms: [
        .macOS(.v14),
        .iOS(.v17)
    ],
    products: [
        .executable(name: "MindDiaryApp", targets: ["MindDiaryApp"])
    ],
    dependencies: [
        .package(url: "https://github.com/ml-explore/mlx-swift.git", from: "0.10.0"),
        // Assuming mlx-swift-lm is available separately. If not found, compilation will fail and I'll adjust.
        // Based on search results, it IS separate.
        // Wait, search result said: "MLXLMCommon has been relocated to a dedicated GitHub repository called mlx-swift-lm".
        // URL: https://github.com/ml-explore/mlx-swift-lm
        // Versions: Likely started at 0.0.1 or similar recently.
        .package(url: "https://github.com/ml-explore/mlx-swift-lm.git", branch: "main")
    ],
    targets: [
        .executableTarget(
            name: "MindDiaryApp",
            dependencies: [
                .product(name: "MLX", package: "mlx-swift"),
                .product(name: "MLXRandom", package: "mlx-swift"),
                .product(name: "MLXLMCommon", package: "mlx-swift-lm"),
                .product(name: "MLXLLM", package: "mlx-swift-lm")
            ],
            path: ".",
            exclude: [
                "Assets", 
                "create_appicon.py", 
                "create_assets.py", 
                "make_icons.py"
            ],
            resources: [
                .process("Assets.xcassets")
            ]
        )
    ]
)
