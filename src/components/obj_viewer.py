import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QSurfaceFormat
from PyQt6.QtWidgets import QVBoxLayout, QWidget, QLabel, QHBoxLayout
import math
import os

class OBJModel:
    """Class to parse and store OBJ model data"""
    
    def __init__(self, filename=None):
        self.vertices = []
        self.normals = []
        self.faces = []
        if filename:
            self.load(filename)
    
    def load(self, filename):
        """Load an OBJ file"""
        self.vertices = []
        self.normals = []
        self.faces = []
        
        try:
            with open(filename, 'r') as f:
                for line in f:
                    if line.startswith('#'):  # Skip comments
                        continue
                    
                    values = line.split()
                    if not values:
                        continue
                    
                    if values[0] == 'v':  # Vertices
                        vertex = list(map(float, values[1:4]))
                        self.vertices.append(vertex)
                    
                    elif values[0] == 'vn':  # Normals
                        normal = list(map(float, values[1:4]))
                        self.normals.append(normal)
                    
                    elif values[0] == 'f':  # Faces
                        # OBJ faces can have different formats
                        # Here we handle v//vn format (vertex and normal indices)
                        face = []
                        for v in values[1:]:
                            w = v.split('/')
                            if len(w) >= 3:  # v/vt/vn format
                                face.append((int(w[0]) - 1, int(w[2]) - 1 if w[2] else -1))
                            elif len(w) == 2:  # v//vn format
                                face.append((int(w[0]) - 1, int(w[1]) - 1))
                            else:  # v format
                                face.append((int(w[0]) - 1, -1))
                        self.faces.append(face)
            
            return True
        except Exception as e:
            print(f"Error loading OBJ file: {e}")
            return False

