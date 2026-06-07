# Конфігурація центрального хаба автоматизації комбучі rpi3b-lab
# Деплой: nixos-rebuild switch --flake .#rpi3b-lab --target-host lab

{ config, pkgs, lib, ... }:
{
  system.stateVersion = "25.11";

  networking.hostName = "rpi3b-lab";
  networking.useDHCP = true;

  networking.firewall.allowedTCPPorts = [ 1883 8000 ];

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
    mosquitto
  ];

  services.tor = {
    enable = true;
    client.enable = true;
    relay.onionServices."kombucha_hub" = {
      map = [ { port = 80; target = { addr = "127.0.0.1"; port = 8000; }; } ];
      version = 3;
    };
  };

  services.mosquitto = {
    enable = true;
    listeners = [ {
      acl = [ "pattern readwrite #" ];
      address = "0.0.0.0";
      port = 1883;
      settings.allow_anonymous = true;
    } ];
  };

  systemd.services.kombucha-cortex = {
    description = "Kombucha Bio-Reactor Core Analytics Layer (FastAPI)";
    after = [ "network.target" "mosquitto.service" ];
    wantedBy = [ "multi-user.target" ];
    
    serviceConfig = {
      Type = "simple";
      WorkingDirectory = "/opt/kombucha-cortex";
      
      # ПОВНІСТЮ ДЕКЛАРАТИВНЕ ОТОЧЕННЯ NIX: Безпечно, ізольовано, збирається миттєво
      ExecStart = let
        pythonEnv = pkgs.python3.withPackages (ps: with ps; [
          fastapi
          uvicorn
          paho-mqtt
          sqlalchemy
          aiosqlite  
          jinja2
          python-multipart
        ]);
      in "${pythonEnv}/bin/uvicorn server:app --host 0.0.0.0 --port 8000";

      Restart = "always";
      RestartSec = "5s";
      User = "root";
      MemoryMax = "500M";
    };
  };

  time.timeZone = "Europe/Kyiv";

  nix.settings.experimental-features = [ "nix-command" "flakes" ];
  nix.settings.auto-optimise-store = true;
}