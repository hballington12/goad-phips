from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                          QPushButton, QMessageBox, QLabel, QTextEdit, QHBoxLayout,
                          QTabWidget, QFileDialog)
from PyQt6.QtCore import Qt, QProcess, pyqtSignal, QTimer
import sys
import os
import json
from components.command_manager import CommandManager
from components.plotting import PlottingWidget
from components.obj_viewer import OBJViewer

# Path for storing settings
SETTINGS_FILE = os.path.expanduser("~/Documents/work/post-doc/phips/app/light-scattering-app/settings.json")
DEFAULT_OUTPUT_DIR = "goad_run"  # Default directory where mueller_scatgrid is written

# Add this line to track the rotated.obj file path
OBJ_FILE = "rotated.obj"

class TerminalLogger(QTextEdit):
    """A terminal-style logger widget that displays command output"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            background-color: #1E1E1E;
            color: #FFFFFF;
            font-family: Menlo, Monaco, Courier, monospace;
            font-size: 11px;
        """)
        self.setPlaceholderText("Command output will appear here...")

    def append_output(self, text, error=False):
        """Append output text to the terminal with optional error styling"""
        if error:
            self.append(f'<span style="color: #FF5555;">{text}</span>')
        else:
            self.append(text)
        # Auto-scroll to the bottom
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def clear_output(self):
        """Clear the terminal output"""
        self.clear()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Light Scattering App")
        self.setGeometry(100, 100, 900, 600)  # Increased size for plot

        # Default output paths
        self.mueller_file = os.path.join(DEFAULT_OUTPUT_DIR, "mueller_scatgrid")
        self.bins_file = "phips_bins.toml"
        self.obj_file = OBJ_FILE  # Add the OBJ file path

        # Create the command manager
        self.cmd_manager = CommandManager(SETTINGS_FILE, self)
        
        # Connect command manager signals
        self.cmd_manager.command_started.connect(self.on_command_started)
        self.cmd_manager.command_output.connect(self.on_command_output)
        self.cmd_manager.command_finished.connect(self.on_command_finished)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()

        # Add title and description
        title_label = QLabel("Goad Light Scattering Tool")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        main_layout.addWidget(title_label)
        
        desc_label = QLabel("Run the Goad light scattering computation tool and visualize results")
        main_layout.addWidget(desc_label)
        main_layout.addSpacing(5)

        # Command input pre-filled with default command
        command_label = QLabel("Command:")
        main_layout.addWidget(command_label)
        
        # Create command input UI components
        command_input, button_layout = self.cmd_manager.create_ui()
        main_layout.addWidget(command_input)
        
        # Add buttons
        self.plot_button = QPushButton("Plot Results", self)
        self.plot_button.clicked.connect(self.plot_results)
        
        # Add 3D view button
        self.view_3d_button = QPushButton("View 3D Model", self)
        self.view_3d_button.clicked.connect(self.view_3d_model)
        self.view_3d_button.setEnabled(os.path.exists(self.obj_file))
        
        # Clear terminal button
        self.clear_button = QPushButton("Clear Terminal", self)
        self.clear_button.clicked.connect(self.clear_terminal)
        
        # Add buttons to layout
        button_layout.addWidget(self.plot_button)
        button_layout.addWidget(self.view_3d_button)
        button_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(button_layout)
        
        # Create tabs for terminal, plot, and 3D view
        self.tabs = QTabWidget()
        
        # Terminal tab
        self.terminal_tab = QWidget()
        terminal_layout = QVBoxLayout()
        
        # Terminal logger in first tab
        self.terminal = TerminalLogger(self)
        terminal_layout.addWidget(self.terminal)
        self.terminal_tab.setLayout(terminal_layout)
        
        # Plot tab
        self.plot_tab = QWidget()
        plot_layout = QVBoxLayout()
        
        # Create plotting widget
        self.plotting = PlottingWidget(self)
        plot_layout.addWidget(self.plotting)
        
        # Add save plot button
        save_plot_layout = QHBoxLayout()
        self.save_plot_button = QPushButton("Save Plot", self)
        self.save_plot_button.clicked.connect(self.save_plot)
        save_plot_layout.addStretch()
        save_plot_layout.addWidget(self.save_plot_button)
        plot_layout.addLayout(save_plot_layout)
        
        self.plot_tab.setLayout(plot_layout)
        
        # 3D view tab
        self.model_tab = QWidget()
        model_layout = QVBoxLayout()
        
        # Create 3D viewer widget
        self.obj_viewer = OBJViewer(self)
        model_layout.addWidget(self.obj_viewer)
        
        # Add 3D viewer controls
        controls_layout = QHBoxLayout()
        controls_layout.addStretch()
        
        # Load model button
        self.load_model_button = QPushButton("Load OBJ File", self)
        self.load_model_button.clicked.connect(self.load_obj_file)
        controls_layout.addWidget(self.load_model_button)
        
        # Instruction label
        instructions = QLabel("Drag to rotate, scroll to zoom")
        instructions.setStyleSheet("font-style: italic; color: #888888;")
        controls_layout.addWidget(instructions)
        
        model_layout.addLayout(controls_layout)
        self.model_tab.setLayout(model_layout)
        
        # Add tabs to widget
        self.tabs.addTab(self.terminal_tab, "Terminal Output")
        self.tabs.addTab(self.plot_tab, "Scatter Plot")
        self.tabs.addTab(self.model_tab, "3D Model")
        
        main_layout.addWidget(self.tabs)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)
        
    def on_command_started(self, command):
        """Handle command started event"""
        self.terminal.clear_output()
        self.terminal.append_output(f"> {command}")
        self.terminal.append_output("Running command...\n")
        
    def on_command_output(self, text, is_error):
        """Handle command output event"""
        self.terminal.append_output(text, is_error)
        
    def on_command_finished(self, exit_code):
        """Handle command finished event"""
        if exit_code == 0:
            self.terminal.append_output("\nCommand completed successfully.", False)
            
            # Check if output files exist
            has_mueller = os.path.exists(self.mueller_file)
            has_obj = os.path.exists(self.obj_file)
            
            if has_mueller:
                self.terminal.append_output(f"Found output file: {self.mueller_file}", False)
                self.plot_button.setEnabled(True)
                
                # Automatically plot the results
                self.terminal.append_output("Generating plot automatically...", False)
                self.plot_results()
            else:
                self.terminal.append_output(f"Output file not found: {self.mueller_file}", True)
                self.terminal.append_output("Cannot generate plot: Output file not found.", True)
                self.plot_button.setEnabled(False)
            
            # Check for 3D model file
            if has_obj:
                self.terminal.append_output(f"Found 3D model file: {self.obj_file}", False)
                self.view_3d_button.setEnabled(True)
            else:
                self.terminal.append_output(f"3D model file not found: {self.obj_file}", True)
                self.view_3d_button.setEnabled(False)
                
        else:
            self.terminal.append_output(f"\nCommand failed with exit code: {exit_code}", True)
            self.plot_button.setEnabled(False)
            self.view_3d_button.setEnabled(False)
        
    def clear_terminal(self):
        """Clear the terminal output"""
        self.terminal.clear_output()
    
    def plot_results(self):
        """Plot the results from the mueller_scatgrid file"""
        # Switch to the plot tab
        self.tabs.setCurrentIndex(1)
        
        # Process and plot the data
        success, message = self.plotting.process_and_plot_data(self.mueller_file, self.bins_file)
        
        if success:
            self.terminal.append_output("Plot generated successfully.")
            self.terminal.append_output(message)
        else:
            self.terminal.append_output(f"Error generating plot: {message}", True)
            self.tabs.setCurrentIndex(0)  # Switch back to terminal to show error
    
    def view_3d_model(self):
        """View the 3D model from rotated.obj"""
        # Switch to the 3D model tab
        self.tabs.setCurrentIndex(2)
        
        # Load the model if it exists
        if os.path.exists(self.obj_file):
            success, message = self.obj_viewer.load_obj(self.obj_file)
            if success:
                self.terminal.append_output(f"3D model loaded successfully: {message}")
            else:
                self.terminal.append_output(f"Error loading 3D model: {message}", True)
                self.tabs.setCurrentIndex(0)  # Switch back to terminal to show error
        else:
            self.terminal.append_output(f"3D model file not found: {self.obj_file}", True)
            self.tabs.setCurrentIndex(0)  # Switch back to terminal to show error
    
    def load_obj_file(self):
        """Open a file dialog to load an OBJ file"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "Load OBJ File", "", "OBJ Files (*.obj);;All Files (*)"
        )
        
        if file_path:
            success, message = self.obj_viewer.load_obj(file_path)
            if success:
                self.terminal.append_output(f"3D model loaded from {file_path}: {message}")
                # Update the current obj file path
                self.obj_file = file_path
                self.view_3d_button.setEnabled(True)
            else:
                self.terminal.append_output(f"Error loading 3D model: {message}", True)
    
    def save_plot(self):
        """Save the plot to a file"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            self, "Save Plot", "", "PNG Files (*.png);;All Files (*)"
        )
        
        if file_path:
            success, message = self.plotting.save_plot(file_path)
            if success:
                self.terminal.append_output(message)
            else:
                self.terminal.append_output(message, True)

if __name__ == "__main__":
    # # Enable high DPI scaling
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    # # Use OpenGL for rendering
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseDesktopOpenGL, True)
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())