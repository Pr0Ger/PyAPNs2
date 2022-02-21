local Pipeline(py_version) = {
  kind: "pipeline",
  name: "tests (Python " + py_version + ")",
  steps: [
    {
      name: "test",
      image: "python:" + py_version,
      commands: [
        "pip install poetry",
        "poetry install -v",
        "poetry run pytest"
      ]
    }
  ]
};

[
  {
    kind: "pipeline",
    name: "linting",
    steps: [
      {
        name: "mypy",
        image: "pr0ger/drone-pytools",
        pull: "always",
        settings: {
          linter: "mypy",
        },
      },
      {
        name: "pycodestyle",
        image: "pr0ger/baseimage:base.python-3.9",
        commands: [
          "pycodestyle apns2"
        ]
      },
    ],
  },
  Pipeline("3.6"),
  Pipeline("3.7"),
  Pipeline("3.8"),
  {
    kind: "pipeline",
    name: "upload release",
    trigger: {
      event: ['tag'],
      status: ['success'],
    },
    depends_on: [
      "tests (Python 3.6)",
      "tests (Python 3.7)",
      "tests (Python 3.8)",
    ],
    steps: [
      {
        name: "publish",
        image: "plugins/pypi",
        settings: {
          distributions: ["sdist", "bdist_wheel"],
          username: "Pr0Ger",
          password: {
            from_secret: "pypi_password"
          },
        },
      },
    ],
  },
]
