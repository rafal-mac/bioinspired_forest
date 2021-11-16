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

#need to research the speed of fire spreading in bushes, water, forests so 
# we know what constants to implement in the code

CHAPARRAL = 0
LAKE = 1
FOREST = 2
CANYON = 3
BURNING = 4
BURNED = 5
OBJECT = 6

burn_time_chaparral = 60
burn_time_forest = 400
burn_time_canyon = 5

# starting grid
global start_grid
start_grid = np.zeros((100, 100), dtype=int)
start_grid[30:40, 15:20] = LAKE
start_grid[65:70, 60:90] = LAKE
start_grid[40:80, 20:25] = FOREST
start_grid[10:60, 30:40] = FOREST
start_grid[50:60, 40:100] = FOREST
start_grid[10:90, 25:30] = CANYON
start_grid[40, 10] = BURNING
start_grid[40, 90] = BURNING
start_grid[75:80 ,50:55] = OBJECT

def transition_func(grid, neighbourstates, neighbourcounts, burning_state):
    print(burning_state)
    # dead = state == 0, live = state == 1
    # unpack state counts for state 0 and state 1
    #dead_neighbours, live_neighbours = neighbourcounts
    # create boolean arrays for the birth & survival rules
    # if 3 live neighbours and is dead -> cell born
    #birth = (live_neighbours == 3) & (grid == 0)
    burning_cells = grid==4
    burning_state[burning_cells] -= 1

    burnt = burning_cells & (burning_state == 0)
    print(burnt)

    # CHANGEEEEEE
    x = np.random.rand(100, 100)

    for neigbhourstate in neighbourstates:
        start_burning_chaparal = (grid == 0) & (neigbhourstate == 4) & (x > 0.3)
        start_burning_forest = (grid == 2) & (neigbhourstate == 4) & (x > 0.3)
        start_burning_canyon = (grid == 3) & (neigbhourstate == 4) & (x > 0.3)

        grid[start_burning_chaparal | start_burning_forest | start_burning_canyon] = 4
    # if 2 or 3 live neighbours and is alive -> survives
    #survive = ((live_neighbours == 2) | (live_neighbours == 3)) & (grid == 1)
    # Set all cells to 0 (dead)
    # Set cells to 1 where either cell is born or survives
    
    grid[burnt]=BURNED

    return grid


def setup(args):
    config_path = args[0]
    config = utils.load(config_path)
    config.title = "Forest fire model"
    config.dimensions = 2
    config.states = (CHAPARRAL, LAKE, FOREST, CANYON, BURNING,BURNED,OBJECT)
    config.state_colors = [(0.8,0.8,0),(0.2,0.6,1), (0, 0.4, 0), (1, 1, 0.2), (1, 0, 0),(0.4,0.4,0.4),(0,0,0)]
    config.num_generations = 100
    config.grid_dims = (100,100)
    config.set_initial_grid(start_grid)

    if len(args) == 2:
        config.save()
        sys.exit()

    return config


def main():
    # Open the config object
    config = setup(sys.argv[1:])

    burning_state = np.zeros(config.grid_dims)
    burning_state[start_grid == 0] = burn_time_chaparral
    burning_state[start_grid == 2] = burn_time_forest
    burning_state[start_grid == 3] = burn_time_canyon
    
    # Create grid object
    grid = Grid2D(config, (transition_func, burning_state))

    # Run the CA, save grid state every generation to timeline
    timeline = grid.run()

    # save updated config to file
    config.save()
    # save timeline to file
    utils.save(timeline, config.timeline_path)


if __name__ == "__main__":
    main()
