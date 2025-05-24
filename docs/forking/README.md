# Forking Workflow

1. [Fork the repository](https://github.com/home-assistant/intents/fork) on GitHub.
2. Clone your fork locally with `git clone <url>`
3. Set up a local development environment with `script/setup`
4. Create a new branch off of `main` with `git checkout -b <branch>`
5. If your [language code](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) does not exist yet, run `python3 -m script.intentfest add_language <language_code> <language name>`
6. Modify the files for your language in:
    * `sentences/<language>`
    * `tests/<language>`
    * `responses/<language>`
7. Run `script/lint` and `script/test` to ensure everything is working.
    * Make sure you have at least one test sentence for every intent sentence template.
8. Commit and push your changes with `git commit` and `git push`
9. Submit a pull request (PR) with your suggested changes on GitHub.
