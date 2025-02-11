# Name: Forest fire model
# Dimensions: 2

# --- Set up executable path, do not edit ---
import sys
import inspect

this_file_loc = (inspect.stack()[0][1])
main_dir_loc = this_file_loc[:this_file_loc.index('ca_descriptions')]
sys.path.append(main_dir_loc)
sys.path.append(main_dir_loc + 'capyle')
sys.path.append(main_dir_loc + 'capyle/ca')
sys.path.append(main_dir_loc + 'capyle/guicomponents')
# ---

from capyle.ca import Grid2D, Neighbourhood, CAConfig, randomise2d
import capyle.utils as utils
import numpy as np


# ----- PARAMETERS POSSIBLE TO EXPERIMENT WITH -----

# TRUE for fire starting at the incinerator
start_at_incinerator = True
# TRUE for fire starting at the power plant
start_at_power_plant = False

# Determines the timing and location of the water drop
global water_drop
water_drop = {
    'countdown': 40, # generetion when the water will start being dropped
    'x1': 30,
    'x2': 50, # difference between xs determines the width of the drop 
    'y1': 70,
    'y2': 74 # difference between ys determines the height of a single drop 
             # (there's multiple small drops going in the direction away from the town)
}

# Determines the wind direction (values between -0.5 and 0.5)
global wind_direction
wind_direction = [-0.5, 0.5]

# -------------------------------------------------

CHAPARRAL = 0
LAKE = 1
FOREST = 2
CANYON = 3
BURNED = 5
TOWN = 6

# Add multiple levels of burning (the higher the number, the more severe the burning)
BURNING_1 = 7
BURNING_2 = 8
BURNING_3 = 4
BURNING = [
    [BURNING_1, 0.75, 0.9, 0.25, 0.90],
    [BURNING_2, 0.70, 0.85, 0.20, 0.85],
    [BURNING_3, 0.65, 0.8, 0.15, 0.8],
]

global GRID_SIZE
GRID_SIZE = 100

burn_time_chaparral = 32
burn_time_forest = 300
burn_time_canyon = 2

# starting grid
global start_grid
start_grid = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)

# unpenetratable border to contain the fire
start_grid[0:99, 0:1] = BURNED
start_grid[99:100, 0:99] = BURNED
start_grid[1:100, 99:100] = BURNED
start_grid[0:1, 1:100] = BURNED

start_grid[30:40, 15:20] = LAKE
start_grid[65:70, 60:90] = LAKE
start_grid[40:80, 20:25] = FOREST
start_grid[10:60, 30:40] = FOREST
start_grid[50:60, 40:99] = FOREST
start_grid[10:90, 25:30] = CANYON

if start_at_incinerator:
    start_grid[40, 10] = BURNING_3
if start_at_power_plant:
    start_grid[40, 90] = BURNING_3
start_grid[75:80, 50:55] = TOWN

# Create a grid of burning times of each types of terrain
initial_burning_state = np.zeros((GRID_SIZE, GRID_SIZE))
initial_burning_state[start_grid == 0] = burn_time_chaparral
initial_burning_state[start_grid == 2] = burn_time_forest
initial_burning_state[start_grid == 3] = burn_time_canyon

# This burning state will get updated every generation
# and compared to the initial_burning_state for the purposes of updating fire levels
burning_state = np.zeros((GRID_SIZE, GRID_SIZE))
burning_state[start_grid == 0] = burn_time_chaparral
burning_state[start_grid == 2] = burn_time_forest
burning_state[start_grid == 3] = burn_time_canyon

cell_directions = ["NW", "N", "NE", "W", "E", "SW", "S" ,"SE"] 

