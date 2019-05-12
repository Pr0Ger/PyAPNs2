local Pipeline(py_version) = {
  kind: "pipeline",
  name: "tests (Python " + py_version + ")",
  steps: [
    {
      name: "test",
      image: "python:" + py_version,
      [if py_version == "2.7" then "failure" else null]: "ignore",
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
      # We are ignoring 2.7 since it's randomly fails because of certificate_transparency module
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
