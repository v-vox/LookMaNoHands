import cv2
import numpy as np
from mpTrack import FaceDirectionTracker
import ctypes
import time

# Load user32.dll to call Windows API functions
user32 = ctypes.windll.user32

class FaceTrackerWithSmoothing:
    def __init__(self, smoothing_factor=0.1, x_sensitivity=1.0, y_sensitivity=2.0):
        self.smoothing_factor = smoothing_factor
        self.x_sensitivity = x_sensitivity
        self.y_sensitivity = y_sensitivity
        self.prev_x_angle = None
        self.prev_y_angle = None
        
        # Parameters for axis locking and movement threshold
        self.axis_lock_threshold = 3  # Ratio threshold for determining primary axis
        self.movement_threshold = 0.7    # Minimum angle change required for movement
        self.movement_threshold2 = 0.3    # Minimum angle change required for movement
        
        # New parameters for time-based movement detection
        self.low_movement_start_time = None
        self.low_movement_duration_threshold = 0.2 # Duration in seconds
        self.is_movement_locked = False
        self.is_movement_locked2 = False
    
    def smooth_angle(self, current_angle, prev_angle):
        """ Smooth the angle with a moving average. """
        if prev_angle is None:
            return current_angle
        return self.smoothing_factor * current_angle + (1 - self.smoothing_factor) * prev_angle

    def calibrate_sensitivity(self, x_factor, y_factor):
        """ Calibrate the sensitivity of the face movement. """
        self.x_sensitivity = x_factor
        self.y_sensitivity = y_factor

    def check_movement_threshold(self, x_change, y_change):
        """Check if movement is below threshold and manage time-based locking."""
        current_time = time.time()
        movement_magnitude = (x_change ** 2 + y_change ** 2) ** 0.5

        if movement_magnitude < self.movement_threshold:
            if self.low_movement_start_time is None:
                self.low_movement_start_time = current_time
            elif movement_magnitude < self.movement_threshold2:
                self.is_movement_locked2 = True
            elif current_time - self.low_movement_start_time >= self.low_movement_duration_threshold:
                self.is_movement_locked = True
        else:
            # Reset everything when movement is significant
            self.low_movement_start_time = None
            self.is_movement_locked = False  
            self.is_movement_locked2 = False  

        return self.is_movement_locked, self.is_movement_locked2

    def apply_axis_lock(self, x_change, y_change):
        """Apply axis locking when movement is primarily along one axis."""
        x_abs = abs(x_change)
        y_abs = abs(y_change)
        
        # Check if we should lock movement due to time-based threshold
        slow, lock = self.check_movement_threshold(x_change, y_change)
        if slow:
            self.smoothing_factor = 0.06
        else:
            self.smoothing_factor = 0.3

        # Calculate the ratio between x and y movement
        if x_abs > 0 and y_abs > 0:
            ratio = x_abs / y_abs
            
            # If movement is primarily horizontal
            if ratio > self.axis_lock_threshold:
                return x_change, 0
            # If movement is primarily vertical
            elif ratio < 1/self.axis_lock_threshold:
                return 0, y_change
                
        return x_change, y_change

    def map_angle_to_screen(self, angle, axis='x'):
        """ Map angle to screen coordinate (x or y). """
        screen_width, screen_height = 1920, 1080  # Use your screen resolution here

        # Define the range for the angles (assuming -30° to 30° for both axes)
        min_angle = -30
        max_angle = 30
        
        # Mapping angle to a normalized screen position
        if axis == 'x':
            # Invert the x-axis mapping (flip left-right) to correct inversion
            screen_position = (angle - min_angle) / (max_angle - min_angle) * screen_width
            screen_position = screen_width - screen_position  # Invert horizontal direction
        elif axis == 'y':
            # Invert the y-axis mapping (flip up-down) to correct inversion
            screen_position = (angle + 20) / (40) * screen_height
        
        # Apply sensitivity adjustment
        if axis == 'x':
            screen_position *= self.x_sensitivity
        elif axis == 'y':
            screen_position *= self.y_sensitivity

        return int(screen_position)

    def update_angles(self, x_angle, y_angle):
        """ Update the angles with smoothing, axis locking, and movement threshold applied. """
        smoothed_x = self.smooth_angle(x_angle, self.prev_x_angle)
        smoothed_y = self.smooth_angle(y_angle, self.prev_y_angle)

        # Calculate angle changes
        x_change = smoothed_x - (self.prev_x_angle or smoothed_x)
        y_change = smoothed_y - (self.prev_y_angle or smoothed_y)
        
        # Apply axis locking and movement threshold
        locked_x_change, locked_y_change = self.apply_axis_lock(x_change, y_change)
        
        # Update final angles
        final_x = (self.prev_x_angle or smoothed_x) + locked_x_change
        final_y = (self.prev_y_angle or smoothed_y) + locked_y_change
        
        self.prev_x_angle = final_x
        self.prev_y_angle = final_y

        return final_x, final_y

def move_mouse(x, y):
    """Move the mouse to the specified coordinates using the Windows API."""
    user32.SetCursorPos(x, y)
     

def main():
    # Initialize tracker with visualization
    tracker = FaceDirectionTracker(show_visualization=False)  # Turn off visualization for better performance
    
    # Instantiate
    tracker_with_smoothing = FaceTrackerWithSmoothing(
        smoothing_factor=0.3,
        x_sensitivity=1.4,
        y_sensitivity=3
    )
    
    tracker_with_smoothing.calibrate_sensitivity(x_factor=1.5, y_factor=2)

    try:
        tracker.start_camera(0) 
        
        # Main loop
        while True:
            angles = tracker.get_frame()
            

            if angles is not None:
                x_angle, y_angle, blinked = angles
                
                # Update angles with smoothing, axis locking, and movement threshold
                final_x, final_y = tracker_with_smoothing.update_angles(x_angle, y_angle)
                
                # Map smoothed angles to screen coordinates
                screen_x = tracker_with_smoothing.map_angle_to_screen(final_x, axis='x')
                screen_y = tracker_with_smoothing.map_angle_to_screen(final_y, axis='y')
                
                # Move the mouse cursor to the calculated position using the Windows API
                move_mouse(screen_x, screen_y)

                if blinked:
                    user32.mouse_event(2, 0, 0, 0, 0)  # Left button down
                    user32.mouse_event(4, 0, 0, 0, 0)  # Left button up
            
            # Optional: Check for 'q' key to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
    except KeyboardInterrupt:
        print("\nStopping tracker...")
    finally:
        # Clean up
        tracker.stop_camera()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()