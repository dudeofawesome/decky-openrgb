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
  ];

  buildPhase = ''
    runHook preBuild
    pnpm run build
    runHook postBuild
  '';

  installPhase = ''
    runHook preInstall

    mkdir -p "$out"
    cp -R dist py_modules assets "$out/"
    cp LICENSE README.md main.py package.json plugin.json "$out/"
    cp -R defaults/. "$out/"

    runHook postInstall
  '';

  doInstallCheck = true;
  installCheckPhase = ''
    runHook preInstallCheck

    for required in \
      "dist/index.js" \
      "main.py" \
      "py_modules/backend.py" \
      "package.json" \
      "plugin.json" \
      "LICENSE"
    do
      test -f "$out/$required"
    done

    test ! -e "$out/.devenv"
    test ! -e "$out/devenv.nix"

    if find "$out" -type d \( \
      -name src -o \
      -name tests -o \
      -name node_modules -o \
      -name __pycache__ \
    \) -print -quit | grep -q .
    then
      echo "distribution contains development-only directories" >&2
      exit 1
    fi

    if find "$out" -type f -name '*.zip' -print -quit | grep -q .
    then
      echo "distribution contains a ZIP archive" >&2
      exit 1
    fi

    runHook postInstallCheck
  '';
}
