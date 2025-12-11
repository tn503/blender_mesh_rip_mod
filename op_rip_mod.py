import bpy
import bmesh
from bpy_extras import view3d_utils
import mathutils
import math

bl_info = {"name": "Single Vertex Rip Operator", "version": (1, 0),}

def main(self, context):
    c = bpy.context
    
    if c.mode=='EDIT_MESH':
        obj = c.object
        bm = bmesh.from_edit_mesh(obj.data)
        bpy.ops.ed.undo_push()
        
        select_verts = [v for v in bm.verts if v.select]
        
        if len(select_verts) == 1:
            select_vert = select_verts[0]
            if not select_vert.is_manifold or len(select_vert.link_faces)==1:
                self.report({'ERROR'}, "Cannot rip")
                return
            if select_vert.is_wire or len(select_vert.link_faces)==2: 
                bpy.ops.mesh.rip_move('INVOKE_DEFAULT')
                return
                
            
            mp = mathutils.Vector((self.x, self.y))
            dmin = 10000
            best = None
            
            for f in select_vert.link_faces:
                f_center = f.calc_center_median()
                f_center2d = view3d_utils.location_3d_to_region_2d(c.region, c.space_data.region_3d, f_center)
                dist0 = (mp - f_center2d).length
                
                #closest_point_on_tri
                v_2d = []
                for v in f.verts:
                    vxy = view3d_utils.location_3d_to_region_2d(c.region, c.space_data.region_3d, v.co)
                    v_2d.append(vxy)
                    
                closest_point = mathutils.geometry.closest_point_on_tri(mp, v_2d[0], v_2d[1], v_2d[2])
                dist1 = (closest_point - mp.to_3d()).length
                if len(f.verts) == 4:
                    closest_point2 = mathutils.geometry.closest_point_on_tri(mp, v_2d[0], v_2d[2], v_2d[3])
                    dist2 = (closest_point2 - mp.to_3d()).length
                    if dist2 < dist1:
                        dist1 = dist2
                
                dist = min(dist0, dist1, dist2)
                
                if dist < dmin:
                    best = f
                    dmin = dist
                    
            
            dmin += 0.0001 #give edge an advantage

            edge_rotate_angle = 15 #degrees
            for e in select_vert.link_edges:
                v2 = e.other_vert(select_vert)
                v1_2d = view3d_utils.location_3d_to_region_2d(c.region, c.space_data.region_3d, select_vert.co)
                v2_2d = view3d_utils.location_3d_to_region_2d(c.region, c.space_data.region_3d, v2.co)
                #closest_point, dist = mathutils.geometry.intersect_point_line_segment(mp, v1_2d, v2_2d)
                
                #edge rotate +-edge_rotate_angle and make triangle and hittest
                v3 = (v2_2d - v1_2d).to_3d()
                v4 = v3.copy()
                eul1 = mathutils.Euler((0.0, 0.0, math.radians(edge_rotate_angle)), 'XYZ')
                eul2 = mathutils.Euler((0.0, 0.0, math.radians(-edge_rotate_angle)), 'XYZ')
                v3.rotate(eul1)
                v4.rotate(eul2)
                
                closest_point = mathutils.geometry.closest_point_on_tri(mp, v1_2d, v1_2d + v3.to_2d(), v1_2d + v4.to_2d())
                dist = (closest_point - mp.to_3d()).length
                
                if dist < dmin:
                    best = e
                    dmin = dist
                    

            do_nothing = True
            if best:
                if type(best) is bmesh.types.BMFace:
                    v_new = bmesh.utils.face_vert_separate(best, select_vert)
                    
                    select_vert.select = False
                    bm.select_history.remove(select_vert)
                    v_new.select = True
                    bm.select_history.add(v_new)
                    bmesh.update_edit_mesh(obj.data)
                    do_nothing = False
                    
                elif type(best) is bmesh.types.BMEdge:
                    if len(best.link_faces)==2:
                        v_new_array = []
                        for f in best.link_faces[:]:
                            v_new = bmesh.utils.face_vert_separate(f, select_vert)
                            v_new_array.append(v_new)
                        
                        bmesh.utils.vert_splice(v_new_array[0], v_new_array[1])
                        
                        select_vert.select = False
                        bm.select_history.remove(select_vert)
                        v_new_array[1].select = True
                        bm.select_history.add(v_new_array[1])
                        bmesh.update_edit_mesh(obj.data)
                        do_nothing = False
                
                if do_nothing:
                    bpy.ops.mesh.rip_move('INVOKE_DEFAULT')
                else:
                    bpy.ops.transform.translate('INVOKE_DEFAULT')
            
            


class SingleVertexRipOperator(bpy.types.Operator):
    """Single Vertex Rip Operator"""
    bl_idname = "object.single_vertex_rip_operator"
    bl_label = "Single Vertex Rip Operator"
    bl_options = {'REGISTER',}

    x: bpy.props.IntProperty()
    y: bpy.props.IntProperty()
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        main(self, context)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        self.x, self.y = event.mouse_region_x, event.mouse_region_y
        return self.execute(context)


def menu_func(self, context):
    self.layout.operator(SingleVertexRipOperator.bl_idname, text=SingleVertexRipOperator.bl_label)




def register():
    bpy.utils.register_class(SingleVertexRipOperator)
    #direct call execute from edit_mesh_context_menu, so dont get mouse position
    #bpy.types.VIEW3D_MT_edit_mesh_context_menu.prepend(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.append(menu_func)
    
    key_config = bpy.context.window_manager.keyconfigs.addon
    if key_config:
        key_map = key_config.keymaps.new(name='Mesh', space_type='EMPTY')
        key_entry = key_map.keymap_items.new("object.single_vertex_rip_operator",
                                            type='V',
                                            value='PRESS',
                                            #shift=True,#ctrl=True,
        )
    


def unregister():
    bpy.utils.unregister_class(SingleVertexRipOperator)
    #bpy.types.VIEW3D_MT_edit_mesh_context_menu.remove(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_vertices.remove(menu_func)


if __name__ == "__main__":
    register()


