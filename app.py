import sys
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QOpenGLWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QVector3D, QMatrix4x4, QFont
from OpenGL.GL import *
from OpenGL.GLU import *

class Environment:
    def __init__(self):
        # Room dimensions
        self.room_width = 10
        self.room_height = 6
        self.room_depth = 10

        # Wall configurations (simplified maze)
        self.walls = [
            # Outer walls
            [-self.room_width/2, 0, -self.room_depth/2, 
             self.room_width/2, 0, -self.room_depth/2, 
             0.5, 0.5, 0.5, 1],  # Front wall
            [-self.room_width/2, 0, self.room_depth/2, 
             self.room_width/2, 0, self.room_depth/2, 
             0.5, 0.5, 0.5, 1],  # Back wall
            [-self.room_width/2, 0, -self.room_depth/2, 
             -self.room_width/2, 0, self.room_depth/2, 
             0.5, 0.5, 0.5, 1],  # Left wall
            [self.room_width/2, 0, -self.room_depth/2, 
             self.room_width/2, 0, self.room_depth/2, 
             0.5, 0.5, 0.5, 1],  # Right wall
            
            # Maze walls (thin walls)
            [-2, 0, -2, 
             -2, 0, 2, 
             1.0, 0.2, 0.2, 1],  # Vertical wall 1
            [2, 0, -2, 
             2, 0, 2, 
             1.0, 0.2, 0.2, 1],  # Vertical wall 2
            [-2, 0, -2, 
             2, 0, -2, 
             0.2, 1.0, 0.2, 1],  # Horizontal wall 1
            [-2, 0, 2, 
             2, 0, 2, 
             0.2, 1.0, 0.2, 1],  # Horizontal wall 2
        ]

        # No obstacles
        self.obstacles = []

class OpenGLWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Environment setup
        self.environment = Environment()
        
        # Camera parameters
        self.camera_pos = QVector3D(0.0, 0.0, 0.0)
        self.camera_front = QVector3D(0.0, 0.0, -1.0)
        self.camera_up = QVector3D(0.0, 1.0, 0.0)
        
        # Rotation parameters
        self.yaw = -90.0  # Initial yaw angle
        self.pitch = 0.0  # Initial pitch angle
        
        # Movement parameters
        self.camera_speed = 0.1  # Linear movement speed
        self.rotation_speed = 2.0
        self.mouse_sensitivity = 0.1
        
        # Key state tracking
        self.keys_pressed = set()
        
        # Movement timer
        self.move_timer = QTimer(self)
        self.move_timer.timeout.connect(self.update_movement)
        self.move_timer.start(16)  # ~60 FPS
        
        # Mouse tracking
        self.last_x = self.width() / 2
        self.last_y = self.height() / 2
        self.first_mouse = True
        
        # Collision detection
        self.collision_radius = 0.5
        
        # Coordinate label
        self.coord_label = QLabel(self)
        self.coord_label.setStyleSheet("color: white; font-size: 12px; background-color: rgba(0,0,0,100);")
        self.coord_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        
        # Set focus policy to receive keyboard events
        self.setFocusPolicy(Qt.StrongFocus)

    def initializeGL(self):
        # Enable OpenGL features
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_NORMALIZE)
        
        # Set up lighting
        light_position = [5.0, 5.0, 5.0, 1.0]
        light_ambient = [0.2, 0.2, 0.2, 1.0]
        light_diffuse = [0.8, 0.8, 0.8, 1.0]
        light_specular = [1.0, 1.0, 1.0, 1.0]
        
        glLightfv(GL_LIGHT0, GL_POSITION, light_position)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)

    def resizeGL(self, width, height):
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45.0, width / height, 0.1, 100.0)

    def check_collision(self, new_pos):
        # Simplified collision check (always return True)
        return True

    def update_movement(self):
        # Create a horizontal front vector (ignore vertical component)
        horizontal_front = QVector3D(self.camera_front.x(), 0.0, self.camera_front.z()).normalized()
        
        # Calculate right vector based on horizontal front
        right = QVector3D.crossProduct(horizontal_front, self.camera_up).normalized()
        
        # Linear movement based on pressed keys
        movement = QVector3D(0.0, 0.0, 0.0)
        if Qt.Key_W in self.keys_pressed:
            movement += horizontal_front * self.camera_speed
        if Qt.Key_S in self.keys_pressed:
            movement -= horizontal_front * self.camera_speed
        if Qt.Key_A in self.keys_pressed:
            movement -= right * self.camera_speed
        if Qt.Key_D in self.keys_pressed:
            movement += right * self.camera_speed
        
        # Vertical movement ONLY by Q and E
        if Qt.Key_Q in self.keys_pressed:
            movement += self.camera_up * self.camera_speed
        if Qt.Key_E in self.keys_pressed:
            movement -= self.camera_up * self.camera_speed
        
        # Apply linear movement
        new_pos = self.camera_pos + movement
        
        # Remove collision check
        self.camera_pos = new_pos
        
        self.update()

    def paintGL(self):
        # Clear buffers with solid blue and dark green background
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Draw background with solid colors
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(-1, 1, -1, 1, -1, 1)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_DEPTH_TEST)
        glBegin(GL_QUADS)
        # Top half solid blue
        glColor3f(0.0, 0.0, 1.0)
        glVertex2f(-1, 0)
        glVertex2f(1, 0)
        glVertex2f(1, 1)
        glVertex2f(-1, 1)
        
        # Bottom half solid dark green
        glColor3f(0.0, 0.4, 0.0)
        glVertex2f(-1, -1)
        glVertex2f(1, -1)
        glVertex2f(1, 0)
        glVertex2f(-1, 0)
        glEnd()
        
        glEnable(GL_DEPTH_TEST)
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

        # Reset modelview matrix
        glLoadIdentity()
        
        # Set up camera
        gluLookAt(
            self.camera_pos.x(), self.camera_pos.y(), self.camera_pos.z(),
            self.camera_pos.x() + self.camera_front.x(), 
            self.camera_pos.y() + self.camera_front.y(), 
            self.camera_pos.z() + self.camera_front.z(),
            self.camera_up.x(), self.camera_up.y(), self.camera_up.z()
        )

        # Render walls
        for wall in self.environment.walls:
            glColor3f(wall[6], wall[7], wall[8])
            glBegin(GL_QUADS)
            glVertex3f(wall[0], wall[1], wall[2])
            glVertex3f(wall[3], wall[1], wall[2])
            glVertex3f(wall[3], wall[4], wall[5])
            glVertex3f(wall[0], wall[4], wall[5])
            glEnd()

        # Render coordinate axes
        glLineWidth(2.0)
        glBegin(GL_LINES)
        # X-axis (Red)
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(1, 0, 0)
        
        # Y-axis (Green)
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 1, 0)
        
        # Z-axis (Blue)
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 1)
        glEnd()

        # Render coordinate display
        coord_text = (f"Pos: ({self.camera_pos.x():.2f}, {self.camera_pos.y():.2f}, {self.camera_pos.z():.2f})\n"
                      f"Yaw: {self.yaw:.2f}°\n"
                      f"Pitch: {self.pitch:.2f}°")
        self.coord_label.setText(coord_text)
        self.coord_label.move(10, 10)
        self.coord_label.adjustSize()

    def keyPressEvent(self, event):
        # Add key to pressed keys
        self.keys_pressed.add(event.key())
        
        # Custom ESC key handling for exit
        if event.key() == Qt.Key_Escape:
            print("Exiting with custom error code")
            sys.exit(42)  # Custom exit code
        
        # Smooth camera rotation with arrow keys
        if event.key() == Qt.Key_Left:
            self.yaw -= self.rotation_speed
            self.update_camera_front()
        elif event.key() == Qt.Key_Right:
            self.yaw += self.rotation_speed
            self.update_camera_front()
        elif event.key() == Qt.Key_Up:
            self.pitch += self.rotation_speed
            self.update_camera_front()
        elif event.key() == Qt.Key_Down:
            self.pitch -= self.rotation_speed
            self.update_camera_front()

    def keyReleaseEvent(self, event):
        # Remove key from pressed keys
        if event.key() in self.keys_pressed:
            self.keys_pressed.remove(event.key())

    def update_camera_front(self):
        # Constrain pitch
        if self.pitch > 89.0:
            self.pitch = 89.0
        if self.pitch < -89.0:
            self.pitch = -89.0
        
        # Calculate new front vector
        front = QVector3D()
        front.setX(np.cos(np.radians(self.yaw)) * np.cos(np.radians(self.pitch)))
        front.setY(np.sin(np.radians(self.pitch)))
        front.setZ(np.sin(np.radians(self.yaw)) * np.cos(np.radians(self.pitch)))
        
        self.camera_front = front.normalized()
        self.update()

    def mousePressEvent(self, event):
        self.last_x = event.x()
        self.last_y = event.y()
        self.first_mouse = False

    def mouseMoveEvent(self, event):
        if self.first_mouse:
            self.last_x = event.x()
            self.last_y = event.y()
            self.first_mouse = False
        
        x_offset = event.x() - self.last_x
        y_offset = self.last_y - event.y()  # Reversed since y-coordinates go from bottom to top
        
        self.last_x = event.x()
        self.last_y = event.y()
        
        x_offset *= self.mouse_sensitivity
        y_offset *= self.mouse_sensitivity
        
        self.yaw += x_offset
        self.pitch += y_offset
        
        # Constrain pitch
        if self.pitch > 89.0:
            self.pitch = 89.0
        if self.pitch < -89.0:
            self.pitch = -89.0
        
        self.update_camera_front()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('3D Environment')
        self.resize(800, 600)
        
        # Create OpenGL widget
        self.opengl_widget = OpenGLWidget(self)
        self.setCentralWidget(self.opengl_widget)
        
        # Ensure coordinate label is visible
        self.opengl_widget.coord_label.setParent(self)

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    exit_code = app.exec_()
    
    # Check for custom exit code
    if exit_code == 42:
        print("Application exited with custom ESC key exit code")
        sys.exit(42)
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
