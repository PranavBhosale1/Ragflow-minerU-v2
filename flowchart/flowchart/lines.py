import cv2
import numpy as np
import networkx as nx
from typing import List, Dict, Tuple
from skimage.morphology import skeletonize

def build_skeleton_graph(skeleton: np.ndarray) -> nx.Graph:
    """
    Convert a skeletonized binary image into a NetworkX Graph.
    Nodes are pixels (x, y). Edges exist between 8-connected neighbors.
    """
    # np.where returns (row, col) -> (y, x)
    rows, cols = np.where(skeleton > 0)
    G = nx.Graph()
    
    # Add nodes using (x, y) coordinates
    for r, c in zip(rows, cols):
        G.add_node((c, r))

    # Efficiently add edges using a set for O(1) lookups
    node_set = set(G.nodes())
    
    for (x, y) in node_set:
        # Check 4 neighbors (right, down-right, down, down-left) to avoid double counting
        neighbors = [
            (x + 1, y), (x + 1, y + 1), 
            (x, y + 1), (x - 1, y + 1)
        ]
        for n in neighbors:
            if n in node_set:
                G.add_edge((x, y), n, weight=1)
                
    return G

def simplify_graph_topology(G: nx.Graph) -> nx.Graph:
    """
    Contracts chains of degree-2 nodes into single edges.
    Preserves Endpoints (degree 1) and Junctions (degree > 2).
    """
    simple_G = G.copy()
    
    while True:
        nodes_to_remove = [n for n, d in simple_G.degree() if d == 2]
        if not nodes_to_remove:
            break
            
        did_simplify = False
        for node in nodes_to_remove:
            if node not in simple_G: continue
            
            neighbors = list(simple_G.neighbors(node))
            if len(neighbors) == 2:
                u, v = neighbors
                w1 = simple_G[u][node].get('weight', 1)
                w2 = simple_G[node][v].get('weight', 1)
                
                simple_G.remove_node(node)
                
                if simple_G.has_edge(u, v):
                    current_w = simple_G[u][v].get('weight', 1)
                    simple_G.add_edge(u, v, weight=min(current_w, w1 + w2))
                else:
                    simple_G.add_edge(u, v, weight=w1 + w2)
                
                did_simplify = True
        
        if not did_simplify:
            break
            
    return simple_G

def get_node_interface_points(nodes: List[Dict], proximity: int) -> List[Dict]:
    """
    Adds a 'search_area' to nodes for hit-testing.
    """
    for node in nodes:
        x, y, w, h = node['bbox']
        # Define a rim around the box
        x1, y1 = max(0, x - proximity), max(0, y - proximity)
        x2, y2 = x + w + proximity, y + h + proximity
        node['search_area'] = (x1, y1, x2, y2)
    return nodes

def map_graph_nodes_to_boxes(G: nx.Graph, nodes: List[Dict]) -> Dict[Tuple[int, int], int]:
    """
    Maps coordinates in the simplified graph to Flowchart Node Indices.
    """
    mapping = {}
    for pt in G.nodes():
        px, py = pt
        for i, node in enumerate(nodes):
            x1, y1, x2, y2 = node['search_area']
            if x1 <= px <= x2 and y1 <= py <= y2:
                mapping[pt] = i
                break
    return mapping

def check_local_arrowhead(
    binary_img: np.ndarray, 
    point: Tuple[int, int], 
    window_size: int = 15,
    density_thresh: float = 0.25
) -> bool:
    """
    Analyze the local neighborhood of a point on the binary image.
    If the endpoint terminates in a dense blob (arrowhead), it will have
    higher pixel density than a simple thin line.
    
    Args:
        binary_img: The original binary image (0=background, 255=foreground)
        point: (x, y) center to check
        window_size: Size of crop
        density_thresh: Ratio of white pixels to trigger 'arrow' detection
    """
    x, y = point
    h, w = binary_img.shape
    
    x1 = max(0, x - window_size)
    y1 = max(0, y - window_size)
    x2 = min(w, x + window_size)
    y2 = min(h, y + window_size)
    
    crop = binary_img[y1:y2, x1:x2]
    
    if crop.size == 0:
        return False
        
    # Count non-zero pixels
    non_zero = cv2.countNonZero(crop)
    area = crop.size
    density = non_zero / float(area)
    
    # A single line (thickness 2-3px) in a 30x30 window has low density (~0.1).
    # A solid triangular arrowhead has much higher density.
    return density > density_thresh

