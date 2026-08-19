{
  lib,
  pkgs,
  config,
  options,
  ...
}:
let
  has_jovian = options ? jovian.enable;
in
{
  options = {
    jovian.decky-loader.modules.openrgb = {
      enable = lib.mkEnableOption "openrgb plugin";
      package = lib.mkPackageOption pkgs "decky-openrgb" {
        default = [ "decky-openrgb" ];
      };
      openrgbPackage = lib.mkPackageOption pkgs "openrgb" {
        default = [ "openrgb" ];
      };
    };
  };

  config =
    let
      cfg = config.jovian.decky-loader;
    in
    lib.mkIf (has_jovian && cfg.enable) {
      systemd.services.decky-loader.path = lib.mkIf (cfg.modules.openrgb.enable) [
        cfg.modules.openrgb.openrgbPackage
      ];
    };
}
