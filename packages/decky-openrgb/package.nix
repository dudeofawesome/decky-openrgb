{
  lib,
  pkgs,
  config,
  ...
}:
let
  manifest = builtins.fromJSON (builtins.readFile ../../package.json);
  pname = manifest.name;
  inherit (manifest) version;

  source = lib.fileset.toSource {
    root = ../../.;
    fileset = lib.fileset.unions [
      ../../LICENSE
      ../../README.md
      ../../assets
      ../../defaults
      ../../main.py
      ../../package.json
      ../../plugin.json
      ../../pnpm-lock.yaml
      (lib.fileset.fileFilter (file: file.hasExt "py") ../../py_modules)
      ../../rollup.config.js
      ../../src
      ../../tsconfig.json
    ];
  };
in
pkgs.stdenvNoCC.mkDerivation {
  inherit pname source version;
  src = source;

  pnpmDeps = pkgs.fetchPnpmDeps {
    inherit pname version;
    src = source;
    fetcherVersion = 4;
    hash = "sha256-JoruBItrmp8RbSO5muVIZePd+avsC7vhjJTC4xsAe/c=";
  };

  nativeBuildInputs = [
    config.languages.javascript.package
    pkgs.pnpm
    pkgs.pnpmConfigHook
    pkgs.unzip
    pkgs.zip
  ];

  buildPhase = ''
    runHook preBuild
    pnpm run build
    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall

    pluginRoot="$TMPDIR/${pname}"
    mkdir -p "$pluginRoot" "$out"
    cp -R dist py_modules assets "$pluginRoot/"
    cp LICENSE README.md main.py package.json plugin.json "$pluginRoot/"
    cp -R defaults/. "$pluginRoot/"

    find "$pluginRoot" -exec touch -h -d '@1' {} +
    (
      cd "$TMPDIR"
      zip -X -q -r "$out/${pname}-${version}.zip" "$pname"
    )

    runHook postInstall
  '';

  doInstallCheck = true;
  installCheckPhase = ''
    runHook preInstallCheck

    archive="$out/${pname}-${version}.zip"
    entries="$(mktemp)"
    unzip -Z1 "$archive" > "$entries"

    for required in \
      "${pname}/dist/index.js" \
      "${pname}/main.py" \
      "${pname}/py_modules/backend.py" \
      "${pname}/package.json" \
      "${pname}/plugin.json" \
      "${pname}/LICENSE"
    do
      grep -Fxq "$required" "$entries"
    done

    if grep -Evq "^${pname}(/|$)" "$entries"
    then
      echo "distribution contains more than one top-level path" >&2
      exit 1
    fi

    if grep -Eq \
      "(^|/)(src|tests|node_modules|__pycache__)(/|$)|^${pname}/(\.devenv|devenv\.nix)" \
      "$entries"
    then
      echo "distribution contains development-only files" >&2
      exit 1
    fi

    runHook postInstallCheck
  '';
}
