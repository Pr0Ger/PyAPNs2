local Pipeline(py_version) = {
  kind: "pipeline",
  name: "tests (Python " + py_version + ")",
  steps: [
    {
      name: "test",
      image: "python:" + py_version,
      commands: [
        "pip install .[tests]",
        "pytest"
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
        image: "pr0ger/drone-mypy",
        settings: {
          strict: true,
          package: "apns2",
        },
      },
    ],
  },
  Pipeline("3.5"),
  Pipeline("3.6"),
  Pipeline("3.7"),
  {
    kind: "pipeline",
    name: "upload release",
    trigger: {
      event: ['tag'],
      status: ['success'],
    },
    depends_on: [
      "tests (Python 3.5)",
      "tests (Python 3.6)",
      "tests (Python 3.7)",
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
