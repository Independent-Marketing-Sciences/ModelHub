
# temp <- qhpvt(varContsDb, "OBS", "Categorisation.2", "sum(value)")
#
# pt <- PivotTable$new()
# pt$addData(varContsDb)
# pt$addColumnDataGroups("Categorisation.2")
# pt$addRowDataGroups("OBS")
# pt$defineCalculation(calculationName="value", summariseExpression="sum()")
# pt$renderPivot()