class OBJViewer(QOpenGLWidget):
    """OpenGL Widget for rendering OBJ files"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Set OpenGL format for better rendering
        fmt = QSurfaceFormat()
        fmt.setDepthBufferSize(24)
        fmt.setSamples(4)  # Enable antialiasing
        self.setFormat(fmt)
        
        # Initialize parameters
        self.obj_model = OBJModel()
        self.rotation_x = 0.0
        self.rotation_y = 0.0
        self.rotation_z = 0.0  # Added Z rotation
       
        # For orthographic projection, zoom is a scale factor rather than a z-translation
        self.zoom = 2.0  # Default scale (1.0 = 100%)
        
        self.last_pos = QPoint()
        
        # Colors for the model
        self.model_color = (0.7, 0.7, 0.9, 1.0)  # Light blue
        self.background_color = (0.2, 0.2, 0.2, 1.0)  # Dark gray
        
        # Set minimum size to ensure visibility
        self.setMinimumSize(300, 300)
        
        # Allow mouse tracking for interactivity
        self.setMouseTracking(True)
        
        # Initialize model center and size with defaults
        self.model_center = np.array([0.0, 0.0, 0.0])
        self.model_size = 1.0
    
    def load_obj(self, filename):
        """Load an OBJ file and prepare it for rendering"""
        if os.path.exists(filename):
            success = self.obj_model.load(filename)
            if success:
                # Calculate bounds to center the model
                if self.obj_model.vertices:
                    min_bounds = np.min(np.array(self.obj_model.vertices), axis=0)
                    max_bounds = np.max(np.array(self.obj_model.vertices), axis=0)
                    
                    # Center the model and scale it to fit the view
                    self.model_center = (min_bounds + max_bounds) / 2
                    self.model_size = np.max(max_bounds - min_bounds)
                    
                    self.update()  # Trigger a redraw
                    return True, f"Loaded OBJ model with {len(self.obj_model.vertices)} vertices and {len(self.obj_model.faces)} faces"
            
            return False, "Failed to load OBJ file"
        else:
            return False, f"File not found: {filename}"
    
    def initializeGL(self):
        """Initialize OpenGL settings"""
        glClearColor(*self.background_color)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_POSITION, [1.0, 1.0, 1.0, 0.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.2, 0.2, 0.2, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.8, 0.8, 0.8, 1.0])
    
    def resizeGL(self, width, height):
        """Handle widget resize events with orthographic projection"""
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        # Calculate aspect ratio
        aspect = width / height if height > 0 else 1.0
        
        # Use an orthographic projection instead of perspective
        # The size determines how much of the world is visible
        size = 3.0  # Adjust this value to control zoom level
        
        if width <= height:
            # Width is smaller, use it to determine size
            glOrtho(-size, size, -size / aspect, size / aspect, -100.0, 100.0)
        else:
            # Height is smaller, use it to determine size
            glOrtho(-size * aspect, size * aspect, -size, size, -100.0, 100.0)
        
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        """Render the scene with orthographic projection"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # For orthographic projection, use scaling instead of z-translation for zoom
        scale_factor = self.zoom
        glScalef(scale_factor, scale_factor, scale_factor)
        
        # Apply rotations
        glRotatef(self.rotation_z, 0.0, 0.0, 1.0)  # Z-axis rotation (roll)
        glRotatef(self.rotation_x, 1.0, 0.0, 0.0)  # X-axis rotation (pitch)
        # glRotatef(self.rotation_y, 0.0, 1.0, 0.0)  # Y-axis rotation (yaw)
        
        # Draw coordinate axes first
        self._draw_axes()
        
        # If we have a model, center and scale it
        if self.obj_model.vertices:
            # Scale to fit view
            model_scale = 2.0 / self.model_size if self.model_size > 0 else 1.0
            glScalef(model_scale, model_scale, model_scale)
            
            # Center the model
            glTranslatef(-self.model_center[0], -self.model_center[1], -self.model_center[2])
            
            # Set material properties and render model as before
            glMaterialfv(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE, self.model_color)
            
            # Draw the model
            glBegin(GL_TRIANGLES)
            for face in self.obj_model.faces:
                for i in range(min(3, len(face))):  # Ensure we only use the first 3 vertices (triangulate)
                    vi, ni = face[i]
                    
                    # Apply normal if available
                    if ni >= 0 and ni < len(self.obj_model.normals):
                        glNormal3fv(self.obj_model.normals[ni])
                    
                    # Apply vertex
                    if vi >= 0 and vi < len(self.obj_model.vertices):
                        glVertex3fv(self.obj_model.vertices[vi])
                        
                # If face has more than 3 vertices, triangulate
                for i in range(3, len(face)):
                    # First vertex
                    vi, ni = face[0]
                    if ni >= 0:
                        glNormal3fv(self.obj_model.normals[ni])
                    glVertex3fv(self.obj_model.vertices[vi])
                    
                    # Previous vertex
                    vi, ni = face[i-1]
                    if ni >= 0:
                        glNormal3fv(self.obj_model.normals[ni])
                    glVertex3fv(self.obj_model.vertices[vi])
                    
                    # Current vertex
                    vi, ni = face[i]
                    if ni >= 0:
                        glNormal3fv(self.obj_model.normals[ni])
                    glVertex3fv(self.obj_model.vertices[vi])
            glEnd()
    
    def _draw_axes(self):
        """Draw the coordinate axes (X: blue, Y: green, Z: red)"""
        # Save current lighting state
        lighting_enabled = glIsEnabled(GL_LIGHTING)
        
        # Disable lighting for the axes
        glDisable(GL_LIGHTING)
        
        # Set line properties
        glLineWidth(1.5)  # Thin lines
        
        # Draw coordinate axes at origin
        axis_length = 1.0  # Length of each axis
        
        # X axis - Blue
        glBegin(GL_LINES)
        glColor3f(0.0, 0.0, 1.0)  # Blue
        glVertex3f(0.0, 0.0, 0.0)  # Origin
        glVertex3f(axis_length, 0.0, 0.0)  # X direction
        glEnd()
        
        # Y axis - Green
        glBegin(GL_LINES)
        glColor3f(0.0, 1.0, 0.0)  # Green
        glVertex3f(0.0, 0.0, 0.0)  # Origin
        glVertex3f(0.0, axis_length, 0.0)  # Y direction
        glEnd()
        
        # Z axis - Red
        glBegin(GL_LINES)
        glColor3f(1.0, 0.0, 0.0)  # Red
        glVertex3f(0.0, 0.0, 0.0)  # Origin
        glVertex3f(0.0, 0.0, axis_length)  # Z direction
        glEnd()
        
        # Add small labels at the end of each axis
        self._draw_axis_label("X", axis_length, 0.0, 0.0, (0.0, 0.0, 1.0))
        self._draw_axis_label("Y", 0.0, axis_length, 0.0, (0.0, 1.0, 0.0))
        self._draw_axis_label("Z", 0.0, 0.0, axis_length, (1.0, 0.0, 0.0))
        
        # Reset color to white
        glColor3f(1.0, 1.0, 1.0)
        
        # Restore lighting state
        if lighting_enabled:
            glEnable(GL_LIGHTING)

    def _draw_axis_label(self, text, x, y, z, color):
        """Draw a text label at the specified position (simplified)"""
        # Note: Text rendering in OpenGL requires more setup
        # This is a simplified placeholder - real text rendering would need
        # bitmap fonts or texture-based text
        
        # In a production app, you'd use a library like FTGL or render
        # text to textures and apply them as billboards
        
        # For now, we'll just leave this as a placeholder for future enhancement
        pass
    
    def mousePressEvent(self, event):
        """Handle mouse press events for rotation"""
        self.last_pos = event.position().toPoint()
    
    def mouseMoveEvent(self, event):
        """Handle mouse movement for model rotation"""
        pos = event.position().toPoint()
        if event.buttons() & Qt.MouseButton.LeftButton:
            dx = pos.x() - self.last_pos.x()
            dy = pos.y() - self.last_pos.y()
            
            self.rotation_y += dx * 0.5
            self.rotation_x += dy * 0.5
            
            self.update()
        
        self.last_pos = pos
    
    def wheelEvent(self, event):
        """Handle mouse wheel for orthographic zoom"""
        delta = event.angleDelta().y() / 120.0
        
        # For orthographic projection, we'll use a scaling factor
        # instead of translating along Z axis
        if delta > 0:
            # Zoom in: scale up by a factor
            self.zoom *= 1.1
        else:
            # Zoom out: scale down by a factor
            self.zoom /= 1.1
        
        # Ensure minimum and maximum zoom levels
        self.zoom = max(0.1, min(self.zoom, 10.0))
        
        self.update()

