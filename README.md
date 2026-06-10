# qsm

A queued state machine implementation for Python.

A queued state machine is a small workflow runner where each state can schedule
the next states to run. Instead of returning a single transition, states add
state names to a queue. The machine dequeues one state at a time, executes it,
and keeps going until the queue is empty.

Use `append()` for normal follow-up work. Use `prepend()` when a state needs to
run before the work that is already waiting.

## Quickstart

```python
from qsm import QSM, State, StateContext


class Start(State):
    def execute(self, ctx: StateContext) -> None:
        ctx.context["name"] = "World"
        ctx.queue.append("hello")
        ctx.queue.append("goodbye")


class Hello(State):
    def execute(self, ctx: StateContext) -> None:
        print(f"Hello {ctx.context['name']}!")


class Goodbye(State):
    def execute(self, ctx: StateContext) -> None:
        print(f"Goodbye {ctx.context['name']}!")


machine = QSM(initial_context={})
machine.state_map["initial_state"] = Start()
machine.state_map["hello"] = Hello()
machine.state_map["goodbye"] = Goodbye()
machine.loop()
```

Output:

```text
Hello World!
Goodbye World!
```

The execution order is:

1. `start`
2. `hello`
3. `goodbye`

## Prepending Work

`prepend()` places a state at the front of the queue. This is useful for urgent
or corrective work that should run before older queued states.

```python
from qsm import State, StateContext


class Check(State):
    def execute(self, ctx: StateContext) -> None:
        if ctx.context["needs_login"]:
            ctx.queue.prepend("login")
        ctx.queue.append("continue")
```

If the queue already contains `["later"]`, this state can schedule `login` to
run before `later`.

## API

### `QSM`

```python
QSM(initial_context=None, initial_state="initial_state", max_queue_size=None)
```

`QSM` owns the state queue, the registered states, and shared workflow context.

- `machine.state_map` maps state names to `State` instances.
- `machine.queue.append("state")` schedules normal work.
- `machine.queue.prepend("state")` schedules work at the front of the queue.
- `machine.get_next_state()` dequeues the next state name and updates
  `machine.current_state`.
- `machine.execute_state("state")` executes a registered state by name.
- `machine.execute_current_state()` executes `machine.current_state`.
- `machine.loop()` executes queued states until the queue is empty. It starts from a good state, it flushes the queue and enqueues the machine's initial state unless `flush` is `False`. Use `flush=False` to allow yourself to prime the queue prior to calling.

### `State`

Create states by subclassing `State` and implementing `execute()`.

```python
from qsm import State, StateContext


class Example(State):
    def execute(self, ctx: StateContext):
        ...
```

`execute()` receives a `StateContext` with:

- `ctx.queue`: the queue used to schedule more states.
- `ctx.context`: the shared context object passed to `QSM`.

## Notes

The queue stores state names as strings and is based on Python's `queue.Queue`
locking model. It supports max-size blocking behavior, `append()`, and
`prepend()`.
