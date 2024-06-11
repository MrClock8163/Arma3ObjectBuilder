# Backend functions of the vertex mass tools.


import numpy as np
import math

import bmesh
from mathutils import Vector

from . import generic as utils


def can_edit_mass(context):
    obj = context.object
    return obj and obj.type == 'MESH' and obj.mode == 'EDIT'


# Query the sum of the vertex mass of selected vertices.
# The function is used by the selection mass property of the
# vertex mass tools. Obviously not ideal to iterate over all
# vertices frequently, but this is the only working solution,
# and no issues were observed so far (geometry LOD
# meshes are relatively simple).
def get_selection_mass(self):
    if self.type != 'MESH' or self.mode != 'EDIT':
        return 0
    
    bm = bmesh.from_edit_mesh(self.data)
    layer = bm.verts.layers.float.get("a3ob_mass")
    
    if not layer:
        return 0
    
    mass = [vertex[layer] for vertex in bm.verts if vertex.select]
        
    return math.fsum(mass)


# Same efficiency concern applies as above.
# The sum of the vertex masses is taken for the selected
# vertices, then the difference of the sum and the target
# value is distributed equally to the selected vertices.
def set_selection_mass(self, value):
    if self.type != 'MESH' or self.mode != 'EDIT':
        return
    
    with utils.edit_bmesh(self) as bm:
    
        layer = bm.verts.layers.float.get("a3ob_mass")
        if layer is None:
            layer = bm.verts.layers.float.new("a3ob_mass")
            
        verts = [vertex for vertex in bm.verts if vertex.select]
        if len(verts) == 0:
            return
        
        current_mass = get_selection_mass(self)
        diff = value - current_mass
        correction = diff / len(verts)
        
        for vertex in verts:
            vertex[layer] += correction


def set_selection_mass_each(obj, value):
    if obj.type != 'MESH' or obj.mode != 'EDIT':
        return
    
    with utils.edit_bmesh(obj) as bm:
    
        layer = bm.verts.layers.float.get("a3ob_mass")
        if layer is None:
            layer = bm.verts.layers.float.new("a3ob_mass")
            
        for vertex in bm.verts:
            if vertex.select:
                vertex[layer] = round(value, 3)

   
def set_selection_mass_distribute(obj, value):
    if obj.type != 'MESH' or obj.mode != 'EDIT':
        return
    
    with utils.edit_bmesh(obj) as bm:
    
        layer = bm.verts.layers.float.get("a3ob_mass")
        if layer is None:
            layer = bm.verts.layers.float.new("a3ob_mass")
            
        verts = [vertex for vertex in bm.verts if vertex.select]
        if len(verts) == 0:
            return
            
        vertex_value = value / len(verts)
        for vertex in verts:
            vertex[layer] = vertex_value


def clear_selection_masses(obj):
    with utils.edit_bmesh(obj) as bm:
        layer = bm.verts.layers.float.get("a3ob_mass")
        if not layer:
            return
        
        bm.verts.layers.float.remove(layer)


# Volume is calculated as a signed sum of the volume of tetrahedrons
# formed by the vertices of each triangle face and the object origin.
# The formula only yields valid results if the mesh is closed, and
# otherwise manifold.
def calculate_volume(mesh, component):    
    volumes = []
    for face in component:
        v1 = mesh.vertices[face.vertices[0]].co
        v2 = mesh.vertices[face.vertices[1]].co
        v3 = mesh.vertices[face.vertices[2]].co
        volumes.append(v1.dot(v2.cross(v3)) / 6.0)
            
    return math.fsum(volumes)


# The function splits the mesh into loose components, calculates
# the volume of each component, then distributes and equal weight
# to the vertices of each component so that:
# vertex_mass = component_volume * density / count_component_vertices
def set_selection_mass_density(obj, density):
    obj.update_from_editmode()
    mesh = obj.data
    
    component_verts, component_tris, all_closed = utils.get_closed_components(obj)
    stats = [[len(verts), calculate_volume(mesh, tris)] for verts, tris in zip(component_verts, component_tris)] # [vertex count, volume, mass per vertex]
    component_mass = [(volume * density / count_verts) for count_verts, volume in stats]
    
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        
        layer = bm.verts.layers.float.get("a3ob_mass")
        if not layer:
            layer = bm.verts.layers.float.new("a3ob_mass")
        
        for verts, mass in zip(component_verts, component_mass):
            for idx in verts:
                bm.verts[idx][layer] = mass
    
    return all_closed


