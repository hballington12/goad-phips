import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QWidget, QVBoxLayout
import os
import toml

class PlottingWidget(QWidget):
    """Widget for plotting light scattering data"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(300)
        
        # Default constants from phips_goad.py
        self.wavelength = 0.532  # Default wavelength in microns
        self.waveno = 2 * np.pi / self.wavelength
        
        # Default settings for PHIPS bins
        self.num_detectors = 20
        self.phips_start = 18
        self.phips_end = 170
        self.bin_width = 8
        
        # Reference data file
        self.reference_data_file = "Plate_Crystal_IMPACTS2022_RF02_3606.txt"
        
        # Setup the figure canvas
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)
        
        # Setup layout
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        # Clear the plot initially
        self.clear_plot()
    
    def clear_plot(self):
        """Clear the plot"""
        self.axes.clear()
        self.axes.set_title("No data loaded")
        self.axes.set_xlabel("Scattering Angle (degrees)")
        self.axes.set_ylabel("Mean DSCS")
        self.canvas.draw()
    
    def read_mueller_scatgrid(self, filename='goad_run/mueller_scatgrid'):
        """Read the mueller_scatgrid file and return as numpy array"""
        if not os.path.exists(filename):
            return None, f"Error: Mueller scatgrid file {filename} not found"
            
        try:
            data = np.loadtxt(filename)
            return data, f"Successfully loaded {filename} with shape {data.shape}"
        except Exception as e:
            return None, f"Error reading {filename}: {str(e)}"
    
    def process_and_plot_data(self, data_file, bins_file=None):
        """Process and plot the mueller scatgrid data with reference data if available"""
        # If bins_file is provided, use it, otherwise use default PHIPS binning
        data, message = self.read_mueller_scatgrid(data_file)
        
        if data is None:
            self.clear_plot()
            return False, message
        
        try:
            # Process data here...
            # Divide the third column of the data by the dscs conversion factor
            processed_data = data.copy()
            processed_data[:, 2] *= 1e-12 / self.waveno**2
            
            # If we have a bins file, use those bins
            if bins_file and os.path.exists(bins_file):
                with open(bins_file, 'r') as f:
                    bins_data = toml.load(f)
                    
                if 'bins' not in bins_data:
                    return False, f"Error: No 'bins' key in {bins_file}"
                    
                phips_bins = np.array(bins_data['bins'])
                # Additional custom binning code would go here
            
            # Create default binning based on PHIPS settings
            theta = np.linspace(self.phips_start, self.phips_end, self.num_detectors)
            values = np.zeros_like(theta)
            
            # For each bin, find data points within this angular range and average them
            bin_values_log = []
            for i in range(len(theta)):
                half_width = self.bin_width / 2
                indices = np.where((processed_data[:, 0] >= theta[i]-half_width) & 
                                 (processed_data[:, 0] < theta[i]+half_width))
                
                if len(indices[0]) > 0:
                    values[i] = np.mean(processed_data[indices, 2])
                    bin_values_log.append(f"Bin {i}: theta={theta[i]:.1f}°, {len(indices[0])} points, mean S11={values[i]:.6e}")
                else:
                    bin_values_log.append(f"Bin {i}: theta={theta[i]:.1f}°, no data points found")
            
            # Generate the plot
            self.axes.clear()
            
            # Plot the computed data in blue
            self.axes.plot(theta, values, 'o-', markersize=8, color='b', label='GOAD')
            
            # Replace the reference file section in process_and_plot_data
            reference_file = self.reference_data_file
            if os.path.exists(reference_file):
                try:
                    # Load reference data with tab separator, skipping comment lines
                    ref_data = np.loadtxt(reference_file, comments='//')
                    
                    # Extract angles and values
                    ref_angles = ref_data[:, 0]
                    ref_values = ref_data[:, 1]
                    
                    # Plot reference data in red
                    self.axes.plot(ref_angles, ref_values, 's-', markersize=6, color='r', 
                                  label='PHIPS (IMPACTS2022)')
                    
                    bin_values_log.append("\nReference data from IMPACTS2022 also plotted")
                except Exception as e:
                    bin_values_log.append(f"\nError loading reference data: {str(e)}")
            else:
                bin_values_log.append(f"\nReference data file '{reference_file}' not found")
            
            # Complete the plot formatting
            self.axes.set_xlabel('Scattering Angle (degrees)')
            self.axes.set_ylabel('Mean DSCS')
            self.axes.set_title('PHIPS Scattering Intensity vs. Angle')
            self.axes.grid(True, which='both', linestyle='--', linewidth=0.5)
            self.axes.legend()
            self.axes.set_yscale('log')
            self.figure.tight_layout()
            self.canvas.draw()
            
            return True, "\n".join(bin_values_log)
            
        except Exception as e:
            self.clear_plot()
            import traceback
            return False, f"Error processing data: {str(e)}\n{traceback.format_exc()}"

    def save_plot(self, filename='phips_scattering.png'):
        """Save the plot to a file"""
        try:
            self.figure.savefig(filename)
            return True, f"Plot saved to {filename}"
        except Exception as e:
            return False, f"Error saving plot: {str(e)}"