import json
import logging

from asyncio_mqtt.client import Client, MqttError
from contextlib import AsyncExitStack

from mesh import Node
from tools import Tasks

from .bridges import light


BRIDGES = {
    "light": light.GenericLightBridge,
}


class HassMqttMessenger:
    """
    Provides home assistant specific MQTT functionality

    Manages a set of bridges for specific device types and
    manages tasks to receive and handle incoming messages.
    """

    def __init__(self, config, nodes):
        self._config = config
        self._nodes = nodes
        self._bridges = {}
        self._paths = {}

        self._client = Client(
            self._config.require("mqtt.broker"),
            username=self._config.optional("mqtt.username"),
            password=self._config.optional("mqtt.password"),
        )
        self._topic = config.optional("mqtt.topic", "mqtt_mesh")

        # initialize bridges
        for name, constructor in BRIDGES.items():
            self._bridges[name] = constructor(self)

    @property
    def client(self):
        return self._client

    @property
    def topic(self):
        return self._topic

    def node_topic(self, component, node):
        """
        Return base topic for a specific node
        """
        if isinstance(node, Node):
            node = node.config.require("id")

        return f"homeassistant/{component}/{self._topic}/{node}"

    def filtered_messages(self, component, node, topic="#"):
        """
        Shorthand to get messages for a specific node
        """
        return self._client.filtered_messages(f"{self.node_topic(component, node)}/{topic}")

    async def publish(self, component, node, topic, message, **kwargs):
        """
        Send a state update for a specific nde
        """
        if isinstance(message, dict):
            message = json.dumps(message)

        await self._client.publish(f"{self.node_topic(component, node)}/{topic}", str(message).encode(), **kwargs)

    async def run(self, app):
        async with AsyncExitStack() as stack:
            tasks = await stack.enter_async_context(Tasks())

            while True:
                try:
                    # connect to MQTT broker
                    await stack.enter_async_context(self._client.connect())

                    # spawn tasks for every node
                    for node in self._nodes.all():
                        bridge = self._bridges.get(node.type)

                        if bridge is None:
                            logging.warning(f"No MQTT bridge for node {node} ({node.type})")
                            return

                        tasks.spawn(bridge.listen(node), f"bridge {node}")

                    # global subscription to messages
                    await self._client.subscribe("homeassistant/#")

                    # wait for all tasks
                    await tasks.gather()

                except MqttError:
                    logging.warning("Lost connection to MQTT broker")
                    await asyncio.sleep(10)
                    continue

                except asyncio.CancelledError:
                    logging.debug("Run task cancelled")
                    return