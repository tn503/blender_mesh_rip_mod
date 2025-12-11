# blender_mesh_rip_mod
Blender addon mesh rip mod in select single vertex

![screen_shot](./screen.jpg)

Default Blender Rip Operator (V key in mesh editmode) does not rip like above image in 4 or more connected face.
Only 3 faces connected.
So, I make addon to do this.

# Usage
Download op_rip_mod.py and Preferences -> Add-ons -> \/ -> Instal from Disk ... .
Enable Single Vertex Rip Operator.
Overwrite V key function.
If not select only single vertex (, or some situation), call bpy.ops.mesh.rip_move('INVOKE_DEFAULT').
