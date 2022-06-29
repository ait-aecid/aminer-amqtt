class BasePlugin() :
    def __init__(self,options):
        """
        Constructor for the plugin
        """
        self.options = options

    def decode(self,payload):
        """
        This method decodes the payload.
        @param payload the payload to decode.
        """
