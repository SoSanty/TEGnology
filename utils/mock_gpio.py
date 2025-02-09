class MockGPIO:
    BCM = "BCM"
    OUT = "OUT"
    
    def setmode(self, mode):
        print(f"Setting mode to {mode}")

    def setup(self, pin, mode):
        print(f"Setting up pin {pin} as {mode}")

    def output(self, pin, state):
        print(f"Setting pin {pin} to {'HIGH' if state else 'LOW'}")

    def cleanup(self):
        print("Cleaning up GPIO")
