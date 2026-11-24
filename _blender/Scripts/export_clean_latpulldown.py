import bpy
bpy.ops.wm.open_mainfile(filepath=r"G:\Unity_Gym\AI-Gym\_blender\LatPulldown_ani_clean.blend")
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.type in {'MESH', 'ARMATURE', 'EMPTY'}:
        o.select_set(True)
bpy.ops.export_scene.fbx(
    filepath=r"G:\Unity_Gym\AI-Gym\Assets\Gym\1124\LatPulldown_ani.fbx",
    use_selection=True,
    object_types={'ARMATURE', 'MESH', 'EMPTY'},
    use_armature_deform_only=True,
    add_leaf_bones=False,
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=False,
    bake_anim_use_all_actions=False,
    bake_anim_force_startend_keying=True,
    bake_anim_simplify_factor=1.0,
    path_mode='COPY',
    embed_textures=True,
)
print("DONE")
