---
doc_id: LG-03
title: LangGraph — State, Reducers, Command & Send
series: LG
product: LangGraph
version_scope: langgraph 1.x
last_verified: 2026-08-13
source_tier: 1
tags: [state, reducers, Annotated, add_messages, MessagesState, Command, Send, map-reduce, fan-out, InvalidUpdateError]
---

# LG-03 — State, Reducers, Command & Send

## LG-03.1 — Default state merge behavior

By default, a node's returned update **overwrites** the corresponding state keys. A node returning `{"count": 3}` replaces whatever `count` held. For single-writer keys this is what you want and needs no configuration.

The default breaks down as soon as two nodes write the same key in the same superstep — the parallel execution described in `LG-02`. LangGraph will not silently choose a winner; it raises `InvalidUpdateError`. Reducers are the mechanism for defining the merge explicitly. **Tier 1** ([Graph API docs](https://docs.langchain.com/oss/python/langgraph/graph-api)).

## LG-03.2 — Reducers via Annotated

A reducer is attached to a state key using `typing.Annotated`, pairing the field's type with a function that combines the current value (left) with the incoming update (right):

```python
from typing import Annotated
from typing_extensions import TypedDict
from operator import add

class State(TypedDict):
    tags: Annotated[list[str], add]  # appends instead of overwriting
```

`operator.add` is the conventional choice for accumulating lists. Any two-argument function works, so custom merge semantics — deduplication, bounded windows, numeric max — are straightforward.

The diagnostic rule worth memorizing: **if you see `InvalidUpdateError` about concurrent updates, the fix is a reducer on the contended key, not a change to your graph topology.**

## LG-03.3 — add_messages and MessagesState

Message accumulation gets a purpose-built reducer, `add_messages`, and a prebuilt state class, `MessagesState`, that applies it to a `messages` key.

`add_messages` does more than append. It performs **ID tracking with overwrite support** — a message re-emitted with an existing ID replaces that message rather than duplicating it — and it handles deserialization, accepting both LangChain message objects and plain dict form.

ID-based overwrite is the enabling mechanism for message editing, summarization, and removal. Combined with `RemoveMessage` and the `REMOVE_ALL_MESSAGES` sentinel (see `LG-05`), it is how conversation history is trimmed or rewritten without rebuilding state by hand.

## LG-03.4 — Command: state update plus control flow

`Command` lets a node return both a state update and a routing decision together:

```python
from typing import Literal
def my_node(state: State) -> Command[Literal["next_node"]]:
    return Command(update={"key": "value"}, goto="next_node")
```

The `Command[Literal[...]]` return annotation declares reachable destinations, which preserves graph analyzability despite routing being decided in-node.

`Command` is also available to **tools**, per `LC-03` — a tool can return a `Command` to update graph state and redirect flow. That is a meaningful capability: it means a tool is not confined to returning data to the model, it can steer the graph directly.

## LG-03.5 — Send: dynamic fan-out for map-reduce

`Send`, imported from `langgraph.types`, enables **variable fan-out** — dispatching a node multiple times with different payloads, where the count is determined at runtime from state:

```python
from langgraph.types import Send
return [Send("node_name", {"subset": item}) for item in state['items']]
```

This is the map-reduce primitive. The distinction from ordinary parallel edges matters: parallel edges are fixed at graph-definition time, whereas `Send` produces a fan-out width computed at runtime from data.

Because the map step produces many concurrent writes to the same key, `Send` and reducers are almost always used together — the reduce half of map-reduce *is* the reducer. A `Send` fan-out without a reducer on the collecting key is a reliable way to produce `InvalidUpdateError`.

## LG-03.6 — Practical state design guidance

Three heuristics follow from the above. **Keep state JSON-serializable**, because it is checkpointed; prefer Pydantic models or plain types over arbitrary objects (`LG-02`, `SH-07`). **Keep large payloads out of state** — the official guidance for big files is external storage such as S3 with only a reference held in state, since checkpointed state is written to the database at every superstep (`LG-04`). And **decide reducers when you design the schema**, not after the first `InvalidUpdateError` — any key that more than one node can write in a superstep needs one.

## Sources

- [Graph API — official docs](https://docs.langchain.com/oss/python/langgraph/graph-api) — accessed 2026-08-13 (Tier 1)
- [LangGraph errors reference](https://tessl.io/registry/tessl/pypi-langgraph/1.0.0/files/docs/errors.md) — accessed 2026-08-13 (Tier 2)
- [Understanding Checkpointers, Databases, API Memory and TTL — LangChain support](https://support.langchain.com/articles/6253531756-understanding-checkpointers-databases-api-memory-and-ttl) — accessed 2026-08-13 (Tier 1)
