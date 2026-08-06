{ lib, pkgs, ... }:
{
  packages = with pkgs; [
    docker
    gcc
    gnumake
    # decky
    (import ./packages/decky-cli/package.nix pkgs)
  ];

  languages = {
    javascript = {
      enable = true;
      package =
        pkgs."nodejs_${
          lib.pipe (builtins.readFile ./.nvmrc) [
            lib.trim
            lib.versions.major
          ]
        }";
      pnpm = {
        enable = true;
        install.enable = true;
      };
    };

    python = {
      enable = true;
      version = "3.14";
    };
  };
}
