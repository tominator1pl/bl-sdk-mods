import unrealsdk
import math

from Mods import ModMenu

try:
    from Mods.Enums import (EInteractionIcons, EUsabilityType, PlayerMark)
except ImportError:
    import webbrowser
    webbrowser.open("https://bl-sdk.github.io/requirements/?mod=PickupAsTrash&all")
    raise ImportError("Pickup As Trash requires at least Enums version 1.0")

try:
    from Mods.Structs import (InteractionIconWithOverrides)
except ImportError:
    import webbrowser
    webbrowser.open("https://bl-sdk.github.io/requirements/?mod=PickupAsTrash&all")
    raise ImportError("Pickup As Trash requires at least Structs version 1.0")

class MyMod(ModMenu.SDKMod):
    Name: str = "PickupAsTrash"
    Author: str = "Tominator"
    Description: str = "Allows you to pickup items as Trash"
    Version: str = "1.0.0"
    SupportedGames: ModMenu.Game = ModMenu.Game.BL2 | ModMenu.Game.TPS  # Either BL2 or TPS; bitwise OR'd together
    Types: ModMenu.ModTypes = ModMenu.ModTypes.Utility  # One of Utility, Content, Gameplay, Library; bitwise OR'd together
    SaveEnabledState: ModMenu.EnabledSaveType = ModMenu.EnabledSaveType.LoadOnMainMenu
    
    iconOverride: InteractionIconWithOverrides
    Pickup: unrealsdk.UObject
    
    def Enable(self) -> None:
        super().Enable()
        self.create_Icon()
        
    def Disable(self) -> None:
        super().Disable()
    
    def __init__(self) -> None:
        self.ShowPopup = ModMenu.Options.Boolean(
            Caption="Show Pick Up Popup",
            Description="Whether To Display PICK UP AS TRASH Below normal Pick Up.",
            StartingValue=True,
            Choices=["No", "Yes"]  # False, True
        )
        
        self.Options = [
            self.ShowPopup,
        ]

    def create_Icon(self) -> None:
        base_icon = unrealsdk.FindObject("InteractionIconDefinition", "GD_InteractionIcons.Default.Icon_DefaultUse")
        icon = unrealsdk.ConstructObject(
            Class=base_icon.Class,
            Outer=base_icon.Outer,
            Name="Icon_PickupAsTrash",
            Template=base_icon,
        )
        unrealsdk.KeepAlive(icon)
        icon.Icon = EInteractionIcons.INTERACTION_ICON_PickUp

        PC = unrealsdk.GetEngine().GamePlayers[0].Actor
        #buttons = list(inputDevice.Buttons)
        #buttons.append(inputDeviceButtonData)
        #inputDevice.Buttons = unrealsdk.FArray(buttons)
        # Setting values directly on the object causes a crash on quitting the game
        # Everything still works fine, not super necessary to fix, but people get paranoid
        # https://github.com/bl-sdk/PythonSDK/issues/45
        PC.ServerRCon(f"set {PC.PathName(icon)} Action UseSecondary")
        PC.ServerRCon(f"set {PC.PathName(icon)} Text PICK UP AS TRASH")

        self.iconOverride = InteractionIconWithOverrides(IconDef = icon)

    @ModMenu.Hook("WillowGame.WillowPlayerController.SawPickupable")
    def onSpawn(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        if params.Pickup.ObjectPointer.Inventory.Class != unrealsdk.FindClass("WillowUsableItem"):
            self.Pickup = params.Pickup.ObjectPointer
            if self.ShowPopup.CurrentValue:
                hud_movie = caller.GetHUDMovie()
                if hud_movie is not None:
                    hud_movie.ShowToolTip(self.iconOverride, EUsabilityType.UT_Secondary)
        return True

    @ModMenu.Hook("WillowGame.WillowPlayerController.PerformedSecondaryUseAction")
    def PerformedSecondaryUseAction(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        item = caller.CurrentSeenPickupable.ObjectPointer
        if(item == self.Pickup):
            item.GetPickupableInventory().Mark = PlayerMark.PM_Trash
            caller.PickupPickupable(item, False)
        return True
    
            
            
        

instance = MyMod()
   
if __name__ == "__main__":
    unrealsdk.Log(f"[{instance.Name}] Manually loaded")
    for mod in ModMenu.Mods:
        if mod.Name == instance.Name:
            if mod.IsEnabled:
                mod.Disable()
            ModMenu.Mods.remove(mod)
            unrealsdk.Log(f"[{instance.Name}] Removed last instance")

            # Fixes inspect.getfile()
            instance.__class__.__module__ = mod.__class__.__module__
            break
ModMenu.RegisterMod(instance)