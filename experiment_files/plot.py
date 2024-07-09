import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager

plt.rcParams['font.sans-serif']=['kaiti']
add_str = "steps"
data_list = np.load("plot_data/"+add_str+"_0709_1.npy")

num = len (data_list)
x = range(num)


# Create graphs and subgraphs
fig, ax1 = plt.subplots()

# Plot the curve of the first array (left y-axis)
ax1.plot(x, data_list, 'y-')
ax1.set_xlabel('training steps')
ax1.set_ylabel('reward', color='y')


tick_font = font_manager.FontProperties(family='DejaVu Sans', size=7.0)
for labelx  in ax1.get_xticklabels():
    labelx.set_fontproperties(tick_font) # Set x-axis scale font
for labely in ax1.get_yticklabels():
    labely.set_fontproperties(tick_font) # Set y-axis scale font

plt.title("Average reward curve chart")
plt.show()