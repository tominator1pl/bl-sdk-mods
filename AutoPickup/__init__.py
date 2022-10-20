import unrealsdk
import math
from Mods import ModMenu
   
class MyMod(ModMenu.SDKMod):
    Name: str = "AutoPickup"
    Author: str = "Tominator"
    Description: str = "Automaticly Pickups Consumable Items"
    Version: str = "1.0.0"
    SupportedGames: ModMenu.Game = ModMenu.Game.BL2 | ModMenu.Game.TPS  # Either BL2 or TPS; bitwise OR'd together
    Types: ModMenu.ModTypes = ModMenu.ModTypes.Utility  # One of Utility, Content, Gameplay, Library; bitwise OR'd together
    SaveEnabledState: ModMenu.EnabledSaveType = ModMenu.EnabledSaveType.LoadOnMainMenu
    
    Pickinup = False
    pickups = ["Ammo", "Shells", "Cash", "Eridium", "Grenade", "Health", "Seraph"] #Item names to pickup
    
    def Enable(self) -> None:
        super().Enable()
        
    def Disable(self) -> None:
        super().Disable()
    
    def dist(self, a, b) -> float:
        d = 0.0
        d = math.sqrt((b.X - a.X)**2 + (b.Y - a.Y)**2 + (b.Z - a.Z)**2)
        return d
    
    @ModMenu.Hook("WillowGame.WillowPlayerController.PlayerTick")
    def onSpawn(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        maxDist = caller.GetWillowGlobals().GetGlobalsDefinition().PlayerInteractionDistance
        for pickup in caller.GetWillowGlobals().PickupList:
            if pickup.Inventory.Class == unrealsdk.FindClass("WillowUsableItem"):
                distance = self.dist(pickup.Location, caller.CalcViewActorLocation)
                if distance <= maxDist: #Check if item is within Player pickup range
                    if any(ele in pickup.Inventory.ItemName for ele in self.pickups):
                        self.Pickinup = True
                        caller.PickupPickupable(pickup, False)
                        self.Pickinup = False
        return True
    
    #Suppress displaying full inventory
    @ModMenu.Hook("WillowGame.WillowPlayerController.ClientDisplayPickupFailedMessage")
    def ClientDisplayPickupFailedMessage(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        if self.Pickinup:
            return False
        return True
    
    #Suppress item "jumping"
    @ModMenu.Hook("WillowGame.WillowPickup.FailedPickup")
    def FailedPickup(self, caller: unrealsdk.UObject, function: unrealsdk.UFunction, params: unrealsdk.FStruct) -> bool:
        if self.Pickinup:
            return False
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