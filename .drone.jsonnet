local Pipeline(py_version) = {
  kind: "pipeline",
  name: "tests (Python " + py_version + ")",
  steps: [
    {
      name: "test",
      image: "python:" + py_version,
      commands: [
        "pip install .",
        "pip install -r requirements-dev.txt",
        "nosetests"
      ]
    }
  ]
};

[
  Pipeline("2.7"),
  Pipeline("3.4"),
  Pipeline("3.5"),
  Pipeline("3.6"),
  Pipeline("3.7"),
  {
    kind: "pipeline",
    name: "upload release",
    trigger: {
      event: ['tag'],
    },
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
