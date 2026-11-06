"""Short counterfactual fixtures for tests (gate_override=True). Real cases are 150-300 words and written by people."""
from sakshi.counterfactual import Case

P1 = ("Rahul visited a hill station in the story. At the hill station the water boiled at 90 degrees Celsius. "
      "The cook waited a long time for the rice to soften. Everyone was surprised that the pot bubbled so early.")
P2 = ("The village fair is held in the month of Magha each year. Families bring sweets and lanterns to the fair. "
      "Children play games near the old temple. The fair ends with a boat race on the river.")
P3 = ("In 1887 the town built a stone bridge over the river. Farmers carried grain across the bridge every week. "
      "The bridge stood firm through many floods. Children still walk across the bridge to school.")

def cases():
    return [
        Case("boil", P1, 1, "90 degrees Celsius", "100 degrees Celsius", "number", "dev"),
        Case("fair", P2, 0, "Magha", "Diwali", "name", "dev"),
        Case("bridge", P3, 0, "1887", "1950", "number", "heldout"),
    ]
