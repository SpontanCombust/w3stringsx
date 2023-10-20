function IBT_IsDLCBeard() : bool
{
	var customHead	: name;

	// keep in mind that it will work properly only if when setting head beforehand it was also remembered in thePlayer
	// if it was done through an actual in-game barber, it will work 100%
	customHead = thePlayer.GetRememberedCustomHead();

	return IsNameValid( customHead );
}

function IBT_GetGeraltBeardStage() : int
{
	var components	: array< CComponent >;
	var headManager	: CHeadManagerComponent;
	var curHead		: name;
	var stage		: int;
	
	components = thePlayer.GetComponentsByClassName( 'CHeadManagerComponent' );
	headManager = ( ( CHeadManagerComponent ) components[0] );
	curHead = headManager.GetCurHeadName();

	switch( curHead )
	{
		case 'head_0':
		case 'head_0_tattoo':
		case 'head_0_mark':
		case 'head_0_mark_tattoo':
			stage = 0;
			break;
		case 'head_1':
		case 'head_1_tattoo':
		case 'head_1_mark':
		case 'head_1_mark_tattoo':
			stage = 1;
			break;
		case 'head_2':
		case 'head_2_tattoo':
		case 'head_2_mark':
		case 'head_2_mark_tattoo':
			stage = 2;
			break;
		case 'head_3':
		case 'head_3_tattoo':
		case 'head_3_mark':
		case 'head_3_mark_tattoo':
			stage = 3;
			break;
		case 'head_4':
		case 'head_4_tattoo':
		case 'head_4_mark':
		case 'head_4_mark_tattoo':
			stage = 4;
			break;
		default:
			stage = -1;
	}

	return stage;
}

function IBT_TrimGeraltBeard() : bool
{
	var components		: array< CComponent >;
	var headManager		: CHeadManagerComponent;
	var destBeardStage	: int;

	components = thePlayer.GetComponentsByClassName( 'CHeadManagerComponent' );
	headManager = ( ( CHeadManagerComponent ) components[0] );

	if( IBT_IsDLCBeard() )
	{
		destBeardStage = 0;
	}
	else
	{
		destBeardStage = IBT_GetGeraltBeardStage() - 1;
	}

	if( destBeardStage >= 0 )
	{
		thePlayer.ClearRememberedCustomHead();
		headManager.RemoveCustomHead();
		headManager.SetBeardStage( false, destBeardStage );
		headManager.BlockGrowing( false );
		return true;
	}
	else
	{
		return false;
	}
}

function IBT_GrowGeraltBeard() : bool
{
	var components		: array< CComponent >;
	var headManager		: CHeadManagerComponent;
	var destBeardStage	: int;

	components = thePlayer.GetComponentsByClassName( 'CHeadManagerComponent' );
	headManager = ( ( CHeadManagerComponent ) components[0] );

	if( IBT_IsDLCBeard() )
	{
		destBeardStage = 3;
	}
	else
	{
		destBeardStage = IBT_GetGeraltBeardStage() + 1;
	}

	if( destBeardStage >= 1 && destBeardStage <= 4 )
	{
		thePlayer.ClearRememberedCustomHead();
		headManager.RemoveCustomHead();
		headManager.SetBeardStage( false, destBeardStage );
		headManager.BlockGrowing( false );
		return true;
	}
	else
	{
		return false;
	}
}







enum IBT_EHairType
{
	IBT_HT_Unknown		= 0,
	IBT_HT_ShortTied	= 1,
	IBT_HT_ShortUntied	= 2,
	IBT_HT_LongTied		= 3,
	IBT_HT_LongUntied	= 4
}

function IBT_HairNameToType( hairName : name ) : IBT_EHairType
{
	switch( hairName )
	{
		case 'Mohawk With Ponytail Hairstyle':
		case 'Shaved With Tail Hairstyle':
			return IBT_HT_ShortTied;
		case 'Short Loose Hairstyle':
		case 'Nilfgaardian Hairstyle':
			return IBT_HT_ShortUntied;
		case 'Half With Tail Hairstyle':
			return IBT_HT_LongTied;
		case 'Long Loose Hairstyle':
			return IBT_HT_LongUntied;
		default:
			return IBT_HT_Unknown;
	}
}

function IBT_HairStyleEnumToName( hairStyle: IBT_EHairStyle ) : name
{
	switch( hairStyle )
	{
		case IBT_EHairStyleShavedWithPonytail:
			return 'Shaved With Tail Hairstyle';
		case IBT_EHairStyleMohawkWithPonytail:
			return 'Mohawk With Ponytail Hairstyle';
		case IBT_EHairStyleShortLoose:
			return 'Short Loose Hairstyle';
		case IBT_EHairStyleElvenRebel:
			return 'Nilfgaardian Hairstyle';
		default:
			return '';
	}
}

