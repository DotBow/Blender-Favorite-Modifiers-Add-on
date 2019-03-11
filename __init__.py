# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>


import bpy
from bl_ui.properties_data_modifier import (DATA_PT_gpencil_modifiers,
                                            DATA_PT_modifiers)
from bpy.app.handlers import persistent
from bpy.props import (BoolProperty, EnumProperty, PointerProperty,
                       StringProperty)
from bpy.types import (AddonPreferences, GpencilModifier, Menu, Modifier,
                       Operator, Panel, PropertyGroup, Scene)
from bpy.utils import register_class, unregister_class

bl_info = {
    "name": "Favorite Modifiers",
    "description": "Shows buttons with favorite modifiers on top of the Modifier Stack",
    "author": "Oleg Stepanov",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "Properties Editor > Modifiers",
    "warning": "",
    "wiki_url": "",
    "support": 'COMMUNITY',
    "category": "Modifiers"
}


class FavoriteModifiersAddonPreferences(AddonPreferences):
    bl_idname = __name__

    display_style_items = [
        ("BUTTONS", "Buttons", "", 1),
        ("ICONS", "Icons", "", 2),
    ]

    display_style = EnumProperty(
        name="Display Style", items=display_style_items)

    def draw(self, context):
        layout = self.layout
        col = layout.column()
        col.label(text="Favorite modifiers grouped per object type:")
        col.label(text="Mesh, Lattice, Curve/Font/Surface, Grease Pencil.")
        col.label(text="Favorite modifiers stored in Startup File.")
        layout.prop(self, "display_style")


def get_favorite_modifiers(context):
    ob_type = context.active_object.type
    favorite_modifiers = context.scene.favorite_modifiers

    if ob_type in 'CURVE FONT SURFACE':
        ob_type = 'CURVE'

    return getattr(favorite_modifiers, ob_type.lower() + '_modifiers')


def set_favorite_modifiers(context, value):
    ob_type = context.active_object.type
    favorite_modifiers = context.scene.favorite_modifiers

    if ob_type in 'CURVE FONT SURFACE':
        ob_type = 'CURVE'

    setattr(favorite_modifiers, ob_type.lower() + '_modifiers', value)


class MODIFIER_OT_append_to_favorites(Operator):
    """Add to Favorite Modifiers list (stored in Startup File)"""
    bl_idname = "object.append_to_favorites"
    bl_label = "Add to Favorites Modifiers"

    mod_type: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        fm = get_favorite_modifiers(context)
        set_favorite_modifiers(context, fm + self.mod_type + ',')
        context.area.tag_redraw()
        return {'FINISHED'}


class MODIFIER_OT_remove_from_favorites(Operator):
    """Remove from Favorite Modifiers list (stored in Startup File)"""
    bl_idname = "object.remove_from_favorites"
    bl_label = "Remove from Favorites Modifiers"

    mod_type: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.object is not None

    def execute(self, context):
        fm = get_favorite_modifiers(context)
        set_favorite_modifiers(context, fm.replace(self.mod_type + ',', ''))
        context.area.tag_redraw()
        return {'FINISHED'}


class MODIFIER_OT_add_favorite_modifier(Operator):
    """Add a procedural operation/effect to the active object"""
    bl_idname = "object.add_favorite_modifier"
    bl_label = "Add Favorite Modifier"

    mod_type: StringProperty()

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        active_object_type = context.active_object.type

        if active_object_type == 'GPENCIL':
            bpy.ops.object.gpencil_modifier_add(type=self.mod_type)
        else:
            bpy.ops.object.modifier_add(type=self.mod_type)
        return {'FINISHED'}


class WM_MT_button_context(Menu):
    bl_label = "Append/Remove Favorite Modifier"

    def draw(self, context):
        if context.space_data.context != 'MODIFIER':
            return

        if hasattr(context, 'button_operator'):
            op = context.button_operator

            if "modifier_add" in str(getattr(op, 'bl_rna')):
                mod_type = getattr(op, 'type')
                layout = self.layout
                layout.separator()

                if mod_type not in get_favorite_modifiers(context):
                    layout.operator("object.append_to_favorites",
                                    icon='SOLO_ON').mod_type = mod_type
                else:
                    layout.operator("object.remove_from_favorites",
                                    icon='SOLO_ON').mod_type = mod_type
            elif "add_favorite_modifier" in str(getattr(op, 'bl_rna')):
                layout = self.layout
                layout.separator()
                layout.operator("object.remove_from_favorites",
                                icon='SOLO_ON').mod_type = getattr(op, 'mod_type')


class FavoriteModifiers(PropertyGroup):
    curve_modifiers = StringProperty(default="")
    lattice_modifiers = StringProperty(default="")
    gpencil_modifiers = StringProperty(default="")
    mesh_modifiers = StringProperty(default="")


def find(f, seq):
    for item in seq:
        if f(item):
            return item

    return None


def draw_favorite_modifiers(self, context):
    mods = []
    fms = get_favorite_modifiers(context)[:-1].split(',')

    for mod_type in fms:
        mod = find(lambda mod: mod.identifier == mod_type, modifiers)
        if mod:
            mods.append(mod)

    if len(mods) > 0:
        layout = self.layout
        prefs = context.preferences
        addon_prefs = prefs.addons[__name__].preferences
        display_style = addon_prefs.display_style

        if display_style == 'BUTTONS':
            grid_flow = layout.grid_flow(
                row_major=True, columns=2,
                even_columns=True, even_rows=True,
                align=True)

            for mod in mods:
                grid_flow.operator("object.add_favorite_modifier",
                                   text=mod.name,
                                   icon=mod.icon).mod_type = mod.identifier
        elif display_style == 'ICONS':
            grid_flow = layout.grid_flow(
                row_major=True, columns=0,
                even_columns=True, even_rows=True,
                align=True)
            grid_flow.scale_x = 1.4
            grid_flow.scale_y = 1.4

            for mod in mods:
                grid_flow.operator("object.add_favorite_modifier", text="",
                                   icon=mod.icon).mod_type = mod.identifier


classes = (
    FavoriteModifiersAddonPreferences,
    MODIFIER_OT_append_to_favorites,
    MODIFIER_OT_remove_from_favorites,
    MODIFIER_OT_add_favorite_modifier,
    WM_MT_button_context,
    FavoriteModifiers,
)


modifiers = []


def register():
    for cls in classes:
        register_class(cls)

    Scene.favorite_modifiers = PointerProperty(type=FavoriteModifiers)

    for mod in Modifier.bl_rna.properties['type'].enum_items:
        modifiers.append(mod)

    for mod in GpencilModifier.bl_rna.properties['type'].enum_items:
        modifiers.append(mod)

    DATA_PT_modifiers.prepend(draw_favorite_modifiers)
    DATA_PT_gpencil_modifiers.prepend(draw_favorite_modifiers)


def unregister():
    for cls in classes:
        unregister_class(cls)

    DATA_PT_modifiers.remove(draw_favorite_modifiers)
    DATA_PT_gpencil_modifiers.remove(draw_favorite_modifiers)


if __name__ == "__main__":
    register()