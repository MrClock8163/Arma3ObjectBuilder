# Backend logic for data validation.


import re
import math

import bmesh
import bpy

from ..io.data_p3d import P3D_LOD_Resolution as LOD


class ValidatorResult():
    def __init__(self, is_valid = True, comment = ""):
        self.is_valid = is_valid
        self.comment = comment
    
    def __bool__(self):
        return self.is_valid
    
    def set(self, is_valid = True, comment = ""):
        self.is_valid = is_valid
        self.comment = comment


class ValidatorComponent():
    """Base component"""

    @staticmethod
    def is_ascii_internal(value):
        try:
            value.encode("ascii")
            return True
        except:
            return False

    def conditions(self):
        strict = optional = info = ()

        return strict, optional, info
    
    def validate_lazy(self, warns_errs):
        strict, optional, _ = self.conditions()

        for item in strict:
            result = item()
            if not result:
                return False
        
        if warns_errs:
            for item in optional:
                result = item()
                if not result:
                    return False
        
        return True

    def validate_verbose(self, warns_errs):
        strict, optional, info = self.conditions()
        is_valid = True
        self.logger.level_up()

        for item in strict:
            result = item()
            if not result:
                self.logger.step("ERROR: %s" % result.comment)
                is_valid = False
        
        for item in optional:
            result = item()
            if not result:
                self.logger.step("WARNING: %s" % result.comment)
                is_valid &= not warns_errs
        
        for item in info:
            result = item()
            self.logger.step("INFO: %s" % result.comment)

        self.logger.level_down()

        return is_valid

    
    def validate(self, lazy, warns_errs):
        is_valid = True

        if lazy:
            is_valid = self.validate_lazy(warns_errs)
        else:
            self.logger.step("RULESET: %s" % self.__doc__)
            is_valid = self.validate_verbose(warns_errs)

        return is_valid


class ValidatorComponentLOD(ValidatorComponent):
    """LOD - Base component"""

    def __init__(self, obj, bm, logger, relative_paths = False):
        self.obj = obj
        self.bm = bm
        self.logger = logger
        self.relative_paths = relative_paths

    def is_contiguous(self):
        result = ValidatorResult()

        for edge in self.bm.edges:
            if not edge.is_contiguous:
                result.set(False, "mesh is not contiguous")
                break
            
        return result

    def is_triangulated(self):
        result = ValidatorResult()

        for face in self.bm.faces:
            if len(face.verts) > 3:
                result.set(False, "mesh is not triangulated")
                break
                
        return result

    def no_ngons(self):
        result = ValidatorResult()

        for face in self.bm.faces:
            if len(face.verts) > 4:
                result.set(False, "mesh has n-gons")
                break
        
        return result
    
    def max_two_uvs(self):
        result = ValidatorResult()

        if len(self.obj.data.uv_layers) > 2:
            result.set(False, "mesh has more than 2 UV channels")

        return result

    def has_selection_internal(self, re_selection):
        if len(self.bm.verts) == 0:
            return False
        
        RE_NAME = re.compile(re_selection, re.IGNORECASE)
        for group in self.obj.vertex_groups:
            if RE_NAME.match(group.name):
                return True
        
        return False
    
    def only_ascii_vgroups(self):
        result = ValidatorResult()

        for group in self.obj.vertex_groups:
            if not self.is_ascii_internal(group.name):
                result.set(False, "mesh has vertex groups with non-ASCII characters (first encountered: %s)" % group.name)
                break

        return result
    
    def only_ascii_materials(self):
        result = ValidatorResult()

        for slot in self.obj.material_slots:
            mat = slot.material
            if not mat:
                continue

            texture, material = mat.a3ob_properties_material.to_p3d(self.relative_paths)
            if not self.is_ascii_internal(texture) or not self.is_ascii_internal(material):
                result.set(False, "mesh has materials with non-ASCII characters (first encountered: %s)" % mat.name)
                break

        return result

    def only_ascii_properties(self):
        result = ValidatorResult()

        for prop in self.obj.a3ob_properties_object.properties:
            value = "%s = %s" % (prop.name, prop.value)
            if not self.is_ascii_internal(value):
                result.set(False, "mesh has named properties with non-ASCII characters (first encountered: %s)" % value)
                break

        return result

    def only_ascii_proxies(self):
        result = ValidatorResult()

        if self.obj.a3ob_properties_object_proxy.is_a3_proxy:
            path, _ = self.obj.a3ob_properties_object_proxy.to_placeholder(self.relative_paths)
            if not self.is_ascii_internal(path):
                result.set(False, "mesh has proxy path with non-ASCII characters")

        return result


