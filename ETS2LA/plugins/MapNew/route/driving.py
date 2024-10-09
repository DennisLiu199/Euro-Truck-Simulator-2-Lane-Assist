# TODO: Fix this file, it's still using the old steering system!
import ETS2LA.plugins.MapNew.classes as c
import utils.math_helpers as math_helpers
import route.classes as rc
import numpy as np
import logging
import data
import math

OFFSET_MULTIPLIER = 1.5
ANGLE_MULTIPLIER = 1

was_indicating = False
def CheckForLaneChange():
    global was_indicating
    if type(data.route_plan[0].items[0].item) == c.Prefab:
        was_indicating = False
        return
    
    current_index = data.route_plan[0].lane_index
    lanes = data.route_plan[0].items[0].item.lanes
    side = lanes[current_index].side
    
    if data.truck_indicating_right and not was_indicating:
        was_indicating = True
        current_index = data.route_plan[0].lane_index
        start_node = data.route_plan[0].start_node
        if math_helpers.IsInFront((data.truck_x, data.truck_z), data.truck_rotation, (start_node.x, start_node.z)):
            if side == "left":
                if current_index > 0:
                    data.route_plan[0].lane_index -= 1
            else:
                if current_index < len(lanes) - 1:
                    data.route_plan[0].lane_index += 1
        else:
            if side == "left":    
                if current_index < len(lanes) - 1:
                    data.route_plan[0].lane_index += 1
            else:
                if current_index > 0:
                    data.route_plan[0].lane_index -= 1
                
    elif data.truck_indicating_left and not was_indicating:
        was_indicating = True
        current_index = data.route_plan[0].lane_index
        start_node = data.route_plan[0].start_node
        if math_helpers.IsInFront((data.truck_x, data.truck_z), data.truck_rotation, (start_node.x, start_node.z)):
            if side == "left":
                if current_index < len(lanes) - 1:
                    data.route_plan[0].lane_index += 1
            else:
                if current_index > 0:
                    data.route_plan[0].lane_index -= 1
        else:
            if side == "left":
                if current_index > 0:
                    data.route_plan[0].lane_index -= 1
            else:
                if current_index < len(lanes) - 1:
                    data.route_plan[0].lane_index += 1
                
    elif not data.truck_indicating_left and not data.truck_indicating_right:
        was_indicating = False  
        

def GetSteering():
    if len(data.route_plan) == 0:
        return 0
    
    CheckForLaneChange()
    
    points = []
    for section in data.route_plan:
        if len(points) > 5:
            break
        
        if section is None:
            continue
        
        for point in section.get_points():
            if len(points) > 5:
                break
            points.append(point)
            
    forward_vector = [-math.sin(data.truck_rotation), -math.cos(data.truck_rotation)]
    try:
        if len(points) > 2:
            points = points[:5]

            x = 0
            z = 0
            for i in range(1, len(points)):
                x += points[i].x
                z += points[i].z
            x /= 4
            z /= 4
            
            point_forward_vector = [points[len(points)-1].x - points[0].x, points[len(points)-1].z - points[0].z]
            
            if np.cross(forward_vector, point_forward_vector) < 0:
                isLeft = True
            else: isLeft = False
            
            centerline = [points[-1].x - points[0].x, points[-1].z - points[0].z]
            truck_position_vector = [data.truck_x - points[0].x, data.truck_z - points[0].z]
            
            lateral_offset = np.cross(truck_position_vector, centerline) / np.linalg.norm(centerline)
            
            angle = np.arccos(np.dot(forward_vector, centerline) / (np.linalg.norm(forward_vector) * np.linalg.norm(centerline)))
            angle = math.degrees(angle)
            
            if np.cross(forward_vector, centerline) < 0:
                angle = -angle
            
            if angle > 140:
                angle = 0
            if angle < -140:
                angle = 0
            
            angle = angle * ANGLE_MULTIPLIER
            
            offset_correction = lateral_offset * 5
            offset_correction = max(-20, min(20, offset_correction))
            if isLeft:
                angle += offset_correction * OFFSET_MULTIPLIER
            else:
                angle += offset_correction * OFFSET_MULTIPLIER
            
            multiplier = 2
            
            return angle * multiplier
        else:
            x = points[len(points)-1].x
            z = points[len(points)-1].z
            
            vector = [x - data.truck_x, z - data.truck_z]

            angle = np.arccos(np.dot(forward_vector, vector) / (np.linalg.norm(forward_vector) * np.linalg.norm(vector)))
            angle = math.degrees(angle)

            if np.cross(forward_vector, vector) < 0:
                angle = -angle
                
            return angle * 2
    except:
        logging.exception("Error in GetSteering")
        return 0