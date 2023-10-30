let
    pkgs = (import (builtins.fetchTarball {
        url = "https://github.com/NixOS/nixpkgs/archive/a7ecde854aee5c4c7cd6177f54a99d2c1ff28a31.zip";
        sha256 = "162dywda2dvfj1248afxc45kcrg83appjd0nmdb541hl7rnncf02";
    }) { });
    stdenv = pkgs.stdenv;
in pkgs.mkShell rec {
    shellHook = ''
        source .bashrc
    '';
    buildInputs = (with pkgs; [
        bashInteractive
        (pkgs.python3.buildEnv.override {
            ignoreCollisions = true;
            extraLibs = with pkgs.python3.pkgs; [
                feedgen
                markdown
            ];
        })
    ]);
}