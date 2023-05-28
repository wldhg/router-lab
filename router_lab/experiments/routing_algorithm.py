from .__base__ import ExperimentBase


class Experiment(ExperimentBase):
    @property
    def name(self) -> str:
        return "routing_algorithm"

    @property
    def description(self) -> str:
        return "Compare routing algorithms in a simulated network."

    def run(self, *args, **kwargs):
        make_it_route
        pass
