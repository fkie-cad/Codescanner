# -*- coding: utf-8 -*-

# returns Ascii und Unicode Strings (getrennt)
def extract_strings(self):
    pass


# Nachschlagewerk fuer die Kuerzel.
DecisionDict = {}
DecisionDict["(U)"] = "Unknown data"
DecisionDict["(C)"] = "Corrupt, do not use"
DecisionDict["(P)"] = "Packed"
DecisionDict["(N)"] = "Normal"
DecisionDict["(X)"] = "No evaluation possible"
DecisionDict["(D)"] = "Data, for sure"


# Gibt Decision als Kuerzel aus.
def make_decision(sizes, header):
    # ==================================
    # Statements UNDER CONSTRUCTION ! ==
    # ==================================
    
    # This function belongs to Viviane and should not be edited.

    decision = "(X)"
    
    if sizes is None: raise RuntimeError('RuntimeError raised in make_decision: parameter sizes was None.')
    if not sizes.get("FileSize"): raise RuntimeError('RuntimeError raised in make_decision: no FileSize in parameter sizes specified.')
    # it is ok if there is no header.
    # it is also ok if there's no code found.

    header_is_present = header is not None

    zerosInPercent = 100.0 * (float(sizes.get("Zero")) / sizes.get("FileSize"))
    isSmall = sizes.get("FileSize") < 50000  # 50 KB
    isTiny = sizes.get("FileSize") < 20000  # 20 KB

    # 1%, Code gerade noch existent und bemerkbar.
    Code_exists = float(sizes.get("Code")) > (0.01 * sizes.get("FileSize"))

    # Ab 5% Code kann es bereits ein normales Binary sein, wenn es extrem klein ist.
    Code_minimum = float(sizes.get("Code")) > (0.05 * sizes.get("FileSize"))

    # Ab 20% ist vergleichsweise normal.
    Code_sufficient = float(sizes.get("Code")) > (0.2 * sizes.get("FileSize"))

    # Es gibt einen bemerkenswert grossen EBP.
    big_EBP_exists = float(sizes.get("HighEntropy")) > (0.4 * sizes.get("FileSize"))

    # Mehr als 25% Null-Bloecke.
    # Anmerkung: Null-Bloecke koennen auch bei normalen Binaries teilweise sehr gross werden.
    tooManyZeros = (zerosInPercent > 25.0)
    # Wird derzeit nicht verwendet, ist aber vielleicht sinnvoll.

    code_antithesis = (sizes.get("HighEntropy") * 1.0) + (sizes.get("Data") * 0.3)
    if (code_antithesis > sizes.get("FileSize")):
        code_antithesis = sizes.get("FileSize")

    # Default: Unknown.
    decision = "(U)"

    # Korruptes File, weil praktisch 100% Code.
    if (sizes.get("Code") > (0.9 * sizes.get("FileSize"))):
        decision = "(C)"

    # Das Veto ist eine binaere ja/nein Entscheidung, berechnet aus den in Zahlen ausgedrueckten Argumenten, die fuer ein gepacktes Binary sprechen.
    Veto_I = (code_antithesis > (0.2 * sizes.get("FileSize")))
    Veto_II = (code_antithesis > (0.3 * sizes.get("FileSize")))
    Veto_III = (code_antithesis > (0.4 * sizes.get("FileSize")))

    # Zusammensetzung des Binaries skaliert auch mit der Filesize.
    if isTiny and Veto_III and (Code_exists or header_is_present) and not Code_sufficient:
        decision = "(P)"
    elif isSmall and Veto_II and (Code_exists or header_is_present) and not Code_sufficient:
        decision = "(P)"
    elif Veto_I and (Code_exists or header_is_present) and not Code_sufficient:
        decision = "(P)"
    # Entscheidung wird bei .Net Binaries prinzipiell falsch sein.
    # Das wird sich aendern, sobald ich .Net als Language File hinzugefuegt habe.

    # Die packed-Entscheidung kann zurueckgenommen werden, wenn der Code-Anteil mindestens so gross ist wie der grosse EBP.
    # Das ist nur gueltig, wenn es einen solchen grossen EBP gibt.
    if (decision == "(P)"):
        if (sizes.get("Code") > sizes.get("HighEntropy")) and (big_EBP_exists):
            decision = "(N)"

    # Total normales Standard-Executable wie aus dem Lehrbuch.
    elif Code_sufficient:
        decision = "(N)"

    # Sehr winzige Executables
    elif Code_minimum and isTiny:
        decision = "(N)"

    # Groessere Executables, die aber ziemlich viel Daten haben.
    elif Code_minimum and ((sizes.get("HighEntropy")) < (0.1 * sizes.get("FileSize"))):
        decision = "(N)"


    # Datenfile
    elif not (Code_exists or header_is_present):
        decision = "(D)"

    # PackedCertainty koennte als return value Gebrauch finden.
    if (decision == "(P)"):
        PackedCertainty = code_antithesis / (sizes.get("FileSize") * 0.5)
    else:
        PackedCertainty = 0

    return decision