function IBT_MenuShortHairName( tied: bool ) : name
{
	var settings : IBT_Settings;
	var style: IBT_EHairStyle;

	settings = GetIBT_Settings();
	style = tied ? settings.Main.HairShortTied : settings.Main.HairShortUntied;
	
	return IBT_HairStyleEnumToName(style);
}

function IBT_HairTypeToName( hairType : IBT_EHairType ) : name
{
	switch( hairType )
	{
		case IBT_HT_ShortTied:
			return IBT_MenuShortHairName(true);
		case IBT_HT_ShortUntied:
			return IBT_MenuShortHairName(false);
		case IBT_HT_LongTied:
			return 'Half With Tail Hairstyle';
		case IBT_HT_LongUntied:
			return 'Long Loose Hairstyle';
		default:
			return '';
	}
}

function IBT_GetGeraltHairType() : IBT_EHairType
{
	var inv 		: CInventoryComponent;
	var ids			: array<SItemUniqueId>;
	var i			: int;
	var size		: int;
	var hairType	: IBT_EHairType;
	var hairName	: name;

	inv = GetWitcherPlayer().GetInventory();
	ids = inv.GetItemsByCategory( 'hair' );
	size = ids.Size();
	hairType = IBT_HT_Unknown;

	if( size > 0 )
	{
		for(i = 0; i < size; i += 1)
		{
			if( inv.IsItemMounted( ids[i] ) )
			{
				hairName = inv.GetItemName( ids[i] );
				hairType = IBT_HairNameToType( hairName );
				break;
			}
		}
	}

	return hairType;
}

function IBT_EquipHair( hairName : name )
{
	var inv 		: CInventoryComponent;
	var ids			: array<SItemUniqueId>;
	var i			: int;
	var size		: int;

	inv = GetWitcherPlayer().GetInventory();
	ids = inv.GetItemsByCategory( 'hair' );
	size = ids.Size();

	// first clean up all hair items that are in inventory...
	if( size > 0 )
	{
		for( i = 0; i < size; i+=1 )
		{
			inv.RemoveItem( ids[i], 1 );
		}
	}

	// ... and only then add new hair item and mount it onto player model
	ids = inv.AddAnItem( hairName );
	inv.MountItem(ids[0]);
}

function IBT_CutGeraltHair() : bool
{
	var hairType	: IBT_EHairType;
	var hairName	: name;

	hairType = IBT_GetGeraltHairType();
	if( hairType == IBT_HT_LongTied || hairType == IBT_HT_LongUntied )
	{
		hairName = IBT_HairTypeToName( hairType - 2 );
		IBT_EquipHair( hairName );
		return true;
	}
	else
	{
		return false;
	}
}

function IBT_GrowGeraltHair() : bool
{
	var hairType	: IBT_EHairType;
	var hairName	: name;

	hairType = IBT_GetGeraltHairType();
	if( hairType == IBT_HT_ShortTied || hairType == IBT_HT_ShortUntied )
	{
		hairName = IBT_HairTypeToName( hairType + 2 );
		IBT_EquipHair( hairName );
		return true;
	}
	else
	{
		return false;
	}
}

function IBT_TieGeraltHair()
{
	var hairType	: IBT_EHairType;
	var hairName	: name;

	hairType = IBT_GetGeraltHairType();
	if( hairType == IBT_HT_ShortUntied || hairType == IBT_HT_LongUntied )
	{
		hairName = IBT_HairTypeToName( hairType - 1 );
		IBT_EquipHair( hairName );
	}
}

function IBT_UntieGeraltHair()
{
	var hairType	: IBT_EHairType;
	var hairName	: name;

	hairType = IBT_GetGeraltHairType();
	if( hairType == IBT_HT_ShortTied || hairType == IBT_HT_LongTied )
	{
		hairName = IBT_HairTypeToName( hairType + 1 );
		IBT_EquipHair( hairName );
	}
}






enum IBT_EScissorsMode
{
	IBT_SM_Beard	= 0,
	IBT_SM_Hair		= 1
}

function IBT_UseScissors( mode: IBT_EScissorsMode )
{
	var success: bool;

	if (thePlayer.IsInCombat())
	{
		theGame.GetGuiManager().ShowNotification( GetLocStringByKeyExt("menu_cannot_perform_action_combat") );
		success = false;
	}
	else
	{
		if( mode == IBT_SM_Beard )
		{
			success = IBT_TrimGeraltBeard();
			if( success )
				theGame.GetGuiManager().ShowNotification( GetLocStringByKeyExt("ibt_notif_used_scissors_beard_success") );
			else
				theGame.GetGuiManager().ShowNotification( GetLocStringByKeyExt("ibt_notif_used_scissors_beard_failure") );
		}
		else
		{
			success = IBT_CutGeraltHair();
			if( success )
				theGame.GetGuiManager().ShowNotification( GetLocStringByKeyExt("ibt_notif_used_scissors_hair_success") );
			else
				theGame.GetGuiManager().ShowNotification( GetLocStringByKeyExt("ibt_notif_used_scissors_hair_failure") );
		}
	}

	if( success )
		theSound.SoundEvent("gui_inventory_other_attach");
	else
		theSound.SoundEvent("gui_global_denied");
}

