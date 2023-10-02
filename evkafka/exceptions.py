class EVKafkaError(Exception):
    pass


class UndecodedMessageError(EVKafkaError):
    pass
