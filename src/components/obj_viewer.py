import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QSurfaceFormat
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
        self.zoom = -5.0
        self.last_pos = QPoint()
        
        # Colors for the model
        self.model_color = (0.7, 0.7, 0.9, 1.0)  # Light blue
        self.background_color = (0.2, 0.2, 0.2, 1.0)  # Dark gray
        
        # Allow mouse tracking for interactivity
        self.setMouseTracking(True)
    
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
        """Handle widget resize events"""
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = width / height if height > 0 else 1.0
        gluPerspective(45, aspect, 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)
    
    def paintGL(self):
        """Render the scene"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Position camera
        glTranslatef(0.0, 0.0, self.zoom)
        glRotatef(self.rotation_x, 1.0, 0.0, 0.0)
        glRotatef(self.rotation_y, 0.0, 1.0, 0.0)
        
        # If we have a model, center and scale it
        if self.obj_model.vertices:
            # Scale to fit view
            scale_factor = 2.0 / self.model_size if self.model_size > 0 else 1.0
            glScalef(scale_factor, scale_factor, scale_factor)
            
            # Center the model
            glTranslatef(-self.model_center[0], -self.model_center[1], -self.model_center[2])
            
            # Set material properties
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
        """Handle mouse wheel for zooming"""
        delta = event.angleDelta().y() / 120.0
        self.zoom += delta * 0.5
        self.update()