function IBT_GetScissorsMode( item: SItemUniqueId, inv: CInventoryComponent ) : IBT_EScissorsMode
{
	return (IBT_EScissorsMode)inv.GetItemModifierInt( item, 'ibt_scissors_mode', (int)IBT_SM_Beard );
}

function IBT_ChangeScissorsMode( item: SItemUniqueId, inv: CInventoryComponent )
{
	var mode	: IBT_EScissorsMode;

	mode = IBT_GetScissorsMode(item, inv);

	if( mode == IBT_SM_Beard )
	{
		inv.SetItemModifierInt( item, 'ibt_scissors_mode', (int)IBT_SM_Hair );
	}
	else
	{
		inv.SetItemModifierInt( item, 'ibt_scissors_mode', (int)IBT_SM_Beard );
	}

	theSound.SoundEvent("gui_inventory_other_back");
}

function IBT_GetScissorsTooltipModeDescription( item: SItemUniqueId, inv: CInventoryComponent ) : string
{
	var mode		: IBT_EScissorsMode;
	var modeDesc	: string;

	mode = IBT_GetScissorsMode( item, inv );

	modeDesc = "<font color=\"#C6A534\">" + GetLocStringByKeyExt("item_desc_ibt_scissors_mode_preamble") + ":</font> ";

	modeDesc += "<font color=\"#00FF00\">[";
	if( mode == IBT_SM_Beard )
	{
		modeDesc += GetLocStringByKeyExt("item_desc_ibt_scissors_mode_beard");
	}
	else
	{
		modeDesc += GetLocStringByKeyExt("item_desc_ibt_scissors_mode_hair");
	}
	modeDesc += "]</font>";

	return modeDesc;
}






function IBT_ConsumeTonicBeard( item: SItemUniqueId, inv: CInventoryComponent ) : bool
{
	var success	: bool;
	var menu	: CR4InventoryMenu;

	if (thePlayer.IsInCombat())
	{
		theGame.GetGuiManager().ShowNotification( GetLocStringByKeyExt("menu_cannot_perform_action_combat") );
		success = false;
	}
	else
	{
		success = IBT_GrowGeraltBeard();
		if( success )
			theGame.GetGuiManager().ShowNotification( GetLocStringByKeyExt("ibt_notif_drank_tonic_beard_success") );
		else
			theGame.GetGuiManager().ShowNotification( GetLocStringByKeyExt("ibt_notif_drank_tonic_beard_failure") );
	}

	if( success )
	{
		theSound.SoundEvent("gui_inventory_drink");

		menu = (CR4InventoryMenu) ((CR4MenuBase)theGame.GetGuiManager().GetRootMenu()).GetLastChild();
		// update invenotry menu peperdoll if we're currently in the inventory menu
		if( menu )
		{
			menu.UpdateAllItemData();
		}

		success = inv.RemoveItem( item, 1 );
	}
	else
		theSound.SoundEvent("gui_global_denied");

	return success;
}

function IBT_ConsumeTonicHair( item: SItemUniqueId, inv: CInventoryComponent ) : bool
{
	var success	: bool;
	var menu	: CR4InventoryMenu;

	if (thePlayer.IsInCombat())
	{
		theGame.GetGuiManager().ShowNotification( GetLocStringByKeyExt("menu_cannot_perform_action_combat") );
		success = false;
	}
	else
	{
		success = IBT_GrowGeraltHair();
		if( success )
			theGame.GetGuiManager().ShowNotification( GetLocStringByKeyExt("ibt_notif_drank_tonic_hair_success") );
		else
			theGame.GetGuiManager().ShowNotification( GetLocStringByKeyExt("ibt_notif_drank_tonic_hair_failure") );
	}

	if( success )
	{
		theSound.SoundEvent("gui_inventory_drink"); 

		menu = (CR4InventoryMenu) ((CR4MenuBase)theGame.GetGuiManager().GetRootMenu()).GetLastChild();
		// update invenotry menu peperdoll if we're currently in the inventory menu
		if( menu )
		{
			menu.UpdateAllItemData();
		}

		success = inv.RemoveItem( item, 1 );
	}
	else
		theSound.SoundEvent("gui_global_denied");

	return success;
}