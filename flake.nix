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
        config.allowUnfree = true;
      };
    in {
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          platformio
          esptool

          (python3.withPackages (ps: with ps; [
            fastapi
            uvicorn
            paho-mqtt
            pydantic
            python-multipart
          ]))

          direnv
          nix-direnv
          gemini-cli
          tree
          mosquitto
        ];
      };
    };
}