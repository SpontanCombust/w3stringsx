exec function ibt_items()
{
    thePlayer.inv.AddAnItem('ibt_scissors', 1);
    thePlayer.inv.AddAnItem('ibt_hairtie', 1);
    thePlayer.inv.AddAnItem('ibt_tonic_beard', 4);
    thePlayer.inv.AddAnItem('ibt_tonic_hair', 2);
}

exec function ibt_addscissors()
{
    thePlayer.inv.AddAnItem('ibt_scissors', 1);
}

exec function ibt_addhairtie()
{
    thePlayer.inv.AddAnItem('ibt_hairtie', 1);
}

exec function ibt_addtonics()
{
    thePlayer.inv.AddAnItem('ibt_tonic_beard', 4);
    thePlayer.inv.AddAnItem('ibt_tonic_hair', 2);
}

exec function ibt_growhair()
{
    IBT_GrowGeraltHair();
}

exec function ibt_cuthair()
{
    IBT_CutGeraltHair();
}

exec function ibt_tiehair()
{
    IBT_TieGeraltHair();
}

exec function ibt_untiehair()
{
    IBT_UntieGeraltHair();
}

exec function ibt_growbeard()
{
    IBT_GrowGeraltBeard();
}

exec function ibt_trimbeard()
{
    IBT_TrimGeraltBeard();
}