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
TOWN = 6

burn_time_chaparral = 60
burn_time_forest = 400
burn_time_canyon = 5

# TRUE for fire starting at the incinerator
start_at_incinerator = True
# TRUE for fire starting at the power plant
start_at_power_plant = False

# starting grid
global start_grid
start_grid = np.zeros((100, 100), dtype=int)

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
    start_grid[40, 10] = BURNING
if start_at_power_plant:
    start_grid[40, 90] = BURNING
start_grid[75:80, 50:55] = TOWN


def transition_func(grid, neighbourstates, neighbourcounts, burning_state):
    burning_cells = grid == BURNING
    burning_state[burning_cells] -= 1

    burnt = burning_cells & (burning_state == 0)

    x = np.random.rand(100, 100)

    for neigbhourstate in neighbourstates:
        start_burning_chaparal = (grid == CHAPARRAL) & (neigbhourstate
                                                        == BURNING) & (x > 0.3)
        start_burning_forest = (grid == FOREST) & (neigbhourstate
                                                   == BURNING) & (x > 0.7)
        start_burning_canyon = (grid == CANYON) & (neigbhourstate
                                                   == BURNING) & (x > 0.9)
        start_burning_town = (grid == TOWN) & (neigbhourstate
                                               == BURNING) & (x > 0.9)

        grid[start_burning_chaparal | start_burning_forest
             | start_burning_canyon | start_burning_town] = BURNING

    grid[burnt] = BURNED

    return grid


def setup(args):
    config_path = args[0]
    config = utils.load(config_path)
    config.title = "Forest fire model"
    config.dimensions = 2
    config.states = (CHAPARRAL, LAKE, FOREST, CANYON, BURNING, BURNED, TOWN)
    config.state_colors = [(0.8, 0.8, 0), (0.2, 0.6, 1), (0, 0.4, 0),
                           (1, 1, 0.2), (1, 0, 0), (0.4, 0.4, 0.4), (0, 0, 0)]
    config.num_generations = 100
    config.grid_dims = (100, 100)
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

    # Prints the generation when the town catches fire
    is_town_on_fire = False
    for index, generation in enumerate(timeline, start = 0):
        if (BURNING in generation[75:80, 50:55]) & (not is_town_on_fire):
            is_town_on_fire = True
            print("Town on fire, generation - " + str(index))

    # save updated config to file
    config.save()
    # save timeline to file
    utils.save(timeline, config.timeline_path)


if __name__ == "__main__":
    main()
