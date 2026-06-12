# JSON Configuration

QSM can build a machine from JSON by importing classes from dotted Python paths.
Each configured class receives the values in its `kwargs` object, and configured
states are instantiated before they are placed in `machine.state_map`.

This is useful when you want the workflow wiring to live in a config file while
the actual behavior remains in normal Python classes.

## Config Shape

```json
{
  "initial_state": "start",
  "initial_context": {
    "model": "my_app.workflow.WorkflowContext",
    "kwargs": {
      "name": "World"
    }
  },
  "max_queue_size": 10,
  "states": {
    "start": {
      "model": "my_app.workflow.Start",
      "kwargs": {
        "next_state": "hello"
      }
    },
    "hello": {
      "model": "my_app.workflow.Hello",
      "kwargs": {}
    }
  }
}
```

Top-level fields:

- `initial_state`: state name queued when `machine.loop()` starts with the
  default `flush=True`.
- `initial_context`: optional object shared with every state through
  `ctx.context`.
- `max_queue_size`: optional maximum queue size.
- `states`: mapping of state names to importable `State` classes.

For `initial_context` and every state entry:

- `model` must be a dotted import path to a class.
- `kwargs` are passed to that class constructor.

## Python Classes

Given this module:

```python
# my_app/workflow.py

from qsm import State, StateContext


class WorkflowContext:
    def __init__(self, name: str):
        self.name = name
        self.events: list[str] = []


class Start(State):
    def __init__(self, next_state: str):
        self.next_state = next_state

    def execute(self, ctx: StateContext) -> None:
        ctx.context.events.append("started")
        ctx.queue.append(self.next_state)


class Hello(State):
    def execute(self, ctx: StateContext) -> None:
        ctx.context.events.append(f"hello:{ctx.context.name}")
```

The JSON config above creates:

- a `WorkflowContext(name="World")`
- a `Start(next_state="hello")`
- a `Hello()`

## Loading JSON Text

```python
from qsm import QSM


json_text = """
{
  "initial_state": "start",
  "initial_context": {
    "model": "my_app.workflow.WorkflowContext",
    "kwargs": {
      "name": "World"
    }
  },
  "states": {
    "start": {
      "model": "my_app.workflow.Start",
      "kwargs": {
        "next_state": "hello"
      }
    },
    "hello": {
      "model": "my_app.workflow.Hello",
      "kwargs": {}
    }
  }
}
"""

machine = QSM.from_json_text(json_text)
machine.loop()

assert machine.context.events == ["started", "hello:World"]
```

## Loading A Dictionary

```python
from qsm import QSM


data = {
    "initial_state": "start",
    "initial_context": {
        "model": "my_app.workflow.WorkflowContext",
        "kwargs": {"name": "World"},
    },
    "states": {
        "start": {
            "model": "my_app.workflow.Start",
            "kwargs": {"next_state": "hello"},
        },
        "hello": {
            "model": "my_app.workflow.Hello",
            "kwargs": {},
        },
    },
}

machine = QSM.from_json(data)
```

## Loading A File

```python
from pathlib import Path

from qsm import QSM


machine = QSM.from_config_file(Path("machine.json"))
```

## Requirements

JSON configuration uses Pydantic v2 and the package currently targets Python
3.12 or newer.
