# Function

```python
from typing import Literal


def get_current_weather(location: str, format: Literal["fahrenheit", "celsius"]):
    """
    Get the current weather
    :param location: The city and state, e.g. San Francisco, CA
    :param format: The temperature unit to use. Infer this from the users location.
    """
```

```
[
    {
        'name': 'get_current_weather',
        'description': 'Get the current weather',
        'parameters': {
            'type': 'object',
            'properties': {
                'location': {
                    'description': 'The city and state, e.g. San Francisco, CA',
                    'type': 'string'
                },
                'format': {
                    'description': 'The temperature unit to use. Infer this from
the users location.',
                    'type': 'string',
                    'enum': ('fahrenheit', 'celsius')
                }
            }
        },
        'required': ['location', 'format']
    }
]

```

```python
example_messages = [
    {
        "role": "system",
        "content": "You are a helpful, pattern-following assistant that translates corporate jargon into plain English.",
    },
    {
        "role": "system",
        "name": "example_user",
        "content": "New synergies will help drive top-line growth.",
    },
    {
        "role": "system",
        "name": "example_assistant",
        "content": "Things working well together will increase revenue.",
    },
    {
        "role": "system",
        "name": "example_user",
        "content": "Let's circle back when we have more bandwidth to touch base on opportunities for increased leverage.",
    },
    {
        "role": "system",
        "name": "example_assistant",
        "content": "Let's talk later when we're less busy about how to do better.",
    },
    {
        "role": "user",
        "content": "This late pivot means we don't have time to boil the ocean for the client deliverable.",
    },
]
```