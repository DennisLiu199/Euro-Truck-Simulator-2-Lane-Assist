import cv2
from plugins.Map.GameData import nodes, roads, prefabs, prefabItems
import math
import numpy as np
import os
import json
import time
from src.logger import print

LIMIT_OF_PARALLEL_LANE_CALCS_PER_FRAME = 10

def VisualizeRoads(data, img=None, zoom=2):
    """Will draw the roads onto the image.
    data: The game data
    img: The image to draw the roads on
    """
    # Get the current X and Y position of the truck
    x = data["api"]["truckPlacement"]["coordinateX"]
    y = data["api"]["truckPlacement"]["coordinateZ"]
    
    
    startTime = time.time()
    
    # Get the roads in the current area
    areaRoads = []
    areaRoads = roads.GetRoadsInTileByCoordinates(x, y)
    tileCoords = roads.GetTileCoordinates(x, y)
    
    # Also get the roads in the surrounding tiles
    areaRoads += roads.GetRoadsInTileByCoordinates(x + 1000, y)
    areaRoads += roads.GetRoadsInTileByCoordinates(x - 1000, y)
    areaRoads += roads.GetRoadsInTileByCoordinates(x, y + 1000)
    areaRoads += roads.GetRoadsInTileByCoordinates(x, y - 1000)
    areaRoads += roads.GetRoadsInTileByCoordinates(x + 1000, y + 1000)
    areaRoads += roads.GetRoadsInTileByCoordinates(x + 1000, y - 1000)
    areaRoads += roads.GetRoadsInTileByCoordinates(x - 1000, y + 1000)
    areaRoads += roads.GetRoadsInTileByCoordinates(x - 1000, y - 1000)
    
    # Make a blank image of size 1000x1000 (1km x 1km on default zoom of 1)
    if img is None:
        size = 1000
        img = np.zeros((size, size, 3), np.uint8)
    
    # Show the x and y coordinates
    cv2.putText(img, f"X: {x} Y: {y}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # Draw the original x and y coordinates on the imag
    cv2.circle(img, (500, 500), 5, (0, 255, 0), -1, cv2.LINE_AA)

    # Draw the roads on the image, 1m is 1px in the image
    # roads have their start and end positions in the global coordinate system so we need to convert them to local coordinates with roads.GetLocalCoordinateInTile()
    calcCount = 0
    skipped = 0
    for road in areaRoads:
        try:
            if road.Points == None:
                points = roads.CreatePointsForRoad(road)
                roads.SetRoadPoints(road, points)
            
            # newPoints = []
            # for point in road.Points:
            #     xy = roads.GetLocalCoordinateInTile(point[0], point[1], tileCoords[0], tileCoords[1])
            #     truckXY = roads.GetLocalCoordinateInTile(x, y, tileCoords[0], tileCoords[1])
            #     xy = (xy[0] - truckXY[0], xy[1] - truckXY[1])
            #     # Apply zoom to the local coordinates
            #     zoomedX = xy[0] * zoom
            #     zoomedY = xy[1] * zoom
            #     # Offset the zoomed coordinates by the truck's position to "move" the camera
            #     pointX = int(zoomedX + size//2)
            #     pointY = int(zoomedY + size//2)
            #     newPoints.append((pointX, pointY))
            # 
            # cv2.polylines(img, np.int32([newPoints]), False, (0, 100, 150), (1 + (zoom - 1)), cv2.LINE_AA)
            
            # Check for parallel points
            if road.ParallelPoints == []:
                if calcCount > LIMIT_OF_PARALLEL_LANE_CALCS_PER_FRAME:
                    skipped += 1
                    continue
                
                boundingBox, parallelPoints, laneWidth = roads.CalculateParallelCurves(road)
                if parallelPoints == [] or parallelPoints == None:
                    parallelPoints = [[(0, 0), (0, 0)], [(0, 0), (0, 0)]]
                road.ParallelPoints = parallelPoints
                road.LaneWidth = laneWidth
                road.BoundingBox = boundingBox
                roads.SetRoadParallelData(road, parallelPoints, laneWidth, boundingBox)
                calcCount += 1
            
            if road.ParallelPoints == [[(0, 0), (0, 0)], [(0, 0), (0, 0)]]:
                continue
            
            for lane in road.ParallelPoints:
                newPoints = []
                for point in lane:
                    xy = roads.GetLocalCoordinateInTile(point[0], point[1], tileCoords[0], tileCoords[1])
                    truckXY = roads.GetLocalCoordinateInTile(x, y, tileCoords[0], tileCoords[1])
                    xy = (xy[0] - truckXY[0], xy[1] - truckXY[1])
                    # Apply zoom to the local coordinates
                    zoomedX = xy[0] * zoom
                    zoomedY = xy[1] * zoom
                    # Offset the zoomed coordinates by the truck's position to "move" the camera
                    pointX = int(zoomedX + size//2)
                    pointY = int(zoomedY + size//2)
                    # Check if the points are within the display area (1000px x 1000px)
                    if pointX < 0 or pointX > 1000 or pointY < 0 or pointY > 1000:
                        continue
                    newPoints.append((pointX, pointY))
            
                cv2.polylines(img, np.int32([newPoints]), False, (150, 150, 150), (2 + (zoom - 1)), cv2.LINE_AA)
            
            road = None
        
        except:
            #import traceback
            #traceback.print_exc()
            pass
        
    cv2.putText(img, f"Roads: {len(areaRoads)}, Tile: {str(tileCoords)}, Loading: {str(int(skipped))}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

    # Return the image    
    return img


def VisualizePrefabs(data, img=None, zoom=2):
    """Will draw the prefabs onto the image.

    Args:
        data (dict): data dictionary.
        img (np.array, optional): Image array. Defaults to None.
        zoom (float, optional): How many pixels is one meter in the data. Defaults to 2.

    Returns:
        np.array: image array
    """
    # Get the current X and Y position of the truck
    x = data["api"]["truckPlacement"]["coordinateX"]
    y = data["api"]["truckPlacement"]["coordinateZ"]
    
    # Get the roads in the current area
    areaItems = []
    areaItems += prefabItems.GetItemsInTileByCoordinates(x, y)
    tileCoords = roads.GetTileCoordinates(x, y)
    prefabTileCoords = prefabItems.GetTileCoordinates(x, y)
    
    # Also get the roads in the surrounding tiles
    areaItems += prefabItems.GetItemsInTileByCoordinates(x + 1000, y)
    areaItems += prefabItems.GetItemsInTileByCoordinates(x - 1000, y)
    areaItems += prefabItems.GetItemsInTileByCoordinates(x, y + 1000)
    areaItems += prefabItems.GetItemsInTileByCoordinates(x, y - 1000)
    areaItems += prefabItems.GetItemsInTileByCoordinates(x + 1000, y + 1000)
    areaItems += prefabItems.GetItemsInTileByCoordinates(x + 1000, y - 1000)
    areaItems += prefabItems.GetItemsInTileByCoordinates(x - 1000, y + 1000)
    areaItems += prefabItems.GetItemsInTileByCoordinates(x - 1000, y - 1000)
    
    # Make a blank image of size 1000x1000 (1km x 1km on default zoom)
    if img is None:
        size = 1000
        img = np.zeros((size, size, 3), np.uint8)
    else:
        size = img.shape[0]
    
    curveCount = 0
    for item in areaItems:
        try:
            truckXY = roads.GetLocalCoordinateInTile(x, y, tileCoords[0], tileCoords[1])
            if item.Prefab.ValidRoad:
                # Draw the curves
                for curve in item.NavigationLanes:
                    curveCount += 1
                    startXY = roads.GetLocalCoordinateInTile(curve[0], curve[1] , tileCoords[0], tileCoords[1])
                    endXY = roads.GetLocalCoordinateInTile(curve[2], curve[3], tileCoords[0], tileCoords[1])
                    startXY = (startXY[0] - truckXY[0], startXY[1] - truckXY[1])
                    endXY = (endXY[0] - truckXY[0], endXY[1] - truckXY[1])
                    # Apply zoom to the local coordinates
                    zoomedStartX = startXY[0] * zoom
                    zoomedStartY = startXY[1] * zoom
                    zoomedEndX = endXY[0] * zoom
                    zoomedEndY = endXY[1] * zoom
                    # Offset the zoomed coordinates by the truck's position to "move" the camera
                    startX = int(zoomedStartX + size//2)
                    startY = int(zoomedStartY + size//2)
                    endX = int(zoomedEndX + size//2)
                    endY = int(zoomedEndY + size//2)
                    cv2.line(img, (startX, startY), (endX, endY), (100, 100, 100), 1 + (zoom - 1))
        except: 
            pass

    cv2.putText(img, f"Prefabs: {len(areaItems)}, Tile: {str(prefabTileCoords)}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(img, f"Curves: {curveCount}", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return img