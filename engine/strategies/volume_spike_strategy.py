class VolumeSpikeStrategy:
    def __init__(self, window=20, spike_multiplier=2):
        self.window = window
        self.spike_multiplier = spike_multiplier
        self.volumes = []

    def evaluate(self, market_data):
        volume = market_data.get("volume")
        price = market_data.get("price")

        if volume is None or price is None:
            return {"action": "hold"}

        self.volumes.append(volume)

        if len(self.volumes) < self.window:
            return {"action": "hold"}

        avg_volume = sum(self.volumes[-self.window:]) / self.window

        if volume > avg_volume * self.spike_multiplier:
            return {"action": "buy"}
        else:
            return {"action": "hold"}