class ValidatorLODGeneric(ValidatorComponentLOD):
    """LOD - Generic"""
    
    def conditions(self):
        strict = (
            self.no_ngons,
            self.only_ascii_materials,
            self.only_ascii_vgroups,
            self.only_ascii_properties,
            self.only_ascii_proxies
        )
        optional = (
            self.max_two_uvs,
        )
        
        info = ()

        return strict, optional, info


class ValidatorLODGeometry(ValidatorComponentLOD):
    """LOD - Geometry"""

    def is_triangulated(self):
        result =  super().is_triangulated()
        if not result:
            result.set(False, "mesh is not triangulated (convexity is not definite)")
        
        return result
    
    def is_convex_edge_internal(self, edge):
        if edge.is_convex:
            return True
        
        face1 = edge.link_faces[0]
        face2 = edge.link_faces[1]
        dot = face1.normal.dot(face2.normal)

        if not (0.9999 <= dot <= 1.0001):
            return False
        
        return True

    def is_convex(self):
        result = ValidatorResult()

        for edge in self.bm.edges:
            if not self.is_convex_edge_internal(edge):
                result.set(False, "mesh is not convex")
                break
        
        return result
    
    def has_components(self):
        result = ValidatorResult()

        if not self.has_selection_internal("component\d+"):
            result.set(False, "mesh has no component selections")
        
        return result
    
    def has_mass(self):
        result = ValidatorResult()

        layer = self.bm.verts.layers.float.get("a3ob_mass")
        if not layer or math.fsum([vert[layer] for vert in self.bm.verts]) < 0.001:
            result.set(False, "mesh has no vertex mass assigned")

        return result
    
    def no_unweighted(self):
        result = ValidatorResult()

        layer = self.bm.verts.layers.float.get("a3ob_mass")
        if not layer:
            result.set(False, "mesh has vertices with no vertex mass assigned")
            return result
        
        for vert in self.bm.verts:
            if vert[layer] < 0.001:
                result.set(False, "mesh has vertices with no vertex mass assigned")
                break
        
        return result

    def farthest_point(self):
        distance = 0
        for vertex in self.bm.verts:
            if vertex.co.length > distance:
                distance = vertex.co.length
        
        return ValidatorResult(True, "distance of farthest point from origin is %.3f meters" % distance)

    def conditions(self):
        strict = (
            self.is_convex,
            self.has_mass
        )
        if not self.has_selection_internal("occluder\d+"):
            strict = (
                self.is_contiguous,
                self.has_components,
                *strict
            )
        optional = (
            self.is_triangulated,
            self.no_unweighted
        )
        info = (
            self.farthest_point,
        )

        return strict, optional, info


class ValidatorLODGeometrySubtype(ValidatorLODGeometry):
    """LOD - Geometry subtype"""

    def conditions(self):
        strict = (
            self.is_convex,
        )
        if not self.has_selection_internal("occluder\d+"):
            strict = (
                self.is_contiguous,
                self.has_components,
                *strict
            )
        optional = (
            self.is_triangulated,
        )
        info = ()

        return strict, optional, info
    

