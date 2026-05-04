# nixos-rebuild switch --flake .#rpi3b-lab --target-host lab
# ssh lab 'sudo reboot'
# ssh lab 'fastfetch'

{ config, pkgs, lib, ... }:
{
  system.stateVersion = "25.11";

  networking.hostName = "rpi3b-lab";
  networking.useDHCP = true;

  networking.firewall.allowedTCPPorts = [ 1883 ];

  services.openssh = {
    enable = true;
    settings = {
      PermitRootLogin = "prohibit-password";
      PasswordAuthentication = false;
    };
  };

  users.users.root.openssh.authorizedKeys.keys = [
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMHVs1ILK0/WogD9WXoTD2rNqiXuC54SU0fx83OFXKZG rpi3b-lab-key"
  ];

  zramSwap = {
    enable = true;
    algorithm = "zstd";
    memoryPercent = 70;
    priority = 100;
  };
  
  environment.systemPackages = with pkgs; [ 
    neovim 
    git 
    btop 
    fastfetch
    zellij
  ];

  services.mosquitto = {
    enable = true;
    listeners = [ {
      acl = [ "pattern readwrite #" ];
      address = "0.0.0.0";
      port = 1883;
      settings.allow_anonymous = true;
    } ];
  };

  time.timeZone = "Europe/Kyiv";

  nix.settings.experimental-features = [ "nix-command" "flakes" ];

  nix.settings.auto-optimise-store = true;
  nix.gc = {
    automatic = true;
    dates = "weekly";
    options = "--delete-older-than 7d";
  };
}
