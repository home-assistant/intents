{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/basics/
  env.GREET = "devenv";

  # https://devenv.sh/packages/
  packages = [ 
    pkgs.git
  ];

  pre-commit.hooks = {
    prettier.enable = true;
    prettier.name = "prettier";
    prettier.types_or = [ "yaml" ];
  };

  # https://devenv.sh/scripts/
  scripts.hello.exec = "echo hello from $GREET";
  scripts.lint.exec = "./script/lint";
  scripts.test.exec = "./script/test";
  scripts.test_file.exec = "./script/test_file";
  scripts.format.exec = "./script/format";

  enterShell = ''
    hello
    git --version
  '';

  # https://devenv.sh/tests/
  enterTest = ''
    lint
    test
  '';

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/languages/
  # languages.nix.enable = true;
  languages.python.enable = true;
  # languages.python.version = "3.11.3";
  languages.python.venv.enable = true;
  languages.python.venv.requirements = ./requirements.txt;

  # https://devenv.sh/pre-commit-hooks/
  # pre-commit.hooks.shellcheck.enable = true;

  # https://devenv.sh/processes/
  # processes.ping.exec = "ping example.com";

  # See full reference at https://devenv.sh/reference/options/
}
