# Events

EVKafka works with json encoded objects (dicts). In order to distinguish an event type 
a header `Message-Type` must be supplied alongside with a message at the producer side:

```python
async def produce(event: bytes, event_name: str):
    async with AIOKafkaProducer(...) as producer:
        await producer.send(
            value=event,
            headers=[("Message-Type", event_name.encode())]
        )
    
```