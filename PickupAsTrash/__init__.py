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
    Pickup: unrealsdk.UObject = None
    
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
        
        self.TrashIcon = ModMenu.Options.Spinner(
            Caption="Icon",
            Description="What type of Icon to display next to message.",
            StartingValue=EInteractionIcons.INTERACTION_ICON_PickUp.name[17:],
            Choices=[e.name[17:] for e in EInteractionIcons]
        )
        
        self.Options = [
            self.ShowPopup,
            self.TrashIcon
        ]
        
    def ModOptionChanged(self, option: ModMenu.Options.Base, new_value) -> None:
        if option == self.TrashIcon:
            self.iconOverride.IconDef.Icon = self.TrashIcon.Choices.index(new_value)

    def create_Icon(self) -> None:
        base_icon = unrealsdk.FindObject("InteractionIconDefinition", "GD_InteractionIcons.Default.Icon_DefaultUse")
        icon = unrealsdk.ConstructObject(
            Class=base_icon.Class,
            Outer=base_icon.Outer,
            Name="Icon_PickupAsTrash",
            Template=base_icon,
        )
        unrealsdk.KeepAlive(icon)
        #icon.Icon = EInteractionIcons.INTERACTION_ICON_PickUp
        icon.Icon = self.TrashIcon.Choices.index(self.TrashIcon.CurrentValue)

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
        if params.Pickup.ObjectPointer.bIsMissionItem is False: #Do not show on mission items
            if params.Pickup.ObjectPointer.Inventory.Class != unrealsdk.FindClass("WillowUsableItem"):
                self.Pickup = params.Pickup.ObjectPointer
                if caller.GetPawnInventoryManager().HasRoomInInventoryFor(self.Pickup): #Do not show if inventory is full
                    if caller.PlayerInput.bUsingGamepad:
                        self.preventWeaponCycle=True
                    if self.ShowPopup.CurrentValue:
                        hud_movie = caller.GetHUDMovie()
                        if hud_movie is not None:
                            hud_movie.ShowToolTip(self.iconOverride, EUsabilityType.UT_Secondary)
        return True

    @ModMenu.Hook("WillowGame.WillowPlayerController.PerformedSecondaryUseAction")
    def PerformedSecondaryUseAction(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        item = caller.CurrentSeenPickupable.ObjectPointer
        if(self.Pickup != None and item == self.Pickup):
            item.GetPickupableInventory().Mark = PlayerMark.PM_Trash
            caller.PickupPickupable(item, False)
        return True
    
    preventWeaponCycle: bool = False    # Prevents NextWeapon() firing since when using a controller, SecondaryUse button is shared with NextWeapon

    @ModMenu.Hook("WillowGame.WillowPlayerController.ClearSeenPickupable")
    def NotLookingAt(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        self.preventWeaponCycle=False
        return True

    @ModMenu.Hook("WillowGame.WillowPlayerController.NextWeapon")
    def CycleWeaponHook(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        return not self.preventWeaponCycle
            
        

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
