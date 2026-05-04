{
  description = "IIoT Прототип системи керування ферментацією комбучі - Середовище розробника";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-25.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs {
        system = system;
        config.allowUnfree = true; # Дозволяємо unfree пакети, якщо знадобляться драйвери
      };
    in {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          # 1. Тулчейн для прошивки та розробки ESP32
          platformio
          esptool

          # 2. Інструменти автоматизації оточення та ШІ
          direnv
          nix-direnv
          gemini-cli
          tree

          # 3. Робота з мережею та MQTT брокером
          mosquitto
        ];

        shellHook = ''
          echo "========================================================"
          echo "  Екосистема розробника IIoT CPS успішно активована!    "
          echo "  Доступні команди: pio, esptool, mosquitto_sub, gemini-cli"
          echo "========================================================"
        '';
      };
    };
}