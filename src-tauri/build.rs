use std::{env, fs, path::PathBuf};

fn main() {
    ensure_debug_sidecar_placeholder();
    tauri_build::build()
}

fn ensure_debug_sidecar_placeholder() {
    let profile = env::var("PROFILE").unwrap_or_default();
    if profile == "release" {
        return;
    }

    let target = match env::var("TARGET") {
        Ok(target) => target,
        Err(_) => return,
    };

    let manifest_dir = PathBuf::from(
        env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR is required by Cargo"),
    );
    let extension = if target.contains("windows") { ".exe" } else { "" };
    let sidecar_path = manifest_dir
        .join("binaries")
        .join(format!("cutmate-api-{target}{extension}"));

    println!("cargo:rerun-if-changed={}", sidecar_path.display());
    if sidecar_path.exists() {
        return;
    }

    let parent = sidecar_path
        .parent()
        .expect("sidecar path should have a parent directory");
    fs::create_dir_all(parent).expect("failed to create debug sidecar directory");
    fs::write(
        sidecar_path,
        b"Debug-only placeholder. Release builds must provide the real CutMate API sidecar.\n",
    )
    .expect("failed to create debug sidecar placeholder");
}