class ValidatorLODShadow(ValidatorComponentLOD):
    """LOD - Shadow"""

    def is_sharp(self):
        result = ValidatorResult()

        for face in self.bm.faces:
            if face.smooth:
                break
        else:
            return result

        for edge in self.bm.edges:
            if edge.smooth and edge.is_manifold:
                result.set(False, "mesh has smooth edges")
                break
        
        return result
    
    def no_materials(self):
        result = ValidatorResult()

        materials = {}
        for i, slot in enumerate(self.obj.material_slots):
            mat = slot.material
            if not mat:
                materials[i] = ("", "")
                continue

            materials[i] = mat.a3ob_properties_material.to_p3d(False)
        
        if len(materials) > 0:
            for face in self.bm.faces:
                if materials[face.material_index] != ("", ""):
                    result.set(False, "mesh has materials assigned")
                    break
            
        return result

    def only_conventional_indices(self):
        result = ValidatorResult()

        idx = self.obj.a3ob_properties_object.resolution
        if idx not in {0, 10, 1000, 1010, 1020}:
            result.set(False, "unconventional shadow resolution: %d" % idx)

        return result
    
    def not_disabled(self):
        result = ValidatorResult()

        for prop in self.obj.a3ob_properties_object.properties:
            if prop.name.strip().lower() == "lodnoshadow" and prop.value.strip() == "1":
                result.set(False, "disabled by property (LODNoShadow = 1)")
                break

        return result
    
    def conditions(self):
        strict = (
            self.is_contiguous,
            self.is_triangulated,
            self.is_sharp,
            self.no_materials
        )
        optional = (
            self.only_conventional_indices,
            self.not_disabled
        )
        
        info = ()

        return strict, optional, info


class ValidatorLODUnderground(ValidatorLODGeometry, ValidatorLODShadow):
    """LOD - Underground (VBS)"""

    def conditions(self):
        strict = (
            self.is_contiguous,
            self.is_triangulated,
            self.is_convex,
            self.has_components,
            self.is_sharp,
            self.no_materials
        )
        optional = ()
        info = (
            self.farthest_point,
        )

        return strict, optional, info


class ValidatorLODPointcloud(ValidatorComponentLOD):
    """LOD - Point cloud"""

    def no_edges(self):
        result = ValidatorResult()

        if len(self.bm.edges) > 0:
            result.set(False, "point cloud contains edges")

        return result
    
    def no_faces(self):
        result = ValidatorResult()

        if len(self.bm.faces) > 0:
            result.set(False, "point cloud contains faces")
        
        return result
    
    def conditions(self):
        strict = info = ()
        optional = (
            self.no_edges,
            self.no_faces
        )

        return strict, optional, info


class ValidatorLODRoadway(ValidatorComponentLOD):
    """LOD - Roadway"""

    def under_limit(self):
        result = ValidatorResult()

        if len(self.bm.verts) > 255:
            result.set(False, "mesh has more than 255 points (animations will not work properly)")

        return result
    
    def has_faces(self):
        result = ValidatorResult()

        if len(self.bm.faces) == 0:
            result.set(False, "mesh has no faces")

        return result

    def has_sound(self):
        result = ValidatorResult()

        textures = {}
        for i, slot in enumerate(self.obj.material_slots):
            mat = slot.material
            if not mat:
                textures[i] = ""
                continue
                
            textures[i] = mat.a3ob_properties_material.to_p3d(False)[0]
        
        if len(textures) == 0:
            result.set(False, "mesh has no sound textures assigned")
        else:
            for face in self.bm.faces:
                if textures[face.material_index] == "":
                    result.set(False, "mesh has faces with no sound texture assigned")
                    break

        return result

    def farthest_point(self):
        distance = 0
        for vertex in self.bm.verts:
            if vertex.co.length > distance:
                distance = vertex.co.length
        
        return ValidatorResult(True, "distance of farthest point from origin is %.3f meters" % distance)
    
    def conditions(self):
        strict = (
            self.has_faces,
        )
        optional = (
            self.under_limit,
            self.has_sound
        )
        info = (
            self.farthest_point,
        )

        return strict, optional, info