def detect_edges_and_arrows(
    binary: np.ndarray,
    nodes: List[Dict],
    min_line_area: int = 50, # Unused in skeleton approach but kept for signature
    min_arrow_area: int = 20,
    max_arrow_area: int = 600,
    proximity_thresh: int = 20,
    debug_path: str = None
) -> List[Dict]:
    """
    Topology-aware edge detection with local geometry analysis for direction.
    """
    
    # 1. Close gaps slightly before skeletonization
    kernel = np.ones((3, 3), np.uint8)
    processed_binary = cv2.dilate(binary, kernel, iterations=2)
    
    # 2. Skeletonize
    skel = skeletonize(processed_binary > 0)
    G_skel = build_skeleton_graph(skel)
    
    # 3. Simplify Graph (Merge linear paths)
    G_simple = simplify_graph_topology(G_skel)
    
    # 4. Map Graph Nodes to Flowchart Boxes
    nodes_with_search = get_node_interface_points(nodes, proximity_thresh)
    coord_to_node_index = map_graph_nodes_to_boxes(G_simple, nodes_with_search)
    
    interface_vertices = list(coord_to_node_index.keys())
    detected_edges = []
    processed_pairs = set()

    # 5. Path Traversal
    for start_node in interface_vertices:
        src_box_idx = coord_to_node_index[start_node]
        
        # BFS/DFS to find other interface nodes connected to this one
        visited = {start_node}
        stack = [start_node]
        
        while stack:
            curr = stack.pop()
            
            for neighbor in G_simple.neighbors(curr):
                if neighbor in visited:
                    continue
                
                # Check if this neighbor touches a box
                if neighbor in coord_to_node_index:
                    dst_box_idx = coord_to_node_index[neighbor]
                    
                    # Avoid self-loops and duplicate processing of the same edge
                    pair_id = tuple(sorted((start_node, neighbor)))
                    
                    if src_box_idx != dst_box_idx and pair_id not in processed_pairs:
                        processed_pairs.add(pair_id)
                        
                        # DIRECTION LOGIC:
                        # We check the "density" of the original binary image at both endpoints.
                        # The endpoint with the Arrowhead will have higher pixel mass.
                        
                        is_arrow_at_dst = check_local_arrowhead(binary, neighbor)
                        is_arrow_at_src = check_local_arrowhead(binary, start_node)
                        
                        if is_arrow_at_dst and not is_arrow_at_src:
                            # Standard case: Line starts at SRC, Arrow at DST
                            detected_edges.append({'src': src_box_idx, 'dst': dst_box_idx})
                        elif is_arrow_at_src and not is_arrow_at_dst:
                            # Reverse case: Arrow at SRC
                            detected_edges.append({'src': dst_box_idx, 'dst': src_box_idx})
                        else:
                            # Ambiguous (Double arrow or simple line). 
                            # Fallback: Assume Top-to-Bottom or Left-to-Right flow based on centroids
                            # This handles plain lines without arrows reasonably well.
                            src_bbox = nodes[src_box_idx]['bbox']
                            dst_bbox = nodes[dst_box_idx]['bbox']
                            src_center = (src_bbox[0] + src_bbox[2]/2, src_bbox[1] + src_bbox[3]/2)
                            dst_center = (dst_bbox[0] + dst_bbox[2]/2, dst_bbox[1] + dst_bbox[3]/2)
                            
                            # If primarily vertical
                            if abs(src_center[1] - dst_center[1]) > abs(src_center[0] - dst_center[0]):
                                if src_center[1] < dst_center[1]:
                                    detected_edges.append({'src': src_box_idx, 'dst': dst_box_idx})
                                else:
                                    detected_edges.append({'src': dst_box_idx, 'dst': src_box_idx})
                            else:
                                # Primarily horizontal
                                if src_center[0] < dst_center[0]:
                                    detected_edges.append({'src': src_box_idx, 'dst': dst_box_idx})
                                else:
                                    detected_edges.append({'src': dst_box_idx, 'dst': src_box_idx})

                    # Stop this branch, we found a destination
                    visited.add(neighbor)
                else:
                    visited.add(neighbor)
                    stack.append(neighbor)

    if debug_path:
        debug_img = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
        
        # Draw Graph Nodes
        for (x, y) in G_simple.nodes():
            color = [0, 255, 0] # Green
            if (x, y) in coord_to_node_index:
                color = [0, 0, 255] # Red if touching a box
                # Visualize arrow detection
                if check_local_arrowhead(binary, (x,y)):
                    cv2.circle(debug_img, (x, y), 8, (255, 0, 255), 2) # Magenta ring = Arrow detected
            cv2.circle(debug_img, (x, y), 3, color, -1)
            
        # Draw Graph Edges
        for u, v in G_simple.edges():
            cv2.line(debug_img, u, v, (255, 255, 0), 1)
            
        cv2.imwrite(debug_path, debug_img)

    return detected_edges