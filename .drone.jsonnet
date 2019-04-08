local Pipeline(py_version) = {
  kind: "pipeline",
  name: "tests (Python " + py_version + ")",
  steps: [
    {
      name: "test",
      image: "python:" + py_version + "-alpine",
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
]
