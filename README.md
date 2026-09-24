# Adaptive Agricultural Multi-Agent System

Multi-agent simulation for studying adaptive agricultural settlement using Markov decision processes, Q-learning, procedural seed/food generation, terrain data and community dynamics.

The project contains several model versions that share the same core agent and environment components. **Model 3** extends the simulation with colony formation and the separation of communities into **Hanan** and **Hurin** roles.

## Project structure

```text
Final/
├── base_agent.py
├── markov.py
├── DataMapLoad.py
├── Procedural_Seed_Evolution_System.py
├── test.py
├── model 1/
│   ├── model1_functions.py
│   └── Visualizer.py
├── model 2/
│   ├── model2_functions.py
│   └── Visualizer_2.py
├── model 3/
│   ├── model3_function.py
│   └── Visualizer_3.py
└── models.zip
```

### Core components

- **`base_agent.py`**: community and civilization structures, population/calorie management, memory, reproduction and other agent-level operations.
- **`markov.py`**: construction of the environment transition model, Q-tables, action selection and Markov/Q-learning processes.
- **`DataMapLoad.py`**: downloads and processes elevation data, detects the lake region and generates the simulation grid and neighborhood relations.
- **`Procedural_Seed_Evolution_System.py`**: generates seed varieties, food and height-dependent agricultural information used by the agents.
- **`Visualizer*.py`**: visualization of simulation state, visits, communities and colonies.

## Models

### Model 1

Baseline community simulation. Communities interact with the terrain and agricultural system while learning through the Markov/Q-learning process. Community reproduction is included.

Run from the `Final` directory:

```bash
python "model 1/model1_functions.py"
```

### Model 2

Extends the baseline with additional community information exchange and interaction zones between communities.

```bash
python "model 2/model2_functions.py"
```

### Model 3

Extends the previous model with colony mechanics. A community can establish a colony composed of two specialized sub-communities:

- **Hanan**: associated with exploration and territorial expansion.
- **Hurin**: associated with agricultural analysis and cultivation within the colony.

The colony uses a shared state/Q-table representation while the global environment remains available for terrain and height information.

```bash
python "model 3/model3_function.py"
```

## Installation

The project uses Python and the following main external libraries:

```bash
pip install numpy pandas matplotlib scipy rasterio bmi-topography
```

Depending on the local environment, `rasterio` may require platform-specific installation support.

## Terrain data and OpenTopography

`DataMapLoad.py` obtains a **COP30 DEM** through OpenTopography and converts the downloaded terrain into the simulation grid.

Before running the simulation, configure the OpenTopography API key in `DataMapLoad.py` or, preferably, replace the hard-coded key with an environment-variable based configuration.

**Security:** do not commit a real API key to a public GitHub repository. Revoke/rotate any key that has already been exposed publicly.

The grid configuration currently covers the selected area around Lake Titicaca and uses a simulation cell size of 1250 m.

## Simulation flow

At a high level, the models follow this process:

```text
Terrain / DEM
     ↓
Simulation grid
     ↓
Agent initialization
     ↓
Seed / food system
     ↓
Markov transitions + Q-learning
     ↓
Cultivation / movement / interactions
     ↓
Population and resource updates
     ↓
Visualization and experiment output
```

Model 3 adds:

```text
Community
    ↓
Colony establishment
    ↓
Hanan + Hurin
    ↓
Shared colony state / Q-table
    ↓
Exploration + cultivation + colony dynamics
```

## Output files

The simulations generate experiment data such as:

```text
agent_learning_seed_data.csv
```

This file can become very large because it is written during repeated simulation runs. **Do not commit generated CSV data of this type to Git when it exceeds repository limits.** Add generated outputs to `.gitignore` when they are not required as source files.

Example:

```gitignore
agent_learning_seed_data.csv
__pycache__/
*.pyc
```

## Reproducibility notes

The simulation uses stochastic processes, including random seed generation, action selection and probabilistic state transitions. Repeated runs can therefore produce different results unless randomness is explicitly controlled with fixed seeds.

For research use, record the model version, parameter values, number of iterations, number of repetitions and random-seed configuration for each experiment.

## Main parameters in Model 3

Current colony parameters are defined near the top of `model 3/model3_function.py`:

```python
FINAL_MAX_DISTANCE = 4
INITIAL_MAX_DISTANCE = 2
BETA = 0.6
ALPHA = 0.6
GAMMA = 0.6
```

These values control colony distance limits and learning-related parameters in the current implementation.

## Research context

The codebase is intended as an experimental multi-agent framework for investigating agricultural adaptation, settlement and community dynamics in an Andean environmental setting. It combines:

- terrain-dependent environmental conditions;
- agent learning through Q-values;
- probabilistic movement transitions;
- procedural seed and food generation;
- population and resource dynamics;
- community interaction;
- colony formation and specialization in Model 3.

The implementation is experimental and under active development. Model behavior, assumptions and parameters should therefore be interpreted together with the corresponding research documentation and experiment definitions.

## Notes

- Run scripts from the `Final` directory so that the module imports resolve as expected.
- The `__pycache__` directories are Python-generated artifacts and are not required to run the source code.
- `models.zip` is a nested archive included in the current project package.
- The generated terrain requires internet access and a valid OpenTopography configuration.