class MultiViewOBJViewer(QWidget):
    """Container widget that manages multiple OBJ viewers with different perspectives"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Create layout for the viewers
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(5)
        
        # Create the first viewer (30 degrees from positive Z axis in YZ plane)
        self.top_view_label = QLabel("View 1: +30° from +Z axis")
        self.top_view_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.top_viewer = OBJViewer(self)
        
        # Set initial rotation for first view:
        # We need to first rotate around Y to position in YZ plane (90 degrees)
        # Then around X to get 30 degrees from Z (60 degrees)
        self.top_viewer.rotation_y = 0.0  # Rotate to YZ plane
        self.top_viewer.rotation_x = 0.0  # 30 degrees from Z (90-30=60)
        self.top_viewer.rotation_z = 0.0  # Make X the "up" direction
        
        # Create the second viewer (30 degrees from negative Z axis in YZ plane)
        self.bottom_view_label = QLabel("View 2: +30° from -Z axis")
        self.bottom_view_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.bottom_viewer = OBJViewer(self)
        
        # Set initial rotation for second view:
        # Similar to above but from negative Z (210 degrees from positive Z)
        self.bottom_viewer.rotation_y = 90.0  # Rotate to YZ plane
        self.bottom_viewer.rotation_x = -60.0  # 30 degrees from -Z (-90+30=-60)
        self.bottom_viewer.rotation_z = 90.0  # Make X the "up" direction
        
        # Add viewers to layout
        top_view_container = QVBoxLayout()
        top_view_container.addWidget(self.top_view_label)
        top_view_container.addWidget(self.top_viewer)
        
        bottom_view_container = QVBoxLayout()
        bottom_view_container.addWidget(self.bottom_view_label)
        bottom_view_container.addWidget(self.bottom_viewer)
        
        self.layout.addLayout(top_view_container)
        self.layout.addLayout(bottom_view_container)
        
        # Keep track of loaded models
        self.current_model_file = None

    def load_obj(self, filename):
        """Load OBJ model in both viewers"""
        try:
            # Load the model in both viewers
            success1, message1 = self.top_viewer.load_obj(filename)
            success2, message2 = self.bottom_viewer.load_obj(filename)
            
            if success1 and success2:
                self.current_model_file = filename
                return True, f"Model loaded successfully in both views"
            elif success1:
                return False, f"Error loading in second view: {message2}"
            else:
                return False, f"Error loading model: {message1}"
        except Exception as e:
            import traceback
            return False, f"Exception loading model: {str(e)}\n{traceback.format_exc()}"