# Linear conversion of non-zero factor values to [0.001; 1] range.
# 0 is reserved for actual zero values.
def scale_factors(values):
    values_array = np.array(values)
    values_nonzero = values_array[np.nonzero(values_array)]
    if not len(values_nonzero):
        return values
        
    values_min = np.min(values_nonzero)
    values_max = np.max(values_nonzero)
    values_range = values_max - values_min
    
    if values_range == 0:
        return [mass / values_max for mass in values]
    
    coef = 0.999 / values_range
    
    return [max((mass - values_min) * coef + 0.001, 0) for mass in values]


def generate_factors_vertex(bm, layer):
    values = [vert[layer] for vert in bm.verts]
    stats = (0, 0, 0, 0, len(values))
    
    values_array = np.array(values)
    values_nonzero = values_array[np.nonzero(values_array)]
    
    if len(values_nonzero):
        values_min = np.min(values_nonzero)
        values_max = np.max(values_nonzero)
        values_sum = math.fsum(values_nonzero)
        values_avg = values_sum / len(values_nonzero)
        stats = (values_min, values_avg, values_max, values_sum, len(values))
    
    return scale_factors(values), stats


def generate_factors_component(obj, bm, layer):
    component_verts, _ = utils.get_loose_components(obj)
    vertex_lookup = {vert: i for i, comp in enumerate(component_verts) for vert in comp}
    masses = {i: math.fsum([bm.verts[idx][layer] for idx in component]) for i, component in enumerate(component_verts)}
    values = [masses.get(vertex_lookup.get(vert.index), 0) for vert in bm.verts]
    stats = (0, 0, 0, 0, len(masses))
    
    values_array = np.array([masses[id] for id in masses])
    values_nonzero = values_array[np.nonzero(values_array)]
    
    if len(values_nonzero):
        values_min = np.min(values_nonzero)
        values_max = np.max(values_nonzero)
        values_sum = math.fsum(masses.values())
        values_avg = values_sum / len(masses)
        stats = (values_min, values_avg, values_max, values_sum, len(masses))
    
    return scale_factors(values), stats


def interpolate_colors(factors, stops, colorramp):
    bins = np.digitize(factors, stops)
    vcolors = {}
    
    for i, item in enumerate(factors):
        color1 = colorramp[bins[i]]
        color2 = colorramp[bins[i] + 1]
        rate = (item - stops[bins[i] - 1]) / (stops[bins[i]] - stops[bins[i] - 1])
        vcolors[i] = color1.lerp(color2, rate)
    
    return vcolors


def visualize_mass(obj, scene_props):
    obj.update_from_editmode()
    with utils.edit_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()
        
        if not len(bm.verts):
            return
        
        layer = bm.verts.layers.float.get("a3ob_mass")
        if not layer:
            layer = bm.verts.layers.float.new("a3ob_mass")
        
        colorramp = [
            Vector(scene_props.color_0),
            Vector(scene_props.color_0),
            Vector(scene_props.color_1),
            Vector(scene_props.color_2),
            Vector(scene_props.color_3),
            Vector(scene_props.color_4),
            Vector(scene_props.color_5),
            Vector(scene_props.color_5)
        ]
        
        stops = [0, 0.001, 0.25, 0.5, 0.75, 1, 100]
        
        vcolors = {}
        factors = []
        stats = ()
        
        if scene_props.method == 'VERT':
            factors, stats = generate_factors_vertex(bm, layer)
        elif scene_props.method == 'COMP':
            factors, stats = generate_factors_component(obj, bm, layer)
        
        vcolors = interpolate_colors(factors, stops, colorramp)
        
        color_layer = bm.loops.layers.color.get(scene_props.color_layer_name)
        if not color_layer:
            color_layer = bm.loops.layers.color.new(scene_props.color_layer_name)

        for face in bm.faces:
            for loop in face.loops:
                loop[color_layer] = vcolors[loop.vert.index]
        
        scene_props.stats.mass_min = stats[0]
        scene_props.stats.mass_avg = stats[1]
        scene_props.stats.mass_max = stats[2]
        scene_props.stats.mass_sum = stats[3]
        scene_props.stats.count_item = stats[4]


def find_center_of_gravity(obj):
    with utils.query_bmesh(obj) as bm:
        bm.verts.ensure_lookup_table()

        layer = bm.verts.layers.float.get("a3ob_mass")
        if not layer:
            return
        
        contributing = [vert for vert in bm.verts if vert[layer] > 0]
        
        if len(contributing) == 0:
            return
        
        masses = []
        center = Vector()
        for vert in contributing:
            mass = vert[layer]
            masses.append(mass)
            center += vert.co * mass
        
        return center / math.fsum(masses)