class ValidatorLODGroundlayer(ValidatorLODRoadway, ValidatorComponentLOD):
    """LOD - Groundlayer (VBS)"""

    def has_uv_channel(self):
        result = ValidatorResult()

        if len(self.obj.data.uv_layers) != 1:
            result.set(False, "mesh has no UV data or more than 1 UV channel")
        
        return result
    
    def only_valid_uvs(self):
        result = ValidatorResult()
        
        if len(self.obj.data.uv_layers) != 1:
            return result
        
        valid_uvs = {(0, 0), (1, 0), (1, 1), (1, -1)}
        for uv in self.obj.data.uv_layers[0].uv:
            u, v = uv.vector
            if (u, v) not in valid_uvs:
                result.set(False, "mesh has invalid UV values")
                break

        return result
    
    def conditions(self):
        strict = (
            self.has_faces,
            self.has_uv_channel,
            self.only_valid_uvs
        )
        optional = info = ()

        return strict, optional, info


class ValidatorLODPaths(ValidatorComponentLOD):
    """LOD - Paths"""

    def has_faces(self):
        result = ValidatorResult()

        if len(self.bm.faces) == 0:
            result.set(False, "mesh has no faces")

        return result
    
    def has_entry(self):
        result = ValidatorResult()

        if not self.has_selection_internal("in\d+"):
            result.set(False, "mesh has no entry points assigned")
        
        return result
    
    def has_position(self):
        result = ValidatorResult()

        if not self.has_selection_internal("in\d+"):
            result.set(False, "mesh has no position points assigned")
        
        return result

    def conditions(self):
        strict = (
            self.has_faces,
            self.has_entry
        )
        optional = (
            self.has_position,
        )
        info = ()

        return strict, optional, info


class ValidatorComponentSkeleton(ValidatorComponent):
    """Skeleton - Base component"""

    def __init__(self, skeleton, logger):
        self.skeleton = skeleton
        self.logger = logger
    
    def has_valid_name(self):
        result = ValidatorResult()

        if not self.is_ascii_internal(self.skeleton.name) or " " in self.skeleton.name:
            result.set(False, "skeleton name contains spaces and/or non-ASCII characters")

        return result
    
    def only_unique_bones(self):
        result = ValidatorResult()

        names = set()
        for bone in self.skeleton.bones:
            if bone.name.lower() in names:
                result.set(False, "skeleton has duplicate bones (first encountered: %s)" % bone.name)
                break

            names.add(bone.name.lower())

        return result
    
    def has_valid_hierarchy(self):
        result = ValidatorResult()

        bones = self.skeleton.bones
        bone_order = {}
        for bone in bones:
            if bone.parent != "" and bone.parent not in bone_order:
                result.set(False, "skeleton has invalid bone hierarchy (first invalid bone encountered: %s)" % bone.name)
                break
        
            bone_order[bone.name] = bone.parent

        return result

    def only_ascii_bones(self):
        result = ValidatorResult()

        for bone in self.skeleton.bones:
            if not self.is_ascii_internal(bone.name) or not self.is_ascii_internal(bone.parent):
                result.set(False, "skeleton has bones with non-ASCII characters (first encountered: %s)" % bone.name)
                break

        return result


class ValidatorSkeletonGeneric(ValidatorComponentSkeleton):
    """Skeleton - Generic"""

    def conditions(self):
        strict = (
            self.has_valid_name,
            self.only_unique_bones,
            self.has_valid_hierarchy,
            self.only_ascii_bones
        )
        optional = info = ()

        return strict, optional, info


