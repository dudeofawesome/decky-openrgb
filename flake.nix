{
  description = "Decky Loader plugin for applying OpenRGB profiles";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

  outputs =
    { nixpkgs, ... }:
    let
      lib = nixpkgs.lib;

      supportedSystems = [
        "aarch64-darwin"
        "aarch64-linux"
        "x86_64-linux"
      ];

      forAllSystems = nixpkgs.lib.genAttrs supportedSystems;
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = import nixpkgs { inherit system; };
          nodeVersion = nixpkgs.lib.pipe (builtins.readFile ./.nvmrc) [
            nixpkgs.lib.trim
            nixpkgs.lib.versions.major
          ];
          decky-openrgb = import ./packages/decky-openrgb/package.nix {
            inherit (nixpkgs) lib;
            inherit pkgs;
            nodejs = pkgs."nodejs_${nodeVersion}";
          };
        in
        {
          inherit decky-openrgb;
          default = decky-openrgb;
        }
      );

      nixosModules.default = {
        imports = [
          ./modules/decky-openrgb.nix
        ];
      };
    };
}
