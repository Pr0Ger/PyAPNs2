local Pipeline(name, image) = {
  kind: "pipeline",
  name: name,
  steps: [
    {
      name: "test",
      image: image,
      commands: [
        "pip install .",
        "pip install -r requirements-dev.txt",
        "nosetests"
      ]
    }
  ]
};

[
  Pipeline("python-2", "python:2"),
  Pipeline("python-3.3", "python:3.3"),
  Pipeline("python-3.4", "python:3.4"),
  Pipeline("python-3.5", "python:3.5"),
  Pipeline("python-3.6", "python:3.6"),
  Pipeline("python-3.7", "python:3.6"),
]