def transition_func(grid, neighbourstates, neighbourcounts, burning_state, initial_burning_state, wind_direction):
    burning_cells = (grid == BURNING_1) | (grid == BURNING_2) | (grid == BURNING_3)
    burning_state[burning_cells] -= 1

    burnt = burning_cells & (burning_state == 0) 

    counter = 0
    # Introduce probability
    global GRID_SIZE
    x = np.random.rand(GRID_SIZE, GRID_SIZE)

    # Create stronger fire as cells burn
    grid[(grid == BURNING_2) & (burning_state == initial_burning_state - 20)] = BURNING_3

    grid[(grid == BURNING_1) & (burning_state == initial_burning_state - 10)] = BURNING_2


    # Look at each neighbour of each cell separately and determine whether they're on fire.
    # The more cells burning around the target cell, the more chances for it to catch fire.
    for neigbhourstate in neighbourstates:
        
        #probability of setting on fire multiply by factor of wind strength 

        direction_no = counter % 8 
        factor = x 

        #if wind factor exists multiply as appropriate
        if wind_direction[0] != 0:
            if cell_directions[direction_no] == "S" :  
                if wind_direction[0] < 0: 
                    factor = x * wind_direction[0] * -1 
                    #negative values reflecting direction need to be made positive
                else:
                    factor = x *  (1 + wind_direction[0]) 
            if cell_directions[direction_no] == "N" :
                if wind_direction[0] < 0:
                    factor = x * (1 + (wind_direction[0] * -1))
                else:
                    factor = x * wind_direction[0]  #probability decreases if wind in opposite direction        
        
        if wind_direction[1] != 0:
            if  cell_directions[direction_no] == "W":
                if wind_direction[1] < 0:  
                    factor = x * ( -1 * wind_direction[1]) 
                else:
                    factor = x * (1 + wind_direction[1])
            if cell_directions[direction_no] == "E":
                if wind_direction[1] < 0:
                    factor = x * (1 + (wind_direction[1] * -1))
                else:
                    factor = x * wind_direction[1]
        #diagonals considered with both north and east vectors
            
        counter += 1

        for burning_level in BURNING:
            start_burning_chaparal = (grid == CHAPARRAL) & (neigbhourstate
                                                            == burning_level[0]) & (factor > burning_level[1])
            start_burning_forest = (grid == FOREST) & (neigbhourstate
                                                    == burning_level[0]) & (factor > burning_level[2])
            start_burning_canyon = (grid == CANYON) & (neigbhourstate
                                                    == burning_level[0]) & (factor > burning_level[3])
            start_burning_town = (grid == TOWN) & (neigbhourstate
                                                == burning_level[0]) & (factor > burning_level[4])

                
            grid[start_burning_chaparal | start_burning_forest | start_burning_canyon | start_burning_town] = BURNING_1

    global water_drop
    global start_grid
    water_drop['countdown'] -= 1

    # The water is released over the couse of multiple generations,
    # simulating rounds of helicopters flying over a piece of land in the direction away from the town
    if (water_drop['countdown'] <= 0) & (water_drop['countdown'] > -31):
        y1 = water_drop['y1'] + water_drop['countdown']
        y2 = water_drop['y2'] + water_drop['countdown']
        x1 = water_drop['x1']
        x2 = water_drop['x2']

        grid[y1:y2, x1:x2] = start_grid[y1:y2, x1:x2]

    grid[burnt] = BURNED

    return grid


def setup(args):
    config_path = args[0]
    config = utils.load(config_path)
    config.title = "Forest fire model"
    config.dimensions = 2
    config.states = (CHAPARRAL, LAKE, FOREST, CANYON, BURNING_3, BURNED, TOWN, BURNING_1, BURNING_2)
    config.state_colors = [
        (0.8, 0.8, 0),
        (0.2, 0.6, 1),
        (0, 0.4, 0),
        (1, 1, 0.2),
        (1, 0, 0),
        (0.4, 0.4, 0.4), 
        (0, 0, 0),
        (1, 0.4, 0.4),
        (1, 0.2, 0.2),
    ]
    config.num_generations = 100
    config.grid_dims = (GRID_SIZE, GRID_SIZE)
    config.set_initial_grid(start_grid)

    if len(args) == 2:
        config.save()
        sys.exit()

    return config

def main():
    # Open the config object
    config = setup(sys.argv[1:])
    
    # Create grid object
    grid = Grid2D(config, (transition_func, burning_state, initial_burning_state, wind_direction))

    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()

    # Prints the generation when the town catches fire
    for index, generation in enumerate(timeline, start = 0):
        if (BURNING_1 in generation[75:80, 50:55]):
            print("Town on fire, generation - " + str(index))
            break

    # save updated config to file
    config.save()
    # save timeline to file
    utils.save(timeline, config.timeline_path)

if __name__ == "__main__":
    main()
