import numpy as np
import matplotlib.pyplot as plt

# FIRE CURVE MODULE
class ISO834:
    def __init__(self, t):
        self.time = t
    def firetemp(self):
        return 20 + 345 * np.log10(8 * self.time + 1)
    
class ASTME119:
    def __init__(self, t):
        self.time = t
    def firetemp(self):
        return 20 + 750 * (1 - np.exp(-3.79553 * np.sqrt(self.time/60))) + 170.41 * np.sqrt(self.time/60)
    
class External:
    def __init__(self, t):
        self.time = t
    def firetemp(self):
        return 20 + 660 * (1 - 0.686 * np.exp(-0.32 * self.time) - 0.313 * np.exp(-3.8 * self.time))

class Hydrocarbon:
    def __init__(self, t):
        self.time = t
    def firetemp(self):
        return 20 + 1080 * (1 - 0.325 * np.exp(-0.167 * self.time) - 0.675 * np.exp(-2.5 * self.time))
    
# time
t = np.linspace(0, 180, 180) # Time in minutes

# instances
curve1 = ISO834(t)
curve2 = ASTME119(t)
curve3 = External(t)
curve4 = Hydrocarbon(t)

# temperatures
temp1 = curve1.firetemp()
temp2 = curve2.firetemp()
temp3 = curve3.firetemp()
temp4 = curve4.firetemp()

# plot temperatures
plt.figure()
plt.plot(t, temp1, 'r', label='Standard Fire Curve (ISO834)')
plt.plot(t, temp2, 'g', label='ASTM E119 Fire Curve')
plt.plot(t, temp3, 'b', label='External Fire Curve')
plt.plot(t, temp4, 'm', label='Hydrocarbon Fire Curve')

plt.xlabel('Time (minutes)')
plt.ylabel('Gas Temperature (°C)')
plt.title('Published Fire Curves')
plt.legend()
plt.grid(True)
plt.show()