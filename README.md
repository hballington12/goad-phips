# Light Scattering App

This project is a Python application designed to compute light scattering patterns and compare them with measurement data. The application is built using PyQt6 and is structured to maintain modularity, making it easy to extend and maintain.

## Project Structure

```
light-scattering-app
├── src
│   ├── main.py                # Entry point of the application
│   ├── gui                    # Contains GUI related code
│   │   ├── __init__.py
│   │   └── main_window.py      # Main window setup with command input
│   ├── core                   # Core functionalities
│   │   ├── __init__.py
│   │   └── subprocess_runner.py # Handles subprocess execution
│   ├── utils                  # Utility functions
│   │   ├── __init__.py
│   │   └── data_storage.py     # Data storage and retrieval functions
│   └── plotting               # Plotting functionalities
│       ├── __init__.py
│       └── plot_manager.py     # Manages plotting features
├── tests                      # Unit tests for the application
│   ├── __init__.py
│   ├── test_subprocess.py      # Tests for subprocess functionalities
│   └── test_plotting.py        # Tests for plotting functionalities
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

## Installation

To set up the project, clone the repository and install the required dependencies:

```bash
git clone <repository-url>
cd light-scattering-app
pip install -r requirements.txt
```

## Usage

To run the application, execute the following command:

```bash
python src/main.py
```

The application will open a window where you can enter terminal commands and execute them by clicking the button.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.# goad-phips