class ValidatorSkeletonRTM(ValidatorComponentSkeleton):
    """Skeleton - RTM"""

    def has_rtm_compatible_bones(self):
        result = ValidatorResult()

        for bone in self.skeleton.bones:
            if len(bone.name) > 31 or len(bone.parent) > 31:
                result.set(False, "skeleton has bone names longer than 31 characters")
                break

        return result

    def conditions(self):
        strict = (
            self.has_rtm_compatible_bones,
        )
        optional = info = ()

        return strict, optional, info


class Validator():
    def __init__(self, logger):
        self.logger = logger
        self.components = {}
    
    def setup_lod_specific(self):
        self.components = {
            **dict.fromkeys(
                (
                    str(LOD.SHADOW),
                    str(LOD.SHADOW_VIEW_CARGO),
                    str(LOD.SHADOW_VIEW_PILOT),
                    str(LOD.SHADOW_VIEW_GUNNER)
                ), 
                [ValidatorLODShadow]
            ),
            **dict.fromkeys(
                (
                    str(LOD.MEMORY),
                    str(LOD.LANDCONTACT),
                    str(LOD.HITPOINTS)
                ),
                [ValidatorLODPointcloud]
            ),
            **dict.fromkeys(
                (
                    str(LOD.GEOMETRY_BUOY),
                    str(LOD.GEOMETRY_PHYSX),
                    str(LOD.VIEW_GEOMETRY),
                    str(LOD.FIRE_GEOMETRY),
                    str(LOD.VIEW_CARGO_GEOMERTRY),
                    str(LOD.VIEW_CARGO_FIRE_GEOMETRY),
                    str(LOD.VIEW_COMMANDER_GEOMETRY),
                    str(LOD.VIEW_COMMANDER_FIRE_GEOMETRY),
                    str(LOD.VIEW_PILOT_GEOMETRY),
                    str(LOD.VIEW_PILOT_FIRE_GEOMETRY),
                    str(LOD.VIEW_GUNNER_GEOMETRY),
                    str(LOD.VIEW_GUNNER_FIRE_GEOMETRY)
                ),
                [ValidatorLODGeometrySubtype]
            ),
            str(LOD.GEOMETRY): [ValidatorLODGeometry],
            str(LOD.ROADWAY): [ValidatorLODRoadway],
            str(LOD.PATHS): [ValidatorLODPaths],
            str(LOD.UNDERGROUND): [ValidatorLODUnderground],
            str(LOD.GROUNDLAYER): [ValidatorLODGroundlayer]
        }

    def validate_lod(self, obj, lod, lazy = False, warns_errs = True, relative_paths = False):
        self.logger.step("Validating %s" % obj.name)
        self.logger.level_up()
        if warns_errs:
            self.logger.step("Warnings are errors")

        obj.update_from_editmode()
        bm = bmesh.new()
        bm.from_mesh(obj.evaluated_get(bpy.context.evaluated_depsgraph_get()).data)
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()
        bm.faces.ensure_lookup_table()

        is_valid = True
        for item in [ValidatorLODGeneric] + self.components.get(lod, []):
            is_valid &= item(obj, bm, self.logger, relative_paths).validate(lazy, warns_errs)

        bm.free()
        self.logger.step("Validation %s" % ("PASSED" if is_valid else "FAILED"))
        self.logger.level_down()
        self.logger.step("Finished validation")

        return is_valid
    
    def validate_skeleton(self, skeleton, for_rtm = False, lazy = False):
        self.logger.step("Validating %s" % skeleton.name)
        self.logger.level_up()

        is_valid = True
        components = [ValidatorSkeletonGeneric]
        if for_rtm:
            components.append(ValidatorSkeletonRTM)

        for item in components:
            is_valid &= item(skeleton, self.logger).validate(lazy, False)
        
        self.logger.step("Validation %s" % ("PASSED" if is_valid else "FAILED"))
        self.logger.level_down()
        self.logger.step("Finished validation")

        return is_valid
