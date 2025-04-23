import os
import json
from PyQt6.QtWidgets import (QLineEdit, QMessageBox, QPushButton, QHBoxLayout, 
                           QVBoxLayout, QLabel, QDoubleSpinBox, QCheckBox, 
                           QGroupBox, QFormLayout, QWidget)
from PyQt6.QtCore import QProcess, QTimer, pyqtSignal, QObject, Qt

class CommandManager(QObject):
    """Manages command input, settings, and execution"""
    
    # Define signals for command events
    command_started = pyqtSignal(str)  # Signal when command starts (sends command string)
    command_output = pyqtSignal(str, bool)  # Signal for command output (text, is_error)
    command_finished = pyqtSignal(int)  # Signal when command completes (exit code)
    
    def __init__(self, settings_file, parent=None):
        super().__init__(parent)
        self.settings_file = settings_file
        
        # Default command values
        self.factory_default_command = os.path.expanduser("~/Documents/work/rust/goad/target/release/goad --help")
        self.default_command = self.factory_default_command
        
        # Default angle values
        self.use_discrete_angles = False
        self.alpha_value = 0.0
        self.beta_value = 0.0
        self.gamma_value = 0.0
        
        # Load settings
        self.load_settings()
        
        # Process for running commands
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._process_finished)
        self.process.errorOccurred.connect(self._process_error)
        
        self.input = None  # Will be set to QLineEdit when create_ui is called
        self.run_button = None  # Will be set to QPushButton when create_ui is called
        
    def create_ui(self):
        """Create the UI components for command input and execution"""
        # Create main command layout
        main_command_layout = QVBoxLayout()
        
        # Command input for entering commands
        self.input = QLineEdit()
        self.input.setText(self.default_command)
        main_command_layout.addWidget(self.input)
        
        # Create a horizontal layout for the three columns
        three_column_layout = QHBoxLayout()
        
        # === COLUMN 1: Angle Controls ===
        angle_column = QVBoxLayout()
        
        # Create angle inputs group
        angle_group = QGroupBox("Orientation")
        angle_layout = QVBoxLayout()
        angle_layout.setContentsMargins(5, 5, 5, 5)  # Reduced margins
        
        # Checkbox to enable/disable discrete angles
        self.discrete_checkbox = QCheckBox("Use discrete angles")
        self.discrete_checkbox.setChecked(self.use_discrete_angles)
        self.discrete_checkbox.stateChanged.connect(self._toggle_discrete_angles)
        angle_layout.addWidget(self.discrete_checkbox)
        
        # Form layout for angle inputs
        form_layout = QFormLayout()
        form_layout.setSpacing(5)  # Reduced spacing

        # Set the default spin box step size
        STEP_SIZE = 1
        
        # Create spin boxes for angles
        self.alpha_input = QDoubleSpinBox()
        self.alpha_input.setRange(0, 360)
        self.alpha_input.setValue(self.alpha_value)
        self.alpha_input.setSingleStep(STEP_SIZE)
        self.alpha_input.setDecimals(1)
        self.alpha_input.setEnabled(self.use_discrete_angles)
        
        self.beta_input = QDoubleSpinBox()
        self.beta_input.setRange(0, 360)
        self.beta_input.setValue(self.beta_value)
        self.beta_input.setSingleStep(STEP_SIZE)
        self.beta_input.setDecimals(1)
        self.beta_input.setEnabled(self.use_discrete_angles)
        
        self.gamma_input = QDoubleSpinBox()
        self.gamma_input.setRange(0, 360)
        self.gamma_input.setValue(self.gamma_value)
        self.gamma_input.setSingleStep(STEP_SIZE)
        self.gamma_input.setDecimals(1)
        self.gamma_input.setEnabled(self.use_discrete_angles)
        
        # Add fields to form layout
        form_layout.addRow("α (°):", self.alpha_input)
        form_layout.addRow("β (°):", self.beta_input)
        form_layout.addRow("γ (°):", self.gamma_input)
        angle_layout.addLayout(form_layout)
        
        # Add a preview label
        self.angle_preview = QLabel("--discrete 0.0,0.0,0.0")
        self.angle_preview.setStyleSheet("color: gray; font-style: italic; font-size: 10px;")
        self.angle_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        angle_layout.addWidget(self.angle_preview)
        
        # Connect value changed signals
        self.alpha_input.valueChanged.connect(self._update_angle_preview)
        self.beta_input.valueChanged.connect(self._update_angle_preview)
        self.gamma_input.valueChanged.connect(self._update_angle_preview)
        
        # Update the preview initially
        self._update_angle_preview()
        
        # Set the layout on the group box
        angle_group.setLayout(angle_layout)
        angle_column.addWidget(angle_group)
        
        # Add stretcher to fill vertical space
        angle_column.addStretch()
        
        # === COLUMN 2: Empty for now ===
        column2 = QVBoxLayout()
        column2_group = QGroupBox("Column 2")
        column2_layout = QVBoxLayout()
        column2_layout.addWidget(QLabel("Reserved for future controls"))
        column2_group.setLayout(column2_layout)
        column2.addWidget(column2_group)
        column2.addStretch()
        
        # === COLUMN 3: Empty for now ===
        column3 = QVBoxLayout()
        column3_group = QGroupBox("Column 3")
        column3_layout = QVBoxLayout()
        column3_layout.addWidget(QLabel("Reserved for future controls"))
        column3_group.setLayout(column3_layout)
        column3.addWidget(column3_group)
        column3.addStretch()
        
        # Add the three columns to the horizontal layout
        three_column_layout.addLayout(angle_column, 1)  # 1/3 of space
        three_column_layout.addLayout(column2, 1)       # 1/3 of space
        three_column_layout.addLayout(column3, 1)       # 1/3 of space
        
        # Add the three-column layout to the main layout
        main_command_layout.addLayout(three_column_layout)
        
        # Create a widget for the command input and angles
        command_widget = QWidget()
        command_widget.setLayout(main_command_layout)
        
        # Create button layout
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 5, 0, 0)
        
        # Set button style for more compact buttons
        button_style = """
            QPushButton {
                padding: 4px 8px;
                font-size: 11px;
            }
        """
        
        # Reset button goes back to the saved default
        self.reset_button = QPushButton("Reset")
        self.reset_button.setStyleSheet(button_style)
        self.reset_button.clicked.connect(self.reset_command)
        self.reset_button.setToolTip("Reset to saved default command")
        
        # Save as default button to store the current command
        self.save_default_button = QPushButton("Save Default")
        self.save_default_button.setStyleSheet(button_style)
        self.save_default_button.clicked.connect(self.save_as_default)
        self.save_default_button.setToolTip("Save current command as default")
        
        # Factory reset button to restore original default
        self.factory_reset_button = QPushButton("Factory Reset")
        self.factory_reset_button.setStyleSheet(button_style)
        self.factory_reset_button.clicked.connect(self.factory_reset)
        self.factory_reset_button.setToolTip("Reset to factory default")
        
        # Run button
        self.run_button = QPushButton("Run Command")
        self.run_button.setStyleSheet(button_style)
        self.run_button.clicked.connect(self.run_command)
        
        # Add buttons to layout
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.save_default_button)
        button_layout.addWidget(self.factory_reset_button)
        button_layout.addStretch(1)  # Add stretch to push run button to the right
        button_layout.addWidget(self.run_button)
        
        # Return the input widget and button layout
        return command_widget, button_layout
    
    def _toggle_discrete_angles(self, state):
        """Enable or disable angle inputs based on checkbox state"""
        enabled = (state == Qt.CheckState.Checked.value)
        self.use_discrete_angles = enabled
        
        self.alpha_input.setEnabled(enabled)
        self.beta_input.setEnabled(enabled)
        self.gamma_input.setEnabled(enabled)
        self.angle_preview.setEnabled(enabled)
        
        # Update the preview text color based on enabled state
        if enabled:
            self.angle_preview.setStyleSheet("color: black; font-style: normal;")
        else:
            self.angle_preview.setStyleSheet("color: gray; font-style: italic;")
            
        self._update_angle_preview()
    
    def _update_angle_preview(self):
        """Update the angle preview label"""
        alpha = self.alpha_input.value()
        beta = self.beta_input.value()
        gamma = self.gamma_input.value()
        
        # Save current values
        self.alpha_value = alpha
        self.beta_value = beta
        self.gamma_value = gamma
        
        preview_text = f"--discrete {alpha:.1f},{beta:.1f},{gamma:.1f}"
        self.angle_preview.setText(preview_text)
    
    def reset_command(self):
        """Reset command to current default"""
        if self.input:
            self.input.setText(self.default_command)
    
    def save_as_default(self):
        """Save current command as new default"""
        if not self.input:
            return
            
        new_default = self.input.text()
        if not new_default:
            QMessageBox.warning(None, "Input Error", "Please enter a command before saving as default.")
            return
        
        self.default_command = new_default
        self._save_settings()
        self.command_output.emit("Default command saved successfully.", False)
        
    def factory_reset(self):
        """Reset to the factory default command"""
        self.default_command = self.factory_default_command
        if self.input:
            self.input.setText(self.default_command)
        self._save_settings()
        self.command_output.emit("Command reset to factory default.", False)
    
    def run_command(self):
        """Run the command in the input field"""
        if not self.input:
            return
            
        command_text = self.input.text()
        if not command_text:
            QMessageBox.warning(None, "Input Error", "Please enter a command.")
            return
        
        # Add discrete angles if enabled
        if self.use_discrete_angles:
            alpha = self.alpha_input.value()
            beta = self.beta_input.value()
            gamma = self.gamma_input.value()
            angle_arg = f"--discrete {alpha:.1f},{beta:.1f},{gamma:.1f}"
            
            # Append to command text if not already present
            if "--discrete" not in command_text:
                command_text = f"{command_text} {angle_arg}"
            else:
                # Replace existing --discrete parameter
                parts = command_text.split()
                for i, part in enumerate(parts):
                    if part == "--discrete" and i + 1 < len(parts):
                        parts[i + 1] = f"{alpha:.1f},{beta:.1f},{gamma:.1f}"
                        break
                    elif part.startswith("--discrete="):
                        parts[i] = f"--discrete={alpha:.1f},{beta:.1f},{gamma:.1f}"
                        break
                command_text = " ".join(parts)
            
        # Disable run button during process execution
        if self.run_button:
            self.run_button.setEnabled(False)
        
        # Emit signal that command has started
        self.command_started.emit(command_text)
        
        # Split the command into program and arguments
        parts = command_text.split()
        program = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # Set up process properly
        self.process.setProgram(program)
        self.process.setArguments(args)
        
        # Start the process - properly separated now
        self.command_output.emit(f"Executing: {program} with args: {' '.join(args)}\n", False)
        self.process.start()
        
        # Set a timeout - add a safeguard to prevent infinite hanging
        QTimer.singleShot(100000, self._check_process_timeout)
    
    def load_settings(self):
        """Load application settings from JSON file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                    self.default_command = settings.get('default_command', self.factory_default_command)
                    
                    # Load angle settings if present
                    self.use_discrete_angles = settings.get('use_discrete_angles', False)
                    self.alpha_value = settings.get('alpha_value', 0.0)
                    self.beta_value = settings.get('beta_value', 0.0)
                    self.gamma_value = settings.get('gamma_value', 0.0)
            else:
                self.default_command = self.factory_default_command
        except Exception as e:
            print(f"Error loading settings: {str(e)}")
            self.default_command = self.factory_default_command
    
    def _save_settings(self):
        """Save application settings to JSON file"""
        try:
            settings = {
                'default_command': self.default_command,
                'use_discrete_angles': self.use_discrete_angles,
                'alpha_value': self.alpha_value,
                'beta_value': self.beta_value,
                'gamma_value': self.gamma_value
            }
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.settings_file), exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
                
            return True
        except Exception as e:
            self.command_output.emit(f"Error saving settings: {str(e)}", True)
            return False
    
    def _check_process_timeout(self):
        """Check if the process is still running after timeout"""
        if self.process.state() == QProcess.ProcessState.Running:
            self.command_output.emit("\nProcess seems to be taking too long. It might be hanging.", True)
            self.command_output.emit("You can terminate it by closing the app or running a new command.", True)
    
    def _handle_stdout(self):
        """Handle standard output data from the process"""
        data = self.process.readAllStandardOutput().data().decode('utf-8', errors='replace')
        self.command_output.emit(data, False)
        
    def _handle_stderr(self):
        """Handle standard error data from the process"""
        data = self.process.readAllStandardError().data().decode('utf-8', errors='replace')
        self.command_output.emit(data, True)
        
    def _process_finished(self, exit_code, exit_status):
        """Called when the process finishes"""
        if exit_code == 0:
            self.command_output.emit("\nCommand completed successfully.", False)
        else:
            self.command_output.emit(f"\nCommand failed with exit code: {exit_code}", True)
            
        # Re-enable run button
        if self.run_button:
            self.run_button.setEnabled(True)
            
        # Emit finished signal
        self.command_finished.emit(exit_code)
    
    def _process_error(self, error):
        """Handle process errors"""
        error_messages = {
            QProcess.ProcessError.FailedToStart: "Failed to start: The process failed to start.",
            QProcess.ProcessError.Crashed: "Process crashed: The process crashed after starting successfully.",
            QProcess.ProcessError.Timedout: "Timeout: The process timed out.",
            QProcess.ProcessError.ReadError: "Read error: An error occurred when reading from the process.",
            QProcess.ProcessError.WriteError: "Write error: An error occurred when writing to the process.",
            QProcess.ProcessError.UnknownError: "Unknown error: An unknown error occurred."
        }
        
        error_message = error_messages.get(error, f"Process error: {error}")
        self.command_output.emit(error_message, True)
        
        # Re-enable run button
        if self.run_button:
            self.run_button.setEnabled(True)