// Code generated using Mod Settings Framework v1.0.0 by SpontanCombust & Aeltoth

class IBT_Settings extends ISettingsMaster
{
	default modVersion = "3.0.0";

	public var Main : IBT_Settings_Main;

	protected /* override */ function Parser_Init() : void
	{
		Main = new IBT_Settings_Main in this;
		Main.Init(this);
		m_groups.PushBack(Main);
	}

	protected /* override */ function Parser_ShouldResetSettingsToDefaultOnInit(config : CInGameConfigWrapper) : bool
	{
		return ReadSettingValue(config, 'ImmersiveBeardTrimming','HairShortTied') == "-1";
	}
}

class IBT_Settings_Main extends ISettingsGroup
{
	public var HairShortTied : IBT_EHairStyle;
	public var HairShortUntied : IBT_EHairStyle;

	default id = 'ImmersiveBeardTrimming';
	default defaultPresetIndex = 0;

	protected /* override */ function Parser_ValidateSettings() : void
	{
		HairShortTied = (IBT_EHairStyle)EnumValueMappingValidateUnified('HairShortTied', (int)HairShortTied);
		HairShortUntied = (IBT_EHairStyle)EnumValueMappingValidateUnified('HairShortUntied', (int)HairShortUntied);
	}

	protected /* override */ function Parser_ReadSettings(config: CInGameConfigWrapper) : void
	{
		HairShortTied = (IBT_EHairStyle)ReadUnifiedEnumSettingValue(config, 'HairShortTied');
		HairShortUntied = (IBT_EHairStyle)ReadUnifiedEnumSettingValue(config, 'HairShortUntied');
	}

	protected /* override */ function Parser_WriteSettings(config: CInGameConfigWrapper) : void
	{
		WriteUnifiedEnumSettingValue(config, 'HairShortTied', (int)HairShortTied);
		WriteUnifiedEnumSettingValue(config, 'HairShortUntied', (int)HairShortUntied);
	}

	protected /* override */ function Parser_EnumValueMappingValidateUnified(vId: name, val: int) : int
	{
		switch(vId)
		{
		case 'HairShortTied':
			switch(val)
			{
			case 0: 
			case 1: 
				return val;
			default:
				return 0;
			}
		case 'HairShortUntied':
			switch(val)
			{
			case 2: 
			case 3: 
				return val;
			default:
				return 2;
			}
		}

		return 0;
	}

	protected /* override */ function Parser_EnumValueMappingConfigToUnified(vId: name, val: int) : int
	{
		switch(vId)
		{
		case 'HairShortTied':
			switch(val)
			{
			case 0: return 0;
			case 1: return 1;
			}
		case 'HairShortUntied':
			switch(val)
			{
			case 0: return 2;
			case 1: return 3;
			}
		}

		return -1;
	}

	protected /* override */ function Parser_EnumValueMappingUnifiedToConfig(vId: name, val: int) : int
	{
		switch(vId)
		{
		case 'HairShortTied':
			switch(val)
			{
			case 0: return 0;
			case 1: return 1;
			}
		case 'HairShortUntied':
			switch(val)
			{
			case 2: return 0;
			case 3: return 1;
			}
		}

		return -1;
	}
}

enum IBT_EHairStyle
{
	IBT_EHairStyleShavedWithPonytail = 0,
	IBT_EHairStyleMohawkWithPonytail = 1,
	IBT_EHairStyleShortLoose = 2,
	IBT_EHairStyleElvenRebel = 3,
}


function GetIBT_Settings() : IBT_Settings
{
	var settings: IBT_Settings;

	settings = (IBT_Settings)GetSettingsMasterRegistry().GetSettings('IBT_Settings');
	if(!settings)
	{
		settings = new IBT_Settings in theGame;
		GetSettingsMasterRegistry().AddSettings(settings, 'IBT_Settings');
	}

	return settings;
}
