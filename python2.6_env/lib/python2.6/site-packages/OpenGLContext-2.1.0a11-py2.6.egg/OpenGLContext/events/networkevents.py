"""Event classes and manager relating to (PyQNet) networking"""
from OpenGLContext.events import event, eventmanager
    
class NetworkEvent (event.Event):
    """Event received from the network

    attributes:
        type -- "network"
        name -- event type (connect, disconnect, congestion_warning,
            congestion_critical, message, message_acked, message_dropped)
        channel -- network communication channel involved
        message -- message structure from the network (if there is a message)
    """
    type = "network"
    name = ""
    channel = None 
    message = None 
    def getKey (self):
        """Get the event key used to lookup a handler for this event"""
        return self.name, getattr( self.message, 'type' )