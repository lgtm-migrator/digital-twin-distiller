showconsole()
clearconsole()
remove("electrostatic_data.csv")
newdocument(1)
file_out = openfile("electrostatic_data.csv", "w")
ei_probdef("centimeters", "planar", 1e-08, 1, 30)
ei_addnode(-5.0, 5.0)
ei_addnode(-5.0, 0)
ei_addnode(0, 0)
ei_addnode(0, -5.0)
ei_addnode(5.0, -5.0)
ei_addnode(5.0, 5.0)
ei_addsegment(-5.0, 5.0, -5.0, 0)
ei_addsegment(-5.0, 0, 0, 0)
ei_addsegment(0, 0, 0, -5.0)
ei_addsegment(0, -5.0, 5.0, -5.0)
ei_addsegment(5.0, -5.0, 5.0, 5.0)
ei_addsegment(5.0, 5.0, -5.0, 5.0)
ei_addmaterial("Teflon", 2.1, 2.1, 0)
ei_addblocklabel(2.5, 2.5)
ei_selectlabel(2.5, 2.5)
ei_setblockprop("Teflon", 1, 1, 0)
ei_addpointprop("Ug", 10, 0)
ei_addpointprop("U0", 0, 0)
ei_selectnode(0, 0)
ei_setnodeprop("Ug", 0, "<None>")
ei_clearselected()
ei_selectnode(5.0, 5.0)
ei_setnodeprop("U0", 0, "<None>")
ei_clearselected()
ei_zoomnatural()
ei_zoomout()
hideconsole()
ei_saveas("electrostatic_test.fee")
ei_analyze(1)
ei_loadsolution()
eo_selectblock(2.5, 2.5)
E = eo_blockintegral(0)
write(file_out, 'E', ', ', E, "\n")

closefile(file_out)
quit()