class PiNode:
    def __init__(self, ip_address, width, height, innitial_x=0, innitial_y=0):
        self.ip_address = ip_address
        self.width = width
        self.height = height
        self.initial_x = innitial_x
        self.initial_y = innitial_y
        self.screen_name = 'No name'
        self.connection = None

    def __init__(self, ip_address, screen_name):
        self.ip_address = ip_address
        self.screen_name = str(screen_name)

    def __init__(self, connection, ip_address):
        self.ip_address = ip_address
        self.connection = connection

    def set_initialPoint(self, initial_x, initial_y):
        # starting points, top left coordinate (x,y)
        self.initial_x = initial_x
        self.initial_y = initial_y

    def set_address(self, new_address):
        self.ip_address = new_address

    def set_resolution(self, new_width, new_height):
        self.width = new_width
        self.height = new_height

    def set_name(self, name):
        self.screen_name = name

    def get_address(self):
        return self.ip_address

    def get_connection(self):
        return self.connection

    def get_resolution(self):
        return self.width, self.height

    def get_name(self):
        return self.screen_name
